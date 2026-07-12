from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import models, schemas
from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


def to_out(v: models.Vehicle) -> schemas.VehicleOut:
    return schemas.VehicleOut.from_orm(v)


@router.get("", response_model=list[schemas.VehicleOut])
def list_vehicles(
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(models.Vehicle)
    if status:
        q = q.filter(models.Vehicle.status == status)
    if type:
        q = q.filter(models.Vehicle.type == type)
    if search:
        q = q.filter(
            (models.Vehicle.name.ilike(f"%{search}%")) |
            (models.Vehicle.registration_number.ilike(f"%{search}%"))
        )
    vehicles = q.order_by(models.Vehicle.created_at.desc()).all()
    return [to_out(v) for v in vehicles]


@router.post("", response_model=schemas.VehicleOut, status_code=201)
def create_vehicle(body: schemas.VehicleInput, db: Session = Depends(get_db), _=Depends(get_current_user)):
    existing = db.query(models.Vehicle).filter(models.Vehicle.registration_number == body.registrationNumber).first()
    if existing:
        raise HTTPException(status_code=409, detail="Registration number already exists")
    vehicle = models.Vehicle(
        registration_number=body.registrationNumber,
        name=body.name,
        type=body.type,
        max_load_capacity=body.maxLoadCapacity,
        odometer=body.odometer,
        acquisition_cost=body.acquisitionCost,
        status=body.status or "Available",
        notes=body.notes,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return to_out(vehicle)


@router.get("/{id}", response_model=schemas.VehicleOut)
def get_vehicle(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    v = db.query(models.Vehicle).filter(models.Vehicle.id == id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return to_out(v)


@router.patch("/{id}", response_model=schemas.VehicleOut)
def update_vehicle(id: int, body: schemas.VehicleUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    v = db.query(models.Vehicle).filter(models.Vehicle.id == id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    for field, col in [
        ("name", "name"), ("type", "type"), ("maxLoadCapacity", "max_load_capacity"),
        ("odometer", "odometer"), ("acquisitionCost", "acquisition_cost"),
        ("status", "status"), ("notes", "notes"),
    ]:
        val = getattr(body, field, None)
        if val is not None:
            setattr(v, col, val)
    db.commit()
    db.refresh(v)
    return to_out(v)


@router.delete("/{id}", status_code=204)
def delete_vehicle(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    v = db.query(models.Vehicle).filter(models.Vehicle.id == id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    db.delete(v)
    db.commit()
