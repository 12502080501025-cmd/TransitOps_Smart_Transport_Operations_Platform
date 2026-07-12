from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime

from transit_ops.models import MaintenanceLog, MaintenanceStatusEnum, Vehicle, VehicleStatusEnum
from transit_ops.auth import get_current_user, require_role

router = APIRouter()

class MaintenanceCreate(BaseModel):
    vehicle_id: int
    maintenance_type: str
    description: str
    cost: float = 0.0

class MaintenanceClose(BaseModel):
    cost: float = 0.0

class MaintenanceResponse(BaseModel):
    id: int
    vehicle_id: int
    maintenance_type: str
    description: str
    status: str
    cost: float
    created_at: str
    closed_at: str

    class Config:
        from_attributes = True

@router.post("/create", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED)
def create_maintenance(
    request: MaintenanceCreate,
    current_user: dict = Depends(require_role("fleet_manager")),
    db: Session = Depends()
):
    """Create maintenance log and auto-set vehicle to IN_SHOP."""
    vehicle = db.query(Vehicle).filter(Vehicle.id == request.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    maintenance = MaintenanceLog(
        vehicle_id=request.vehicle_id,
        maintenance_type=request.maintenance_type,
        description=request.description,
        cost=request.cost,
        status=MaintenanceStatusEnum.OPEN
    )
    
    vehicle.status = VehicleStatusEnum.IN_SHOP
    
    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)
    
    return MaintenanceResponse.from_orm(maintenance)

@router.post("/{maintenance_id}/close", response_model=MaintenanceResponse)
def close_maintenance(
    maintenance_id: int,
    request: MaintenanceClose,
    current_user: dict = Depends(require_role("fleet_manager")),
    db: Session = Depends()
):
    """Close maintenance and restore vehicle to AVAILABLE."""
    maintenance = db.query(MaintenanceLog).filter(MaintenanceLog.id == maintenance_id).first()
    if not maintenance:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    
    if maintenance.status == MaintenanceStatusEnum.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maintenance record is already closed"
        )
    
    vehicle = db.query(Vehicle).filter(Vehicle.id == maintenance.vehicle_id).first()
    
    maintenance.status = MaintenanceStatusEnum.CLOSED
    maintenance.closed_at = datetime.utcnow()
    maintenance.cost = request.cost
    
    if vehicle.status != VehicleStatusEnum.RETIRED:
        vehicle.status = VehicleStatusEnum.AVAILABLE
    
    db.commit()
    db.refresh(maintenance)
    
    return MaintenanceResponse.from_orm(maintenance)

@router.get("/", response_model=List[MaintenanceResponse])
def list_maintenance(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends()
):
    """List all maintenance records."""
    records = db.query(MaintenanceLog).order_by(MaintenanceLog.created_at.desc()).all()
    return [MaintenanceResponse.from_orm(r) for r in records]

@router.get("/{maintenance_id}", response_model=MaintenanceResponse)
def get_maintenance(
    maintenance_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends()
):
    """Get specific maintenance record."""
    maintenance = db.query(MaintenanceLog).filter(MaintenanceLog.id == maintenance_id).first()
    if not maintenance:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    return MaintenanceResponse.from_orm(maintenance)

@router.get("/vehicle/{vehicle_id}", response_model=List[MaintenanceResponse])
def get_vehicle_maintenance(
    vehicle_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends()
):
    """Get maintenance history for a vehicle."""
    records = db.query(MaintenanceLog).filter(
        MaintenanceLog.vehicle_id == vehicle_id
    ).order_by(MaintenanceLog.created_at.desc()).all()
    return [MaintenanceResponse.from_orm(r) for r in records]