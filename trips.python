from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import datetime, date
import models, schemas
from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/trips", tags=["trips"])


def to_out(t: models.Trip) -> schemas.TripOut:
    return schemas.TripOut.from_orm(t)


def load_trip(db: Session, id: int) -> models.Trip:
    t = (
        db.query(models.Trip)
        .options(joinedload(models.Trip.vehicle), joinedload(models.Trip.driver))
        .filter(models.Trip.id == id)
        .first()
    )
    return t


@router.get("", response_model=list[schemas.TripOut])
def list_trips(
    status: Optional[str] = Query(None),
    vehicle_id: Optional[int] = Query(None),
    driver_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(models.Trip).options(
        joinedload(models.Trip.vehicle), joinedload(models.Trip.driver)
    )
    if status:
        q = q.filter(models.Trip.status == status)
    if vehicle_id:
        q = q.filter(models.Trip.vehicle_id == vehicle_id)
    if driver_id:
        q = q.filter(models.Trip.driver_id == driver_id)
    trips = q.order_by(models.Trip.created_at.desc()).all()
    return [to_out(t) for t in trips]


@router.post("", response_model=schemas.TripOut, status_code=201)
def create_trip(body: schemas.TripInput, db: Session = Depends(get_db), _=Depends(get_current_user)):
    # Validate vehicle
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == body.vehicleId).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if vehicle.status in ("Retired", "In Shop"):
        raise HTTPException(status_code=400, detail=f"Vehicle is {vehicle.status} and cannot be dispatched")
    if vehicle.status == "On Trip":
        raise HTTPException(status_code=400, detail="Vehicle is already on a trip")

    # Validate driver
    driver = db.query(models.Driver).filter(models.Driver.id == body.driverId).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if driver.status == "Suspended":
        raise HTTPException(status_code=400, detail="Driver is Suspended")
    if driver.status == "On Trip":
        raise HTTPException(status_code=400, detail="Driver is already on a trip")
    today = date.today()
    if driver.license_expiry < today:
        raise HTTPException(status_code=400, detail=f"Driver license expired on {driver.license_expiry}")

    # Validate cargo weight
    if body.cargoWeight > vehicle.max_load_capacity:
        raise HTTPException(
            status_code=400,
            detail=f"Cargo weight {body.cargoWeight}kg exceeds vehicle capacity {vehicle.max_load_capacity}kg",
        )

    trip = models.Trip(
        source=body.source,
        destination=body.destination,
        vehicle_id=body.vehicleId,
        driver_id=body.driverId,
        cargo_weight=body.cargoWeight,
        planned_distance=body.plannedDistance,
        revenue=body.revenue,
        notes=body.notes,
        status="Draft",
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return to_out(load_trip(db, trip.id))


@router.get("/{id}", response_model=schemas.TripOut)
def get_trip(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    t = load_trip(db, id)
    if not t:
        raise HTTPException(status_code=404, detail="Trip not found")
    return to_out(t)


@router.patch("/{id}", response_model=schemas.TripOut)
def update_trip(id: int, body: schemas.TripUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    t = db.query(models.Trip).filter(models.Trip.id == id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Trip not found")
    for field, col in [
        ("source", "source"), ("destination", "destination"),
        ("cargoWeight", "cargo_weight"), ("plannedDistance", "planned_distance"),
        ("revenue", "revenue"), ("notes", "notes"),
    ]:
        val = getattr(body, field, None)
        if val is not None:
            setattr(t, col, val)
    db.commit()
    db.refresh(t)
    return to_out(load_trip(db, t.id))


@router.post("/{id}/dispatch", response_model=schemas.TripOut)
def dispatch_trip(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    t = load_trip(db, id)
    if not t:
        raise HTTPException(status_code=404, detail="Trip not found")
    if t.status != "Draft":
        raise HTTPException(status_code=400, detail=f"Cannot dispatch a trip with status '{t.status}'")

    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == t.vehicle_id).first()
    driver = db.query(models.Driver).filter(models.Driver.id == t.driver_id).first()

    if vehicle.status in ("Retired", "In Shop", "On Trip"):
        raise HTTPException(status_code=400, detail=f"Vehicle is {vehicle.status}")
    if driver.status in ("Suspended", "On Trip"):
        raise HTTPException(status_code=400, detail=f"Driver is {driver.status}")

    today = date.today()
    if driver.license_expiry < today:
        raise HTTPException(status_code=400, detail="Driver license has expired")

    t.status = "Dispatched"
    t.dispatched_at = datetime.utcnow()
    vehicle.status = "On Trip"
    driver.status = "On Trip"
    db.commit()
    db.refresh(t)
    return to_out(load_trip(db, t.id))


@router.post("/{id}/complete", response_model=schemas.TripOut)
def complete_trip(id: int, body: schemas.TripCompleteInput, db: Session = Depends(get_db), _=Depends(get_current_user)):
    t = load_trip(db, id)
    if not t:
        raise HTTPException(status_code=404, detail="Trip not found")
    if t.status != "Dispatched":
        raise HTTPException(status_code=400, detail=f"Cannot complete a trip with status '{t.status}'")

    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == t.vehicle_id).first()
    driver = db.query(models.Driver).filter(models.Driver.id == t.driver_id).first()

    t.status = "Completed"
    t.actual_distance = body.actualDistance
    t.fuel_consumed = body.fuelConsumed
    t.completed_at = datetime.utcnow()

    # Update odometer
    if vehicle:
        vehicle.odometer = (vehicle.odometer or 0) + body.actualDistance
        vehicle.status = "Available"

    if driver:
        driver.status = "Available"

    db.commit()
    db.refresh(t)
    return to_out(load_trip(db, t.id))


@router.post("/{id}/cancel", response_model=schemas.TripOut)
def cancel_trip(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    t = load_trip(db, id)
    if not t:
        raise HTTPException(status_code=404, detail="Trip not found")
    if t.status not in ("Draft", "Dispatched"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel a trip with status '{t.status}'")

    was_dispatched = t.status == "Dispatched"
    t.status = "Cancelled"

    if was_dispatched:
        vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == t.vehicle_id).first()
        driver = db.query(models.Driver).filter(models.Driver.id == t.driver_id).first()
        if vehicle and vehicle.status == "On Trip":
            vehicle.status = "Available"
        if driver and driver.status == "On Trip":
            driver.status = "Available"

    db.commit()
    db.refresh(t)
    return to_out(load_trip(db, t.id))
