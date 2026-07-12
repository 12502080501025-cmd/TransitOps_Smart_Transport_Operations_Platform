from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import models, schemas
from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/drivers", tags=["drivers"])


def to_out(d: models.Driver) -> schemas.DriverOut:
    return schemas.DriverOut.from_orm(d)


@router.get("", response_model=list[schemas.DriverOut])
def list_drivers(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(models.Driver)
    if status:
        q = q.filter(models.Driver.status == status)
    if search:
        q = q.filter(
            (models.Driver.name.ilike(f"%{search}%")) |
            (models.Driver.license_number.ilike(f"%{search}%"))
        )
    drivers = q.order_by(models.Driver.created_at.desc()).all()
    return [to_out(d) for d in drivers]


@router.post("", response_model=schemas.DriverOut, status_code=201)
def create_driver(body: schemas.DriverInput, db: Session = Depends(get_db), _=Depends(get_current_user)):
    existing = db.query(models.Driver).filter(models.Driver.license_number == body.licenseNumber).first()
    if existing:
        raise HTTPException(status_code=409, detail="License number already registered")
    driver = models.Driver(
        name=body.name,
        license_number=body.licenseNumber,
        license_category=body.licenseCategory,
        license_expiry=body.licenseExpiry,
        contact_number=body.contactNumber,
        safety_score=body.safetyScore,
        status=body.status or "Available",
        notes=body.notes,
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return to_out(driver)


@router.get("/{id}", response_model=schemas.DriverOut)
def get_driver(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    d = db.query(models.Driver).filter(models.Driver.id == id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Driver not found")
    return to_out(d)


@router.patch("/{id}", response_model=schemas.DriverOut)
def update_driver(id: int, body: schemas.DriverUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    d = db.query(models.Driver).filter(models.Driver.id == id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Driver not found")
    for field, col in [
        ("name", "name"), ("licenseCategory", "license_category"),
        ("licenseExpiry", "license_expiry"), ("contactNumber", "contact_number"),
        ("safetyScore", "safety_score"), ("status", "status"), ("notes", "notes"),
    ]:
        val = getattr(body, field, None)
        if val is not None:
            setattr(d, col, val)
    db.commit()
    db.refresh(d)
    return to_out(d)


@router.delete("/{id}", status_code=204)
def delete_driver(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    d = db.query(models.Driver).filter(models.Driver.id == id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Driver not found")
    db.delete(d)
    db.commit()
