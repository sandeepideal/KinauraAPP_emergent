"""
Patient-related routes
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..deps import get_db, get_current_user
import uuid

router = APIRouter(prefix="/patient", tags=["patients"])

# Models
class PatientProfile(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    emergency_contact: Optional[str] = None
    medical_conditions: Optional[List[str]] = None
    medications: Optional[List[str]] = None
    allergies: Optional[List[str]] = None

@router.get("/profile")
async def get_patient_profile(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get current patient's profile"""
    user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0, "password_hash": 0})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    return user

@router.put("/profile")
async def update_patient_profile(
    profile_data: PatientProfile,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update patient profile"""
    update_data = profile_data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Return updated profile
    updated_user = await db.users.find_one(
        {"id": current_user["id"]}, 
        {"_id": 0, "password_hash": 0}
    )
    
    return updated_user

@router.get("/appointments")
async def get_patient_appointments(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    status_filter: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """Get patient's appointments"""
    query = {"user_id": current_user["id"]}
    
    if status_filter:
        query["status"] = status_filter
    
    appointments = await db.appointments.find(query, {"_id": 0}).limit(limit).to_list(None)
    
    # Enrich with service details
    for appointment in appointments:
        if appointment.get("service_id"):
            service = await db.services.find_one(
                {"id": appointment["service_id"]},
                {"_id": 0, "name": 1, "duration": 1, "price": 1}
            )
            appointment["service"] = service
    
    return {"appointments": appointments}

@router.post("/appointments")
async def create_patient_appointment(
    appointment_data: dict,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Create new appointment for patient"""
    appointment_id = str(uuid.uuid4())
    
    appointment_doc = {
        "id": appointment_id,
        "user_id": current_user["id"],
        "service_id": appointment_data["service_id"],
        "appointment_date": datetime.fromisoformat(appointment_data["appointment_date"].replace("Z", "+00:00")),
        "status": "scheduled",
        "notes": appointment_data.get("notes"),
        "created_at": datetime.utcnow()
    }
    
    await db.appointments.insert_one(appointment_doc)
    
    # Remove _id from response
    appointment_doc.pop("_id", None)
    
    return appointment_doc

@router.delete("/appointments/{appointment_id}")
async def cancel_patient_appointment(
    appointment_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Cancel patient appointment"""
    # Verify appointment belongs to user
    appointment = await db.appointments.find_one({
        "id": appointment_id,
        "user_id": current_user["id"]
    })
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Update status to cancelled
    result = await db.appointments.update_one(
        {"id": appointment_id},
        {
            "$set": {
                "status": "cancelled",
                "cancelled_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Appointment cancelled successfully"}

@router.get("/files")
async def get_patient_files(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    file_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """Get patient's files (visible to patient only)"""
    query = {
        "patient_id": current_user["id"],
        "visible_to_patient": True
    }
    
    if file_type:
        query["file_type"] = file_type
    
    files = await db.patient_files.find(query, {"_id": 0}).limit(limit).to_list(None)
    
    return {"files": files}

@router.get("/longevity-score")
async def get_longevity_score(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get patient's longevity score"""
    score_data = await db.longevity_scores.find_one(
        {"patient_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not score_data:
        # Return default score if none exists
        return {
            "patient_id": current_user["id"],
            "score": 50,
            "factors": [],
            "last_updated": datetime.utcnow(),
            "trend": "stable"
        }
    
    return score_data