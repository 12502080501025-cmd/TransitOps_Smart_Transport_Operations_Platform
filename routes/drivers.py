from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime

from transit_ops.models import Driver, DriverStatusEnum
from transit_ops.auth import get_current_user, require_role

router = APIRouter()

class DriverCreate(BaseModel):
    name: str
    license_number: str
    license_category: str
    license_expiry_date: str  # ISO format: "2025-12-31"
    contact_number: str

class DriverUpdate(BaseModel):
    name: str = None
    license_category: str = None
    license_expiry_date: str = None
    contact_number: str = None
    status: str = None

class DriverResponse(BaseModel):
    id: int
    name: str
    license_number: str
    license_category: str
    license_expiry_date: str
    contact_number: str
    safety_score: float
    status: str

    class Config:
        from_attributes = True

@router.post("/register", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
def register_driver(
    request: DriverCreate,
    current_user: dict = Depends(require_role("safety_officer", "fleet_manager")),
    db: Session = Depends()
):
    """Register a new driver."""
    
        existing = db.query(Driver).filter(Driver.license_number == request.license_number).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Driver with this license number already exists"
            )
        
        expiry = datetime.fromisoformat(request.license_expiry_date)
        
        driver = Driver(
            name=request.name,
            license_number=request.license_number,
            license_category=request.license_category,
            license_expiry_date=expiry,
            contact_number=request.contact_number,
            status=DriverStatusEnum.AVAILABLE
        )
        
        db.add(driver)
        db.commit()
        db.refresh(driver)
        
        return DriverResponse.from_orm(driver)
        db.close()

@router.get("/", response_model=List[DriverResponse])
def list_drivers(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends()
):
    """List all drivers."""
    
        drivers = db.query(Driver).all()
        return [DriverResponse.from_orm(d) for d in drivers]
        db.close()

@router.get("/dispatch-available", response_model=List[DriverResponse])
def get_dispatch_available_drivers(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends()
):
    """
    Get drivers available for dispatch.
    Rules:
    - Status must be AVAILABLE (not ON_TRIP, OFF_DUTY, SUSPENDED)
    - License must not be expired
    """
    
        now = datetime.utcnow()
        drivers = db.query(Driver).filter(
            Driver.status == DriverStatusEnum.AVAILABLE,
            Driver.license_expiry_date > now
        ).all()
        return [DriverResponse.from_orm(d) for d in drivers]
        db.close()

@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver(
    driver_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends()
):
    """Get a specific driver by ID."""
    
        driver = db.query(Driver).filter(Driver.id == driver_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        return DriverResponse.from_orm(driver)
        db.close()

@router.put("/{driver_id}", response_model=DriverResponse)
def update_driver(
    driver_id: int,
    request: DriverUpdate,
    current_user: dict = Depends(require_role("safety_officer", "fleet_manager")),
    db: Session = Depends()
):
    """Update a driver."""
    
        driver = db.query(Driver).filter(Driver.id == driver_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        if request.name:
            driver.name = request.name
        if request.license_category:
            driver.license_category = request.license_category
        if request.license_expiry_date:
            driver.license_expiry_date = datetime.fromisoformat(request.license_expiry_date)
        if request.contact_number:
            driver.contact_number = request.contact_number
        if request.status:
            driver.status = DriverStatusEnum(request.status)
        
        db.commit()
        db.refresh(driver)
        return DriverResponse.from_orm(driver)
        db.close()