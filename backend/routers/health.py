"""
Health data integration routes
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..deps import get_db, get_current_user
from enum import Enum

router = APIRouter(prefix="/patient/health", tags=["health"])

# Models
class HealthProvider(str, Enum):
    HEALTHKIT = "HEALTHKIT"
    WHOOP = "WHOOP"

class ConnectProviderRequest(BaseModel):
    provider: HealthProvider
    permissions: List[str] = []
    metric_categories: List[str] = []

class ExportDataRequest(BaseModel):
    format: str = "json"  # json or csv
    date_from: datetime
    date_to: datetime

@router.get("/connections")
async def get_health_connections(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get user's health provider connections"""
    connections = await db.health_connections.find(
        {"patient_id": current_user["id"]},
        {"_id": 0}
    ).to_list(None)
    
    return {"connections": connections}

@router.post("/connect")
async def connect_health_provider(
    connect_request: ConnectProviderRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Connect a health data provider"""
    # Check if already connected
    existing = await db.health_connections.find_one({
        "patient_id": current_user["id"],
        "provider": connect_request.provider.value
    })
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{connect_request.provider.value} is already connected"
        )
    
    # Create connection record
    connection_doc = {
        "patient_id": current_user["id"],
        "provider": connect_request.provider.value,
        "permissions": connect_request.permissions,
        "metric_categories": connect_request.metric_categories,
        "status": "connected",
        "connected_at": datetime.utcnow(),
        "last_sync_at": None,
        "sync_status": "pending"
    }
    
    await db.health_connections.insert_one(connection_doc)
    
    # Remove _id from response
    connection_doc.pop("_id", None)
    
    return {
        "message": f"{connect_request.provider.value} connected successfully",
        "connection": connection_doc
    }

@router.delete("/connections/{provider}")
async def disconnect_health_provider(
    provider: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Disconnect a health data provider"""
    result = await db.health_connections.delete_one({
        "patient_id": current_user["id"],
        "provider": provider.upper()
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Also delete associated health data
    await db.health_data.delete_many({
        "patient_id": current_user["id"],
        "provider": provider.upper()
    })
    
    return {"message": f"{provider} disconnected successfully"}

@router.get("/dashboard")
async def get_health_dashboard(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    days: int = Query(30, ge=1, le=365)
):
    """Get health dashboard data"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Aggregate health metrics
    pipeline = [
        {
            "$match": {
                "patient_id": current_user["id"],
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": {
                    "metric": "$metric",
                    "provider": "$provider"
                },
                "latest_value": {"$last": "$value"},
                "latest_timestamp": {"$last": "$timestamp"},
                "samples": {"$push": {"value": "$value", "timestamp": "$timestamp"}},
                "count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "metric": "$_id.metric",
                "provider": "$_id.provider",
                "latest_value": 1,
                "latest_timestamp": 1,
                "sample_count": {"$size": "$samples"},
                "samples": {"$slice": ["$samples", -10]}  # Last 10 samples
            }
        }
    ]
    
    dashboard_data = await db.health_data.aggregate(pipeline).to_list(None)
    
    return {"dashboard": dashboard_data}

@router.get("/metrics/{metric}")
async def get_metric_data(
    metric: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
    provider: Optional[str] = Query(None)
):
    """Get specific metric data"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    query = {
        "patient_id": current_user["id"],
        "metric": metric,
        "timestamp": {"$gte": start_date, "$lte": end_date}
    }
    
    if provider:
        query["provider"] = provider.upper()
    
    samples = await db.health_data.find(
        query,
        {"_id": 0}
    ).sort("timestamp", 1).to_list(None)
    
    return {
        "metric": metric,
        "samples": samples,
        "count": len(samples)
    }

@router.post("/export")
async def export_health_data(
    export_request: ExportDataRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Export health data"""
    query = {
        "patient_id": current_user["id"],
        "timestamp": {
            "$gte": export_request.date_from,
            "$lte": export_request.date_to
        }
    }
    
    health_data = await db.health_data.find(query, {"_id": 0}).to_list(None)
    
    # Create export record
    export_id = f"export_{current_user['id']}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    export_record = {
        "export_id": export_id,
        "patient_id": current_user["id"],
        "format": export_request.format,
        "date_from": export_request.date_from,
        "date_to": export_request.date_to,
        "record_count": len(health_data),
        "exported_at": datetime.utcnow(),
        "filename": f"health_data_{export_id}.{export_request.format}"
    }
    
    await db.health_exports.insert_one(export_record)
    
    # Remove _id from response
    export_record.pop("_id", None)
    
    return {
        "export_id": export_id,
        "record_count": len(health_data),
        "filename": export_record["filename"],
        "message": "Export created successfully"
    }