"""
Appointment management routes
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta, date
from ..deps import get_db, get_current_user, get_admin_user
import uuid

router = APIRouter(prefix="/appointments", tags=["appointments"])

# Models
class AppointmentCreate(BaseModel):
    service_id: str
    appointment_date: datetime
    notes: Optional[str] = None

class AppointmentUpdate(BaseModel):
    appointment_date: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None

@router.get("/availability")
async def get_appointment_availability(
    service_id: str = Query(...),
    date_str: str = Query(..., alias="date"),
    db = Depends(get_db)
):
    """Get available appointment slots for a service on a specific date"""
    try:
        requested_date = datetime.fromisoformat(date_str).date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    # Get service details
    service = await db.services.find_one({"id": service_id}, {"_id": 0})
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Generate available slots (9 AM to 5 PM, hourly)
    available_slots = []
    start_time = datetime.combine(requested_date, datetime.min.time().replace(hour=9))
    end_time = datetime.combine(requested_date, datetime.min.time().replace(hour=17))
    
    current_slot = start_time
    while current_slot < end_time:
        # Check if slot is available (no existing appointment)
        existing = await db.appointments.find_one({
            "service_id": service_id,
            "appointment_date": current_slot,
            "status": {"$in": ["scheduled", "confirmed"]}
        })
        
        if not existing:
            available_slots.append({
                "datetime": current_slot,
                "display_time": current_slot.strftime("%I:%M %p")
            })
        
        current_slot += timedelta(hours=1)
    
    return {
        "service_id": service_id,
        "date": date_str,
        "available_slots": available_slots
    }

@router.get("/")
async def list_appointments(
    db = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """List appointments with pagination and filtering"""
    query = {}
    
    # For non-admin users, only show their appointments
    if current_user.get("role") != "admin":
        query["user_id"] = current_user["id"]
    
    # Date filtering
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = datetime.fromisoformat(start_date)
        if end_date:
            date_query["$lte"] = datetime.fromisoformat(end_date)
        query["appointment_date"] = date_query
    
    # Status filtering
    if status_filter:
        query["status"] = status_filter
    
    # Pagination
    skip = (page - 1) * limit
    
    appointments = await db.appointments.find(query, {"_id": 0}) \
        .skip(skip) \
        .limit(limit) \
        .to_list(None)
    
    # Get total count for pagination
    total_count = await db.appointments.count_documents(query)
    
    # Enrich with service and user details
    for appointment in appointments:
        if appointment.get("service_id"):
            service = await db.services.find_one(
                {"id": appointment["service_id"]},
                {"_id": 0, "name": 1, "duration": 1, "price": 1}
            )
            appointment["service"] = service
        
        if appointment.get("user_id") and current_user.get("role") == "admin":
            user = await db.users.find_one(
                {"id": appointment["user_id"]},
                {"_id": 0, "full_name": 1, "email": 1, "phone": 1}
            )
            appointment["patient"] = user
    
    return {
        "appointments": appointments,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": (total_count + limit - 1) // limit
        }
    }

@router.get("/{appointment_id}")
async def get_appointment(
    appointment_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get specific appointment details"""
    query = {"id": appointment_id}
    
    # Non-admin users can only see their own appointments
    if current_user.get("role") != "admin":
        query["user_id"] = current_user["id"]
    
    appointment = await db.appointments.find_one(query, {"_id": 0})
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Enrich with service details
    if appointment.get("service_id"):
        service = await db.services.find_one(
            {"id": appointment["service_id"]},
            {"_id": 0}
        )
        appointment["service"] = service
    
    return appointment

@router.put("/{appointment_id}")
async def update_appointment(
    appointment_id: str,
    update_data: AppointmentUpdate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update appointment (patient can reschedule, admin can change status)"""
    query = {"id": appointment_id}
    
    # Non-admin users can only update their own appointments
    if current_user.get("role") != "admin":
        query["user_id"] = current_user["id"]
    
    appointment = await db.appointments.find_one(query)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Prepare update data
    update_dict = update_data.dict(exclude_unset=True)
    update_dict["updated_at"] = datetime.utcnow()
    
    # Only admin can change status
    if "status" in update_dict and current_user.get("role") != "admin":
        update_dict.pop("status")
    
    result = await db.appointments.update_one(
        {"id": appointment_id},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Return updated appointment
    updated_appointment = await db.appointments.find_one(
        {"id": appointment_id},
        {"_id": 0}
    )
    
    return updated_appointment