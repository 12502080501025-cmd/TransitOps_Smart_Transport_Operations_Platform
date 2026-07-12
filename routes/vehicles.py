from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from transit_ops.models import Vehicle, VehicleStatusEnum
from transit_ops.auth import get_current_user, require_role

router = APIRouter()

class VehicleCreate(BaseModel):
    registration_number: str
    vehicle_name: str
    vehicle_type: str
    max_load_capacity: float
    acquisition_cost: float

class VehicleUpdate(BaseModel):
    vehicle_name: str = None
    vehicle_type: str = None
    max_load_capacity: float = None
    status: str = None

class VehicleResponse(BaseModel):
    id: int
    registration_number: str
    vehicle_name: str
    vehicle_type: str
    max_load_capacity: float
    odometer: float
    acquisition_cost: float
    status: str

    class Config:
        from_attributes = True

@router.post("/register", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def register_vehicle(
    request: VehicleCreate,
    current_user: dict = Depends(require_role("fleet_manager")),
    db: Session = Depends()
):
    """Register a new vehicle."""
    existing = db.query(Vehicle).filter(Vehicle.registration_number == request.registration_number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vehicle with this registration number already exists"
        )
    
    vehicle = Vehicle(
        registration_number=request.registration_number,
        vehicle_name=request.vehicle_name,
        vehicle_type=request.vehicle_type,
        max_load_capacity=request.max_load_capacity,
        acquisition_cost=request.acquisition_cost,
        status=VehicleStatusEnum.AVAILABLE
    )
    
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    
    return VehicleResponse.from_orm(vehicle)

@router.get("/", response_model=List[VehicleResponse])
def list_vehicles(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends()
):
    """List all vehicles."""
    vehicles = db.query(Vehicle).all()
    return [VehicleResponse.from_orm(v) for v in vehicles]

@router.get("/dispatch-available", response_model=List[VehicleResponse])
def get_dispatch_available_vehicles(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends()
):
    """Get only vehicles available for dispatch (AVAILABLE status only)."""
    vehicles = db.query(Vehicle).filter(
        Vehicle.status == VehicleStatusEnum.AVAILABLE
    ).all()
    return [VehicleResponse.from_orm(v) for v in vehicles]

@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(
    vehicle_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends()
):
    """Get a specific vehicle by ID."""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return VehicleResponse.from_orm(vehicle)

@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: int,
    request: VehicleUpdate,
    current_user: dict = Depends(require_role("fleet_manager")),
    db: Session = Depends()
):
    """Update a vehicle."""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    if request.vehicle_name:
        vehicle.vehicle_name = request.vehicle_name
    if request.vehicle_type:
        vehicle.vehicle_type = request.vehicle_type
    if request.max_load_capacity:
        vehicle.max_load_capacity = request.max_load_capacity
    if request.status:
        vehicle.status = VehicleStatusEnum(request.status)
    
    db.commit()
    db.refresh(vehicle)
    return VehicleResponse.from_orm(vehicle)