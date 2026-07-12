from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List
from datetime import datetime, date


# ── Auth ──────────────────────────────────────────────────────────────────────
class LoginInput(BaseModel):
    email: str
    password: str


class RegisterInput(BaseModel):
    email: str
    password: str
    name: str
    role: str  # Fleet Manager | Driver | Safety Officer | Financial Analyst


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    createdAt: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_user(cls, u):
        return cls(id=u.id, email=u.email, name=u.name, role=u.role, createdAt=u.created_at)


class AuthResponse(BaseModel):
    token: str
    user: UserOut


# ── Dashboard ─────────────────────────────────────────────────────────────────
class DashboardKpis(BaseModel):
    totalVehicles: int
    activeVehicles: int
    availableVehicles: int
    vehiclesInMaintenance: int
    retiredVehicles: int
    activeTrips: int
    pendingTrips: int
    completedTrips: int
    totalDrivers: int
    driversOnDuty: int
    availableDrivers: int
    fleetUtilization: float
    totalFuelCost: float
    totalMaintenanceCost: float


class ActivityItem(BaseModel):
    id: int
    type: str
    description: str
    status: Optional[str] = None
    timestamp: datetime


# ── Vehicle ───────────────────────────────────────────────────────────────────
class VehicleOut(BaseModel):
    id: int
    registrationNumber: str
    name: str
    type: str
    maxLoadCapacity: float
    odometer: float
    acquisitionCost: float
    status: str
    notes: Optional[str] = None
    createdAt: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, v):
        return cls(
            id=v.id,
            registrationNumber=v.registration_number,
            name=v.name,
            type=v.type,
            maxLoadCapacity=v.max_load_capacity,
            odometer=v.odometer or 0.0,
            acquisitionCost=v.acquisition_cost,
            status=v.status,
            notes=v.notes,
            createdAt=v.created_at,
        )


class VehicleInput(BaseModel):
    registrationNumber: str
    name: str
    type: str
    maxLoadCapacity: float
    odometer: float = 0.0
    acquisitionCost: float
    status: str = "Available"
    notes: Optional[str] = None


class VehicleUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    maxLoadCapacity: Optional[float] = None
    odometer: Optional[float] = None
    acquisitionCost: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None


# ── Driver ────────────────────────────────────────────────────────────────────
class DriverOut(BaseModel):
    id: int
    name: str
    licenseNumber: str
    licenseCategory: str
    licenseExpiry: date
    contactNumber: str
    safetyScore: float
    status: str
    notes: Optional[str] = None
    createdAt: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, d):
        return cls(
            id=d.id,
            name=d.name,
            licenseNumber=d.license_number,
            licenseCategory=d.license_category,
            licenseExpiry=d.license_expiry,
            contactNumber=d.contact_number,
            safetyScore=d.safety_score or 100.0,
            status=d.status,
            notes=d.notes,
            createdAt=d.created_at,
        )


class DriverInput(BaseModel):
    name: str
    licenseNumber: str
    licenseCategory: str
    licenseExpiry: date
    contactNumber: str
    safetyScore: float = 100.0
    status: str = "Available"
    notes: Optional[str] = None


class DriverUpdate(BaseModel):
    name: Optional[str] = None
    licenseCategory: Optional[str] = None
    licenseExpiry: Optional[date] = None
    contactNumber: Optional[str] = None
    safetyScore: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None


# ── Trip ──────────────────────────────────────────────────────────────────────
class TripOut(BaseModel):
    id: int
    source: str
    destination: str
    vehicleId: int
    driverId: int
    vehicle: Optional[VehicleOut] = None
    driver: Optional[DriverOut] = None
    cargoWeight: float
    plannedDistance: float
    actualDistance: Optional[float] = None
    fuelConsumed: Optional[float] = None
    revenue: Optional[float] = None
    status: str
    notes: Optional[str] = None
    dispatchedAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None
    createdAt: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, t):
        return cls(
            id=t.id,
            source=t.source,
            destination=t.destination,
            vehicleId=t.vehicle_id,
            driverId=t.driver_id,
            vehicle=VehicleOut.from_orm(t.vehicle) if t.vehicle else None,
            driver=DriverOut.from_orm(t.driver) if t.driver else None,
            cargoWeight=t.cargo_weight,
            plannedDistance=t.planned_distance,
            actualDistance=t.actual_distance,
            fuelConsumed=t.fuel_consumed,
            revenue=t.revenue,
            status=t.status,
            notes=t.notes,
            dispatchedAt=t.dispatched_at,
            completedAt=t.completed_at,
            createdAt=t.created_at,
        )


