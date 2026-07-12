from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
import models, schemas
from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/fuel-logs", tags=["fuel-logs"])


def to_out(f: models.FuelLog) -> schemas.FuelLogOut:
    return schemas.FuelLogOut.from_orm(f)


def load_log(db: Session, id: int) -> models.FuelLog:
    return (
        db.query(models.FuelLog)
        .options(joinedload(models.FuelLog.vehicle))
        .filter(models.FuelLog.id == id)
        .first()
    )


@router.get("", response_model=list[schemas.FuelLogOut])
def list_fuel_logs(
    vehicle_id: Optional[int] = Query(None),
    trip_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(models.FuelLog).options(joinedload(models.FuelLog.vehicle))
    if vehicle_id:
        q = q.filter(models.FuelLog.vehicle_id == vehicle_id)
    if trip_id:
        q = q.filter(models.FuelLog.trip_id == trip_id)
    logs = q.order_by(models.FuelLog.date.desc()).all()
    return [to_out(f) for f in logs]


@router.post("", response_model=schemas.FuelLogOut, status_code=201)
def create_fuel_log(body: schemas.FuelLogInput, db: Session = Depends(get_db), _=Depends(get_current_user)):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == body.vehicleId).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    log = models.FuelLog(
        vehicle_id=body.vehicleId,
        trip_id=body.tripId,
        litres=body.litres,
        cost=body.cost,
        date=body.date,
        odometer=body.odometer,
        notes=body.notes,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return to_out(load_log(db, log.id))


@router.get("/{id}", response_model=schemas.FuelLogOut)
def get_fuel_log(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    f = load_log(db, id)
    if not f:
        raise HTTPException(status_code=404, detail="Fuel log not found")
    return to_out(f)


@router.patch("/{id}", response_model=schemas.FuelLogOut)
def update_fuel_log(id: int, body: schemas.FuelLogUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    f = db.query(models.FuelLog).filter(models.FuelLog.id == id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Fuel log not found")
    for field, col in [
        ("litres", "litres"), ("cost", "cost"), ("date", "date"),
        ("odometer", "odometer"), ("notes", "notes"),
    ]:
        val = getattr(body, field, None)
        if val is not None:
            setattr(f, col, val)
    db.commit()
    db.refresh(f)
    return to_out(load_log(db, f.id))


@router.delete("/{id}", status_code=204)
def delete_fuel_log(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    f = db.query(models.FuelLog).filter(models.FuelLog.id == id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Fuel log not found")
    db.delete(f)
    db.commit()
