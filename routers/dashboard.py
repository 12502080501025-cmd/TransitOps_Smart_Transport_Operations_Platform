from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import models, schemas
from auth import get_current_user
from database import get_db
from datetime import datetime

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/kpis", response_model=schemas.DashboardKpis)
def get_kpis(db: Session = Depends(get_db), _=Depends(get_current_user)):
    total_vehicles = db.query(func.count(models.Vehicle.id)).scalar() or 0
    available_vehicles = db.query(func.count(models.Vehicle.id)).filter(models.Vehicle.status == "Available").scalar() or 0
    on_trip_vehicles = db.query(func.count(models.Vehicle.id)).filter(models.Vehicle.status == "On Trip").scalar() or 0
    in_shop_vehicles = db.query(func.count(models.Vehicle.id)).filter(models.Vehicle.status == "In Shop").scalar() or 0
    retired_vehicles = db.query(func.count(models.Vehicle.id)).filter(models.Vehicle.status == "Retired").scalar() or 0

    active_trips = db.query(func.count(models.Trip.id)).filter(models.Trip.status == "Dispatched").scalar() or 0
    pending_trips = db.query(func.count(models.Trip.id)).filter(models.Trip.status == "Draft").scalar() or 0
    completed_trips = db.query(func.count(models.Trip.id)).filter(models.Trip.status == "Completed").scalar() or 0

    total_drivers = db.query(func.count(models.Driver.id)).scalar() or 0
    on_duty_drivers = db.query(func.count(models.Driver.id)).filter(models.Driver.status == "On Trip").scalar() or 0
    available_drivers = db.query(func.count(models.Driver.id)).filter(models.Driver.status == "Available").scalar() or 0

    active_vehicles = on_trip_vehicles
    fleet_utilization = (on_trip_vehicles / total_vehicles * 100) if total_vehicles > 0 else 0.0

    total_fuel_cost = db.query(func.coalesce(func.sum(models.FuelLog.cost), 0)).scalar() or 0.0
    total_maintenance_cost = db.query(func.coalesce(func.sum(models.MaintenanceLog.cost), 0)).scalar() or 0.0

    return schemas.DashboardKpis(
        totalVehicles=total_vehicles,
        activeVehicles=active_vehicles,
        availableVehicles=available_vehicles,
        vehiclesInMaintenance=in_shop_vehicles,
        retiredVehicles=retired_vehicles,
        activeTrips=active_trips,
        pendingTrips=pending_trips,
        completedTrips=completed_trips,
        totalDrivers=total_drivers,
        driversOnDuty=on_duty_drivers,
        availableDrivers=available_drivers,
        fleetUtilization=round(fleet_utilization, 2),
        totalFuelCost=round(float(total_fuel_cost), 2),
        totalMaintenanceCost=round(float(total_maintenance_cost), 2),
    )


@router.get("/recent-activity", response_model=list[schemas.ActivityItem])
def get_recent_activity(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db), _=Depends(get_current_user)):
    items = []

    trips = db.query(models.Trip).order_by(models.Trip.created_at.desc()).limit(limit).all()
    for t in trips:
        ts = t.dispatched_at or t.completed_at or t.created_at or datetime.utcnow()
        items.append(schemas.ActivityItem(
            id=t.id,
            type="trip",
            description=f"Trip: {t.source} → {t.destination}",
            status=t.status,
            timestamp=ts,
        ))

    maint = db.query(models.MaintenanceLog).order_by(models.MaintenanceLog.created_at.desc()).limit(limit).all()
    for m in maint:
        items.append(schemas.ActivityItem(
            id=m.id,
            type="maintenance",
            description=f"Maintenance ({m.type}) on vehicle #{m.vehicle_id}",
            status=m.status,
            timestamp=m.created_at or datetime.utcnow(),
        ))

    items.sort(key=lambda x: x.timestamp, reverse=True)
    return items[:limit]