class TripInput(BaseModel):
    source: str
    destination: str
    vehicleId: int
    driverId: int
    cargoWeight: float
    plannedDistance: float
    revenue: Optional[float] = None
    notes: Optional[str] = None


class TripUpdate(BaseModel):
    source: Optional[str] = None
    destination: Optional[str] = None
    cargoWeight: Optional[float] = None
    plannedDistance: Optional[float] = None
    revenue: Optional[float] = None
    notes: Optional[str] = None


class TripCompleteInput(BaseModel):
    actualDistance: float
    fuelConsumed: float


# ── Maintenance ───────────────────────────────────────────────────────────────
class MaintenanceOut(BaseModel):
    id: int
    vehicleId: int
    vehicle: Optional[VehicleOut] = None
    type: str
    description: str
    cost: float
    status: str
    startDate: date
    endDate: Optional[date] = None
    notes: Optional[str] = None
    createdAt: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, m):
        return cls(
            id=m.id,
            vehicleId=m.vehicle_id,
            vehicle=VehicleOut.from_orm(m.vehicle) if m.vehicle else None,
            type=m.type,
            description=m.description,
            cost=m.cost,
            status=m.status,
            startDate=m.start_date,
            endDate=m.end_date,
            notes=m.notes,
            createdAt=m.created_at,
        )


class MaintenanceInput(BaseModel):
    vehicleId: int
    type: str
    description: str
    cost: float
    startDate: date
    notes: Optional[str] = None


class MaintenanceUpdate(BaseModel):
    type: Optional[str] = None
    description: Optional[str] = None
    cost: Optional[float] = None
    notes: Optional[str] = None


# ── FuelLog ───────────────────────────────────────────────────────────────────
class FuelLogOut(BaseModel):
    id: int
    vehicleId: int
    vehicle: Optional[VehicleOut] = None
    tripId: Optional[int] = None
    litres: float
    cost: float
    date: date
    odometer: Optional[float] = None
    notes: Optional[str] = None
    createdAt: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, f):
        return cls(
            id=f.id,
            vehicleId=f.vehicle_id,
            vehicle=VehicleOut.from_orm(f.vehicle) if f.vehicle else None,
            tripId=f.trip_id,
            litres=f.litres,
            cost=f.cost,
            date=f.date,
            odometer=f.odometer,
            notes=f.notes,
            createdAt=f.created_at,
        )


class FuelLogInput(BaseModel):
    vehicleId: int
    tripId: Optional[int] = None
    litres: float
    cost: float
    date: date
    odometer: Optional[float] = None
    notes: Optional[str] = None


class FuelLogUpdate(BaseModel):
    litres: Optional[float] = None
    cost: Optional[float] = None
    date: Optional[date] = None
    odometer: Optional[float] = None
    notes: Optional[str] = None


# ── Expense ───────────────────────────────────────────────────────────────────
class ExpenseOut(BaseModel):
    id: int
    vehicleId: int
    vehicle: Optional[VehicleOut] = None
    tripId: Optional[int] = None
    type: str
    amount: float
    date: date
    description: str
    notes: Optional[str] = None
    createdAt: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, e):
        return cls(
            id=e.id,
            vehicleId=e.vehicle_id,
            vehicle=VehicleOut.from_orm(e.vehicle) if e.vehicle else None,
            tripId=e.trip_id,
            type=e.type,
            amount=e.amount,
            date=e.date,
            description=e.description,
            notes=e.notes,
            createdAt=e.created_at,
        )


class ExpenseInput(BaseModel):
    vehicleId: int
    tripId: Optional[int] = None
    type: str
    amount: float
    date: date
    description: str
    notes: Optional[str] = None


class ExpenseUpdate(BaseModel):
    type: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[date] = None
    description: Optional[str] = None
    notes: Optional[str] = None


# ── Reports ───────────────────────────────────────────────────────────────────
class FuelEfficiencyItem(BaseModel):
    vehicleId: int
    vehicleName: str
    registrationNumber: str
    totalDistance: float
    totalFuel: float
    efficiency: float


class FleetUtilizationReport(BaseModel):
    utilizationPercentage: float
    available: int
    onTrip: int
    inShop: int
    retired: int
    totalVehicles: int


class OperationalCostItem(BaseModel):
    vehicleId: int
    vehicleName: str
    registrationNumber: str
    fuelCost: float
    maintenanceCost: float
    otherExpenses: float
    totalCost: float


class VehicleRoiItem(BaseModel):
    vehicleId: int
    vehicleName: str
    registrationNumber: str
    acquisitionCost: float
    revenue: float
    totalCost: float
    roi: float
