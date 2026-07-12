import csv
import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import models, schemas
from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/fuel-efficiency", response_model=list[schemas.FuelEfficiencyItem])
def fuel_efficiency(db: Session = Depends(get_db), _=Depends(get_current_user)):
    vehicles = db.query(models.Vehicle).all()
    result = []
    for v in vehicles:
        total_fuel = sum(f.litres for f in v.fuel_logs) if v.fuel_logs else 0
        total_distance = sum(t.actual_distance for t in v.trips if t.actual_distance and t.status == "Completed") if v.trips else 0
        efficiency = round(total_distance / total_fuel, 2) if total_fuel > 0 else 0.0
        result.append(schemas.FuelEfficiencyItem(
            vehicleId=v.id,
            vehicleName=v.name,
            registrationNumber=v.registration_number,
            totalDistance=round(total_distance, 2),
            totalFuel=round(total_fuel, 2),
            efficiency=efficiency,
        ))
    return sorted(result, key=lambda x: x.efficiency, reverse=True)


@router.get("/fleet-utilization", response_model=schemas.FleetUtilizationReport)
def fleet_utilization(db: Session = Depends(get_db), _=Depends(get_current_user)):
    total = db.query(func.count(models.Vehicle.id)).scalar() or 0
    available = db.query(func.count(models.Vehicle.id)).filter(models.Vehicle.status == "Available").scalar() or 0
    on_trip = db.query(func.count(models.Vehicle.id)).filter(models.Vehicle.status == "On Trip").scalar() or 0
    in_shop = db.query(func.count(models.Vehicle.id)).filter(models.Vehicle.status == "In Shop").scalar() or 0
    retired = db.query(func.count(models.Vehicle.id)).filter(models.Vehicle.status == "Retired").scalar() or 0
    utilization = round(on_trip / total * 100, 2) if total > 0 else 0.0
    return schemas.FleetUtilizationReport(
        utilizationPercentage=utilization,
        available=available,
        onTrip=on_trip,
        inShop=in_shop,
        retired=retired,
        totalVehicles=total,
    )


@router.get("/operational-cost", response_model=list[schemas.OperationalCostItem])
def operational_cost(db: Session = Depends(get_db), _=Depends(get_current_user)):
    vehicles = db.query(models.Vehicle).all()
    result = []
    for v in vehicles:
        fuel_cost = sum(f.cost for f in v.fuel_logs) if v.fuel_logs else 0.0
        maint_cost = sum(m.cost for m in v.maintenance_logs) if v.maintenance_logs else 0.0
        other = sum(e.amount for e in v.expenses) if v.expenses else 0.0
        total = fuel_cost + maint_cost + other
        result.append(schemas.OperationalCostItem(
            vehicleId=v.id,
            vehicleName=v.name,
            registrationNumber=v.registration_number,
            fuelCost=round(fuel_cost, 2),
            maintenanceCost=round(maint_cost, 2),
            otherExpenses=round(other, 2),
            totalCost=round(total, 2),
        ))
    return sorted(result, key=lambda x: x.totalCost, reverse=True)


@router.get("/vehicle-roi", response_model=list[schemas.VehicleRoiItem])
def vehicle_roi(db: Session = Depends(get_db), _=Depends(get_current_user)):
    vehicles = db.query(models.Vehicle).all()
    result = []
    for v in vehicles:
        fuel_cost = sum(f.cost for f in v.fuel_logs) if v.fuel_logs else 0.0
        maint_cost = sum(m.cost for m in v.maintenance_logs) if v.maintenance_logs else 0.0
        other = sum(e.amount for e in v.expenses) if v.expenses else 0.0
        total_cost = fuel_cost + maint_cost + other
        revenue = sum(t.revenue for t in v.trips if t.revenue and t.status == "Completed") if v.trips else 0.0
        roi = round((revenue - total_cost) / v.acquisition_cost, 4) if v.acquisition_cost > 0 else 0.0
        result.append(schemas.VehicleRoiItem(
            vehicleId=v.id,
            vehicleName=v.name,
            registrationNumber=v.registration_number,
            acquisitionCost=round(v.acquisition_cost, 2),
            revenue=round(revenue, 2),
            totalCost=round(total_cost, 2),
            roi=roi,
        ))
    return sorted(result, key=lambda x: x.roi, reverse=True)


@router.get("/export-csv")
def export_csv(
    type: str = Query(..., description="vehicles|drivers|trips|fuel-logs|expenses"),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    output = io.StringIO()
    writer = csv.writer(output)

    if type == "vehicles":
        writer.writerow(["ID", "Registration", "Name", "Type", "Max Load (kg)", "Odometer (km)", "Acquisition Cost", "Status"])
        for v in db.query(models.Vehicle).all():
            writer.writerow([v.id, v.registration_number, v.name, v.type, v.max_load_capacity, v.odometer, v.acquisition_cost, v.status])
    elif type == "drivers":
        writer.writerow(["ID", "Name", "License Number", "Category", "License Expiry", "Contact", "Safety Score", "Status"])
        for d in db.query(models.Driver).all():
            writer.writerow([d.id, d.name, d.license_number, d.license_category, d.license_expiry, d.contact_number, d.safety_score, d.status])
    elif type == "trips":
        writer.writerow(["ID", "Source", "Destination", "Vehicle ID", "Driver ID", "Cargo (kg)", "Planned Dist (km)", "Actual Dist", "Fuel Consumed", "Revenue", "Status"])
        for t in db.query(models.Trip).all():
            writer.writerow([t.id, t.source, t.destination, t.vehicle_id, t.driver_id, t.cargo_weight, t.planned_distance, t.actual_distance, t.fuel_consumed, t.revenue, t.status])
    elif type == "fuel-logs":
        writer.writerow(["ID", "Vehicle ID", "Trip ID", "Litres", "Cost", "Date", "Odometer"])
        for f in db.query(models.FuelLog).all():
            writer.writerow([f.id, f.vehicle_id, f.trip_id, f.litres, f.cost, f.date, f.odometer])
    elif type == "expenses":
        writer.writerow(["ID", "Vehicle ID", "Trip ID", "Type", "Amount", "Date", "Description"])
        for e in db.query(models.Expense).all():
            writer.writerow([e.id, e.vehicle_id, e.trip_id, e.type, e.amount, e.date, e.description])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={type}.csv"},
    )
