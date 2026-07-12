from datetime import date, datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/trips", tags=["Trips"])

MANAGE_ROLES = [models.UserRole.fleet_manager, models.UserRole.driver]


def _to_out(t: models.Trip) -> schemas.TripOut:
    out = schemas.TripOut.model_validate(t)
    out.vehicle_registration = t.vehicle.registration_number if t.vehicle else None
    out.driver_name = t.driver.name if t.driver else None
    return out


@router.get("", response_model=List[schemas.TripOut])
def list_trips(
    status: Optional[models.TripStatus] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    q = db.query(models.Trip)
    if status:
        q = q.filter(models.Trip.status == status)
    trips = q.order_by(models.Trip.created_at.desc()).all()
    return [_to_out(t) for t in trips]


@router.get("/{trip_id}", response_model=schemas.TripOut)
def get_trip(
    trip_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    t = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Trip not found")
    return _to_out(t)


@router.post("", response_model=schemas.TripOut, status_code=201)
def create_trip(
    payload: schemas.TripCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*MANAGE_ROLES)),
):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == payload.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    driver = db.query(models.Driver).filter(models.Driver.id == payload.driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # --- Mandatory business rules ---
    if vehicle.status in (models.VehicleStatus.Retired, models.VehicleStatus.InShop):
        raise HTTPException(status_code=400, detail="Retired or In Shop vehicles cannot be dispatched")
    if vehicle.status == models.VehicleStatus.OnTrip:
        raise HTTPException(status_code=400, detail="Vehicle is already assigned to another trip")
    if driver.status == models.DriverStatus.Suspended:
        raise HTTPException(status_code=400, detail="Suspended drivers cannot be assigned to trips")
    if driver.license_expiry_date < date.today():
        raise HTTPException(status_code=400, detail="Driver's license has expired")
    if driver.status == models.DriverStatus.OnTrip:
        raise HTTPException(status_code=400, detail="Driver is already assigned to another trip")
    if payload.cargo_weight > vehicle.max_load_capacity:
        raise HTTPException(
            status_code=400,
            detail=f"Cargo weight ({payload.cargo_weight} kg) exceeds vehicle's max load capacity ({vehicle.max_load_capacity} kg)",
        )

    trip = models.Trip(
        source=payload.source,
        destination=payload.destination,
        vehicle_id=payload.vehicle_id,
        driver_id=payload.driver_id,
        cargo_weight=payload.cargo_weight,
        planned_distance=payload.planned_distance,
        revenue=payload.revenue or 0,
        status=models.TripStatus.Draft,
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return _to_out(trip)


@router.post("/{trip_id}/dispatch", response_model=schemas.TripOut)
def dispatch_trip(
    trip_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*MANAGE_ROLES)),
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if trip.status != models.TripStatus.Draft:
        raise HTTPException(status_code=400, detail="Only Draft trips can be dispatched")

    vehicle = trip.vehicle
    driver = trip.driver
    if vehicle.status != models.VehicleStatus.Available:
        raise HTTPException(status_code=400, detail="Vehicle is no longer Available")
    if driver.status != models.DriverStatus.Available:
        raise HTTPException(status_code=400, detail="Driver is no longer Available")
    if driver.license_expiry_date < date.today():
        raise HTTPException(status_code=400, detail="Driver's license has expired")

    vehicle.status = models.VehicleStatus.OnTrip
    driver.status = models.DriverStatus.OnTrip
    trip.status = models.TripStatus.Dispatched
    trip.dispatched_at = datetime.utcnow()
    db.commit()
    db.refresh(trip)
    return _to_out(trip)


@router.post("/{trip_id}/complete", response_model=schemas.TripOut)
def complete_trip(
    trip_id: str,
    payload: schemas.TripCompleteRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*MANAGE_ROLES)),
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if trip.status != models.TripStatus.Dispatched:
        raise HTTPException(status_code=400, detail="Only Dispatched trips can be completed")

    vehicle = trip.vehicle
    driver = trip.driver
    if payload.final_odometer < vehicle.odometer:
        raise HTTPException(
            status_code=400, detail="Final odometer cannot be less than the vehicle's current odometer"
        )

    trip.actual_distance = round(payload.final_odometer - vehicle.odometer, 2)
    trip.fuel_consumed = payload.fuel_consumed
    trip.status = models.TripStatus.Completed
    trip.completed_at = datetime.utcnow()

    vehicle.odometer = payload.final_odometer
    vehicle.status = models.VehicleStatus.Available
    driver.status = models.DriverStatus.Available

    db.commit()
    db.refresh(trip)
    return _to_out(trip)


@router.post("/{trip_id}/cancel", response_model=schemas.TripOut)
def cancel_trip(
    trip_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*MANAGE_ROLES)),
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if trip.status not in (models.TripStatus.Draft, models.TripStatus.Dispatched):
        raise HTTPException(status_code=400, detail="Only Draft or Dispatched trips can be cancelled")

    if trip.status == models.TripStatus.Dispatched:
        trip.vehicle.status = models.VehicleStatus.Available
        trip.driver.status = models.DriverStatus.Available

    trip.status = models.TripStatus.Cancelled
    trip.cancelled_at = datetime.utcnow()
    db.commit()
    db.refresh(trip)
    return _to_out(trip)