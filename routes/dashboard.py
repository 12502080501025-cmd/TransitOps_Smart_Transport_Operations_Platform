from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import csv
import io
from datetime import datetime

from -TransitOps-Smart-Transport-Operations-Platform.models import (
    Trip, Vehicle, Driver, FuelLog, MaintenanceLog,
    TripStatusEnum, VehicleStatusEnum, DriverStatusEnum, MaintenanceStatusEnum
)
from -TransitOps-Smart-Transport-Operations-Platform.auth import get_current_user

router = APIRouter()

class DashboardKPIs(BaseModel):
    active_vehicles: int
    available_vehicles: int
    vehicles_in_maintenance: int
    active_trips: int
    pending_trips: int
    drivers_on_duty: int
    fleet_utilization_percent: float

@router.get("/kpis", response_model=DashboardKPIs)
def get_dashboard_kpis(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends()
):
    """Get dashboard KPI metrics."""
    total_vehicles = db.query(Vehicle).count()
    available_vehicles = db.query(Vehicle).filter(
        Vehicle.status == VehicleStatusEnum.AVAILABLE
    ).count()
    on_trip_vehicles = db.query(Vehicle).filter(
        Vehicle.status == VehicleStatusEnum.ON_TRIP
    ).count()
    in_shop_vehicles = db.query(Vehicle).filter(
        Vehicle.status == VehicleStatusEnum.IN_SHOP
    ).count()
    
    active_trips = db.query(Trip).filter(
        Trip.status == TripStatusEnum.DISPATCHED
    ).count()
    pending_trips = db.query(Trip).filter(
        Trip.status == TripStatusEnum.DRAFT
    ).count()
    
    drivers_on_duty = db.query(Driver).filter(
        Driver.status.in_([DriverStatusEnum.ON_TRIP, DriverStatusEnum.AVAILABLE])
    ).count()
    
    fleet_utilization = 0.0
    if total_vehicles > 0:
        fleet_utilization = (on_trip_vehicles / total_vehicles) * 100
    
    return DashboardKPIs(
        active_vehicles=on_trip_vehicles,
        available_vehicles=available_vehicles,
        vehicles_in_maintenance=in_shop_vehicles,
        active_trips=active_trips,
        pending_trips=pending_trips,
        drivers_on_duty=drivers_on_duty,
        fleet_utilization_percent=round(fleet_utilization, 2)
    )

class FuelEfficiencyData(BaseModel):
    vehicle_id: int
    registration_number: str
    total_distance: float
    total_fuel: float
    efficiency: float

@router.get("/fuel-efficiency", response_model=List[FuelEfficiencyData])
def get_fuel_efficiency(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends()
):
    """Get fuel efficiency per vehicle."""
    vehicles = db.query(Vehicle).all()
    result = []
    
    for vehicle in vehicles:
        completed_trips = db.query(Trip).filter(
            Trip.vehicle_id == vehicle.id,
            Trip.status == TripStatusEnum.COMPLETED
        ).all()
        
        total_distance = sum(t.actual_distance or 0 for t in completed_trips)
        total_fuel = sum(log.liters for log in vehicle.fuel_logs)
        
        efficiency = 0.0
        if total_fuel > 0:
            efficiency = total_distance / total_fuel
        
        result.append(FuelEfficiencyData(
            vehicle_id=vehicle.id,
            registration_number=vehicle.registration_number,
            total_distance=round(total_distance, 2),
            total_fuel=round(total_fuel, 2),
            efficiency=round(efficiency, 2)
        ))
    
    return result

class OperationalCostData(BaseModel):
    vehicle_id: int
    registration_number: str
    fuel_cost: float
    maintenance_cost: float
    total_operational_cost: float

@router.get("/operational-cost", response_model=List[OperationalCostData])
def get_operational_costs(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends()
):
    """Get operational costs per vehicle."""
    vehicles = db.query(Vehicle).all()
    result = []
    
    for vehicle in vehicles:
        fuel_cost = sum(log.cost for log in vehicle.fuel_logs)
        maintenance_cost = sum(
            log.cost for log in vehicle.maintenance_logs
            if log.status == MaintenanceStatusEnum.CLOSED
        )
        
        result.append(OperationalCostData(
            vehicle_id=vehicle.id,
            registration_number=vehicle.registration_number,
            fuel_cost=round(fuel_cost, 2),
            maintenance_cost=round(maintenance_cost, 2),
            total_operational_cost=round(fuel_cost + maintenance_cost, 2)
        ))
    
    return result

@router.get("/export/trips")
def export_trips_csv(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends()
):
    """Export trips as CSV."""
    trips = db.query(Trip).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Trip ID", "Vehicle ID", "Driver ID", "Source", "Destination",
        "Cargo Weight (kg)", "Planned Distance (km)", "Actual Distance (km)",
        "Fuel Consumed (L)", "Status", "Created At", "Dispatched At", "Completed At"
    ])
    
    for trip in trips:
        writer.writerow([
            trip.id,
            trip.vehicle_id,
            trip.driver_id,
            trip.source,
            trip.destination,
            trip.cargo_weight,
            trip.planned_distance,
            trip.actual_distance or "",
            trip.fuel_consumed or "",
            trip.status.value,
            trip.created_at.isoformat() if trip.created_at else "",
            trip.dispatched_at.isoformat() if trip.dispatched_at else "",
            trip.completed_at.isoformat() if trip.completed_at else ""
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=trips.csv"}
    )

@router.get("/export/vehicles")
def export_vehicles_csv(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends()
):
    """Export vehicles as CSV."""
    vehicles = db.query(Vehicle).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Vehicle ID", "Registration Number", "Vehicle Name", "Type",
        "Max Load (kg)", "Odometer (km)", "Acquisition Cost", "Status"
    ])
    
    for vehicle in vehicles:
        writer.writerow([
            vehicle.id,
            vehicle.registration_number,
            vehicle.vehicle_name,
            vehicle.vehicle_type,
            vehicle.max_load_capacity,
            vehicle.odometer,
            vehicle.acquisition_cost,
            vehicle.status.value
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=vehicles.csv"}
    )