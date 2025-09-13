"""
Public services routes
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query, Request, Response
from typing import List, Optional
from datetime import datetime
from ..deps import get_db
import hashlib
import json

router = APIRouter(prefix="/services", tags=["services"])

@router.get("/")
async def list_services(
    request: Request,
    response: Response,
    db = Depends(get_db),
    category: Optional[str] = Query(None),
    active_only: bool = Query(True),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """List services with pagination and ETag caching"""
    query = {}
    
    if active_only:
        query["is_active"] = True
    
    if category:
        query["category"] = category
    
    skip = (page - 1) * limit
    
    services = await db.services.find(query, {"_id": 0}) \
        .skip(skip) \
        .limit(limit) \
        .to_list(None)
    
    total_count = await db.services.count_documents(query)
    
    # Generate ETag for caching
    content = json.dumps({
        "services": services,
        "total": total_count,
        "page": page
    }, default=str, sort_keys=True)
    
    etag = hashlib.sha1(content.encode()).hexdigest()
    
    # Check If-None-Match header
    if_none_match = request.headers.get("if-none-match")
    if if_none_match == etag:
        return Response(status_code=304)
    
    # Set ETag header
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutes
    
    return {
        "services": services,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": (total_count + limit - 1) // limit
        }
    }

@router.get("/{service_id}")
async def get_service(
    service_id: str,
    request: Request,
    response: Response,
    db = Depends(get_db)
):
    """Get specific service details with caching"""
    service = await db.services.find_one({"id": service_id}, {"_id": 0})
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    if not service.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not available"
        )
    
    # Generate ETag
    content = json.dumps(service, default=str, sort_keys=True)
    etag = hashlib.sha1(content.encode()).hexdigest()
    
    # Check If-None-Match header
    if_none_match = request.headers.get("if-none-match")
    if if_none_match == etag:
        return Response(status_code=304)
    
    # Set cache headers
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "public, max-age=600"  # 10 minutes
    
    return service

@router.get("/category/{category}")
async def get_services_by_category(
    category: str,
    db = Depends(get_db),
    active_only: bool = Query(True)
):
    """Get services by category"""
    query = {"category": category}
    
    if active_only:
        query["is_active"] = True
    
    services = await db.services.find(query, {"_id": 0}).to_list(None)
    
    return {
        "category": category,
        "services": services,
        "count": len(services)
    }