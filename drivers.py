from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/drivers", tags=["Drivers"])

MANAGE_ROLES = [models.UserRole.fleet_manager, models.UserRole.safety_officer]


@router.get("", response_model=List[schemas.DriverOut])
def list_drivers(
    status: Optional[models.DriverStatus] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    q = db.query(models.Driver)
    if status:
        q = q.filter(models.Driver.status == status)
    return q.order_by(models.Driver.created_at.desc()).all()


@router.get("/available-for-dispatch", response_model=List[schemas.DriverOut])
def available_for_dispatch(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Drivers eligible for a new trip: not Suspended, not already On Trip, license not expired."""
    today = date.today()
    return (
        db.query(models.Driver)
        .filter(
            models.Driver.status == models.DriverStatus.Available,
            models.Driver.license_expiry_date >= today,
        )
        .all()
    )


@router.get("/{driver_id}", response_model=schemas.DriverOut)
def get_driver(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    d = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Driver not found")
    return d


@router.post("", response_model=schemas.DriverOut, status_code=201)
def create_driver(
    payload: schemas.DriverCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*MANAGE_ROLES)),
):
    existing = (
        db.query(models.Driver)
        .filter(models.Driver.license_number == payload.license_number)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="License number already registered")
    d = models.Driver(**payload.model_dump())
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.put("/{driver_id}", response_model=schemas.DriverOut)
def update_driver(
    driver_id: str,
    payload: schemas.DriverUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*MANAGE_ROLES)),
):
    d = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Driver not found")
    if d.status == models.DriverStatus.OnTrip and payload.status and payload.status != models.DriverStatus.OnTrip:
        raise HTTPException(
            status_code=400, detail="Cannot manually change status of a driver currently On Trip"
        )
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(d, field, value)
    db.commit()
    db.refresh(d)
    return d


@router.delete("/{driver_id}", status_code=204)
def delete_driver(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*MANAGE_ROLES)),
):
    d = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Driver not found")
    if d.status == models.DriverStatus.OnTrip:
        raise HTTPException(status_code=400, detail="Cannot delete a driver that is On Trip")
    db.delete(d)
    db.commit()
    return None