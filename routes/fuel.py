from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime

from transit_ops.models import FuelLog, Vehicle
from transit_ops.auth import get_current_user, require_role

router = APIRouter()

class FuelLogCreate(BaseModel):
    vehicle_id: int
    liters: float
    cost: float
    notes: str = ""

class FuelLogResponse(BaseModel):
    id: int
    vehicle_id: int
    liters: float
    cost: float
    date: str
    notes: str

    class Config:
        from_attributes = True

@router.post("/log", response_model=FuelLogResponse, status_code=status.HTTP_201_CREATED)
def log_fuel(
    request: FuelLogCreate,
    current_user: dict = Depends(require_role("fleet_manager", "financial_analyst")),
    db: Session = Depends()
):
    """Log a fuel refill."""
    vehicle = db.query(Vehicle).filter(Vehicle.id == request.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    fuel_log = FuelLog(
        vehicle_id=request.vehicle_id,
        liters=request.liters,
        cost=request.cost,
        notes=request.notes,
        date=datetime.utcnow()
    )
    
    db.add(fuel_log)
    db.commit()
    db.refresh(fuel_log)
    
    return FuelLogResponse.from_orm(fuel_log)

@router.get("/", response_model=List[FuelLogResponse])
def list_fuel_logs(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends()
):
    """List all fuel logs."""
    logs = db.query(FuelLog).order_by(FuelLog.date.desc()).all()
    return [FuelLogResponse.from_orm(log) for log in logs]

@router.get("/vehicle/{vehicle_id}", response_model=List[FuelLogResponse])
def get_vehicle_fuel_logs(
    vehicle_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends()
):
    """Get fuel logs for a vehicle."""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    logs = db.query(FuelLog).filter(
        FuelLog.vehicle_id == vehicle_id
    ).order_by(FuelLog.date.desc()).all()
    
    return [FuelLogResponse.from_orm(log) for log in logs]