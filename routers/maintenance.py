from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import date
import models, schemas
from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


def to_out(m: models.MaintenanceLog) -> schemas.MaintenanceOut:
    return schemas.MaintenanceOut.from_orm(m)


def load_log(db: Session, id: int) -> models.MaintenanceLog:
    return (
        db.query(models.MaintenanceLog)
        .options(joinedload(models.MaintenanceLog.vehicle))
        .filter(models.MaintenanceLog.id == id)
        .first()
    )


@router.get("", response_model=list[schemas.MaintenanceOut])
def list_maintenance(
    vehicle_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(models.MaintenanceLog).options(joinedload(models.MaintenanceLog.vehicle))
    if vehicle_id:
        q = q.filter(models.MaintenanceLog.vehicle_id == vehicle_id)
    if status:
        q = q.filter(models.MaintenanceLog.status == status)
    logs = q.order_by(models.MaintenanceLog.created_at.desc()).all()
    return [to_out(m) for m in logs]


@router.post("", response_model=schemas.MaintenanceOut, status_code=201)
def create_maintenance(body: schemas.MaintenanceInput, db: Session = Depends(get_db), _=Depends(get_current_user)):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == body.vehicleId).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    log = models.MaintenanceLog(
        vehicle_id=body.vehicleId,
        type=body.type,
        description=body.description,
        cost=body.cost,
        start_date=body.startDate,
        status="Active",
        notes=body.notes,
    )
    db.add(log)

    # Business rule: active maintenance → vehicle to In Shop
    vehicle.status = "In Shop"
    db.commit()
    db.refresh(log)
    return to_out(load_log(db, log.id))


@router.get("/{id}", response_model=schemas.MaintenanceOut)
def get_maintenance(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    m = load_log(db, id)
    if not m:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    return to_out(m)


@router.patch("/{id}", response_model=schemas.MaintenanceOut)
def update_maintenance(id: int, body: schemas.MaintenanceUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    m = db.query(models.MaintenanceLog).filter(models.MaintenanceLog.id == id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    for field, col in [("type", "type"), ("description", "description"), ("cost", "cost"), ("notes", "notes")]:
        val = getattr(body, field, None)
        if val is not None:
            setattr(m, col, val)
    db.commit()
    db.refresh(m)
    return to_out(load_log(db, m.id))


@router.post("/{id}/close", response_model=schemas.MaintenanceOut)
def close_maintenance(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    m = load_log(db, id)
    if not m:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    if m.status == "Closed":
        raise HTTPException(status_code=400, detail="Maintenance record is already closed")

    m.status = "Closed"
    m.end_date = date.today()

    # Business rule: closing maintenance restores vehicle to Available (unless Retired)
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == m.vehicle_id).first()
    if vehicle and vehicle.status == "In Shop":
        vehicle.status = "Available"

    db.commit()
    db.refresh(m)
    return to_out(load_log(db, m.id))
