"""
Admin-only routes
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..deps import get_db, get_admin_user, requires_role
import uuid

router = APIRouter(prefix="/admin", tags=["admin"])

# Models
class ServiceCreate(BaseModel):
    name: str
    category: str
    description: str
    detailed_description: str
    duration: int = 60
    price: float
    benefits: List[str] = []
    is_active: bool = True

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    detailed_description: Optional[str] = None
    duration: Optional[int] = None
    price: Optional[float] = None
    benefits: Optional[List[str]] = None
    is_active: Optional[bool] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    membership_tier: Optional[str] = None
    is_active: Optional[bool] = None

@router.get("/dashboard")
async def get_admin_dashboard(
    admin_user: dict = Depends(get_admin_user),
    db = Depends(get_db)
):
    """Get admin dashboard metrics"""
    # Get key metrics
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"is_active": True})
    total_appointments = await db.appointments.count_documents({})
    pending_appointments = await db.appointments.count_documents({"status": "scheduled"})
    total_services = await db.services.count_documents({})
    active_services = await db.services.count_documents({"is_active": True})
    
    # Recent appointments
    recent_appointments = await db.appointments.find(
        {},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(None)
    
    return {
        "metrics": {
            "total_users": total_users,
            "active_users": active_users,
            "total_appointments": total_appointments,
            "pending_appointments": pending_appointments,
            "total_services": total_services,
            "active_services": active_services
        },
        "recent_appointments": recent_appointments
    }

@router.get("/users")
async def list_users(
    admin_user: dict = Depends(get_admin_user),
    db = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    role_filter: Optional[str] = Query(None),
    active_only: bool = Query(False)
):
    """List all users with pagination"""
    query = {}
    
    if role_filter:
        query["role"] = role_filter
    
    if active_only:
        query["is_active"] = True
    
    skip = (page - 1) * limit
    
    users = await db.users.find(
        query,
        {"_id": 0, "password_hash": 0}
    ).skip(skip).limit(limit).to_list(None)
    
    total_count = await db.users.count_documents(query)
    
    return {
        "users": users,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": (total_count + limit - 1) // limit
        }
    }

@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    admin_user: dict = Depends(get_admin_user),
    db = Depends(get_db)
):
    """Update user details (admin only)"""
    update_dict = update_data.dict(exclude_unset=True)
    update_dict["updated_at"] = datetime.utcnow()
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Return updated user
    updated_user = await db.users.find_one(
        {"id": user_id},
        {"_id": 0, "password_hash": 0}
    )
    
    return updated_user

@router.post("/services")
async def create_service(
    service_data: ServiceCreate,
    admin_user: dict = Depends(get_admin_user),
    db = Depends(get_db)
):
    """Create new service"""
    service_id = str(uuid.uuid4())
    
    service_doc = {
        "id": service_id,
        "created_at": datetime.utcnow(),
        **service_data.dict()
    }
    
    await db.services.insert_one(service_doc)
    
    # Remove _id from response
    service_doc.pop("_id", None)
    
    return service_doc

@router.put("/services/{service_id}")
async def update_service(
    service_id: str,
    update_data: ServiceUpdate,
    admin_user: dict = Depends(get_admin_user),
    db = Depends(get_db)
):
    """Update service"""
    update_dict = update_data.dict(exclude_unset=True)
    update_dict["updated_at"] = datetime.utcnow()
    
    result = await db.services.update_one(
        {"id": service_id},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Return updated service
    updated_service = await db.services.find_one(
        {"id": service_id},
        {"_id": 0}
    )
    
    return updated_service

@router.delete("/services/{service_id}")
async def delete_service(
    service_id: str,
    admin_user: dict = Depends(get_admin_user),
    db = Depends(get_db)
):
    """Delete service (soft delete by setting is_active=False)"""
    result = await db.services.update_one(
        {"id": service_id},
        {
            "$set": {
                "is_active": False,
                "deleted_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    return {"message": "Service deleted successfully"}

@router.get("/appointments")
async def list_all_appointments(
    admin_user: dict = Depends(get_admin_user),
    db = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None)
):
    """List all appointments (admin view)"""
    query = {}
    
    if status_filter:
        query["status"] = status_filter
    
    if date_from or date_to:
        date_query = {}
        if date_from:
            date_query["$gte"] = datetime.fromisoformat(date_from)
        if date_to:
            date_query["$lte"] = datetime.fromisoformat(date_to)
        query["appointment_date"] = date_query
    
    skip = (page - 1) * limit
    
    appointments = await db.appointments.find(query, {"_id": 0}) \
        .sort("appointment_date", -1) \
        .skip(skip) \
        .limit(limit) \
        .to_list(None)
    
    # Enrich with patient and service details
    for appointment in appointments:
        if appointment.get("user_id"):
            patient = await db.users.find_one(
                {"id": appointment["user_id"]},
                {"_id": 0, "full_name": 1, "email": 1, "phone": 1}
            )
            appointment["patient"] = patient
        
        if appointment.get("service_id"):
            service = await db.services.find_one(
                {"id": appointment["service_id"]},
                {"_id": 0, "name": 1, "duration": 1, "price": 1}
            )
            appointment["service"] = service
    
    total_count = await db.appointments.count_documents(query)
    
    return {
        "appointments": appointments,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": (total_count + limit - 1) // limit
        }
    }

@router.get("/inquiries")
async def list_patient_inquiries(
    admin_user: dict = Depends(get_admin_user),
    db = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    inquiry_type: Optional[str] = Query(None)
):
    """List patient inquiries from chatbot"""
    query = {}
    
    if status_filter:
        query["status"] = status_filter
    
    if inquiry_type:
        query["inquiry_type"] = inquiry_type
    
    skip = (page - 1) * limit
    
    inquiries = await db.patient_inquiries.find(query, {"_id": 0}) \
        .sort("timestamp", -1) \
        .skip(skip) \
        .limit(limit) \
        .to_list(None)
    
    # Enrich with patient details
    for inquiry in inquiries:
        if inquiry.get("patient_id"):
            patient = await db.users.find_one(
                {"id": inquiry["patient_id"]},
                {"_id": 0, "full_name": 1, "email": 1, "phone": 1}
            )
            inquiry["patient"] = patient
    
    total_count = await db.patient_inquiries.count_documents(query)
    
    return {
        "inquiries": inquiries,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": (total_count + limit - 1) // limit
        }
    }