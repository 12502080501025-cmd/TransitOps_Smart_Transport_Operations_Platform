from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime

from transit_ops.models import (
    Trip, TripStatusEnum, Vehicle, VehicleStatusEnum,
    Driver, DriverStatusEnum
)
from transit_ops.auth import get_current_user, require_role

router = APIRouter()

class TripCreate(BaseModel):
    vehicle_id: int
    driver_id: int
    source: str
    destination: str
    cargo_weight: float
    planned_distance: float

class TripComplete(BaseModel):
    actual_distance: float
    fuel_consumed: float

class TripResponse(BaseModel):
    id: int
    vehicle_id: int
    driver_id: int
    source: str
    destination: str
    cargo_weight: float
    planned_distance: float
    actual_distance: float
    fuel_consumed: float
    status: str
    created_at: str
    dispatched_at: str
    completed_at: str

    class Config:
        from_attributes = True

@router.post("/create", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def create_trip(
    request: TripCreate,
    current_user: dict = Depends(require_role("fleet_manager")),
    db: Session = Depends()
):
    """Create trip with full validation."""
    vehicle = db.query(Vehicle).filter(Vehicle.id == request.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    driver = db.query(Driver).filter(Driver.id == request.driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    now = datetime.utcnow()
    
    if driver.license_expiry_date <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Driver's license has expired"
        )
    
    if driver.status != DriverStatusEnum.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Driver is not available (status: {driver.status.value})"
        )
    
    if vehicle.status != VehicleStatusEnum.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vehicle is not available (status: {vehicle.status.value})"
        )
    
    if request.cargo_weight > vehicle.max_load_capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cargo weight ({request.cargo_weight}kg) exceeds vehicle capacity ({vehicle.max_load_capacity}kg)"
        )
    
    trip = Trip(
        vehicle_id=request.vehicle_id,
        driver_id=request.driver_id,
        source=request.source,
        destination=request.destination,
        cargo_weight=request.cargo_weight,
        planned_distance=request.planned_distance,
        status=TripStatusEnum.DRAFT
    )
    
    db.add(trip)
    db.commit()
    db.refresh(trip)
    
    return TripResponse.from_orm(trip)

@router.post("/{trip_id}/dispatch", response_model=TripResponse)
def dispatch_trip(
    trip_id: int,
    current_user: dict = Depends(require_role("fleet_manager")),
    db: Session = Depends()
):
    """Dispatch trip and auto-set vehicle/driver to ON_TRIP."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.status != TripStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trip cannot be dispatched from {trip.status.value} status"
        )
    
    vehicle = db.query(Vehicle).filter(Vehicle.id == trip.vehicle_id).first()
    driver = db.query(Driver).filter(Driver.id == trip.driver_id).first()
    
    trip.status = TripStatusEnum.DISPATCHED
    trip.dispatched_at = datetime.utcnow()
    vehicle.status = VehicleStatusEnum.ON_TRIP
    driver.status = DriverStatusEnum.ON_TRIP
    
    db.commit()
    db.refresh(trip)
    
    return TripResponse.from_orm(trip)

@router.post("/{trip_id}/complete", response_model=TripResponse)
def complete_trip(
    trip_id: int,
    request: TripComplete,
    current_user: dict = Depends(require_role("fleet_manager")),
    db: Session = Depends()
):
    """Complete trip and restore vehicle/driver to AVAILABLE."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.status != TripStatusEnum.DISPATCHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only dispatched trips can be completed"
        )
    
    vehicle = db.query(Vehicle).filter(Vehicle.id == trip.vehicle_id).first()
    driver = db.query(Driver).filter(Driver.id == trip.driver_id).first()
    
    trip.status = TripStatusEnum.COMPLETED
    trip.completed_at = datetime.utcnow()
    trip.actual_distance = request.actual_distance
    trip.fuel_consumed = request.fuel_consumed
    
    vehicle.status = VehicleStatusEnum.AVAILABLE
    vehicle.odometer += request.actual_distance
    
    driver.status = DriverStatusEnum.AVAILABLE
    
    db.commit()
    db.refresh(trip)
    
    return TripResponse.from_orm(trip)

@router.post("/{trip_id}/cancel", response_model=TripResponse)
def cancel_trip(
    trip_id: int,
    current_user: dict = Depends(require_role("fleet_manager")),
    db: Session = Depends()
):
    """Cancel trip and restore resources."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.status == TripStatusEnum.CANCELLED or trip.status == TripStatusEnum.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a completed or already-cancelled trip"
        )
    
    vehicle = db.query(Vehicle).filter(Vehicle.id == trip.vehicle_id).first()
    driver = db.query(Driver).filter(Driver.id == trip.driver_id).first()
    
    trip.status = TripStatusEnum.CANCELLED
    
    if vehicle.status == VehicleStatusEnum.ON_TRIP:
        vehicle.status = VehicleStatusEnum.AVAILABLE
    
    if driver.status == DriverStatusEnum.ON_TRIP:
        driver.status = DriverStatusEnum.AVAILABLE
    
    db.commit()
    db.refresh(trip)
    
    return TripResponse.from_orm(trip)

@router.get("/", response_model=List[TripResponse])
def list_trips(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends()
):
    """List all trips."""
    trips = db.query(Trip).order_by(Trip.created_at.desc()).all()
    return [TripResponse.from_orm(t) for t in trips]

@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(
    trip_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends()
):
    """Get specific trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return TripResponse.from_orm(trip)