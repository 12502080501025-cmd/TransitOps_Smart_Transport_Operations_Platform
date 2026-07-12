from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator

from .models import UserRole, VehicleStatus, DriverStatus, TripStatus, MaintenanceStatus


# ---------- Auth / User ----------
class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: UserRole


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Vehicle ----------
class VehicleBase(BaseModel):
    registration_number: str = Field(min_length=2, max_length=30)
    name_model: str = Field(min_length=2, max_length=100)
    type: str = Field(min_length=2, max_length=50)
    max_load_capacity: float = Field(gt=0)
    odometer: float = Field(ge=0, default=0)
    acquisition_cost: float = Field(ge=0, default=0)
    region: Optional[str] = ""

    @field_validator("registration_number")
    @classmethod
    def upper_reg(cls, v):
        return v.strip().upper()


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    name_model: Optional[str] = None
    type: Optional[str] = None
    max_load_capacity: Optional[float] = Field(default=None, gt=0)
    odometer: Optional[float] = Field(default=None, ge=0)
    acquisition_cost: Optional[float] = Field(default=None, ge=0)
    region: Optional[str] = None
    status: Optional[VehicleStatus] = None


class VehicleOut(VehicleBase):
    id: str
    status: VehicleStatus
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Driver ----------
class DriverBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    license_number: str = Field(min_length=2, max_length=40)
    license_category: str = Field(min_length=1, max_length=20)
    license_expiry_date: date
    contact_number: str = Field(min_length=7, max_length=20)
    safety_score: float = Field(ge=0, le=100, default=100)

    @field_validator("contact_number")
    @classmethod
    def valid_phone(cls, v):
        digits = "".join(ch for ch in v if ch.isdigit())
        if len(digits) < 7:
            raise ValueError("contact number must contain at least 7 digits")
        return v


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    name: Optional[str] = None
    license_category: Optional[str] = None
    license_expiry_date: Optional[date] = None
    contact_number: Optional[str] = None
    safety_score: Optional[float] = Field(default=None, ge=0, le=100)
    status: Optional[DriverStatus] = None


class DriverOut(DriverBase):
    id: str
    status: DriverStatus
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Trip ----------
class TripCreate(BaseModel):
    source: str = Field(min_length=1, max_length=100)
    destination: str = Field(min_length=1, max_length=100)
    vehicle_id: str
    driver_id: str
    cargo_weight: float = Field(gt=0)
    planned_distance: float = Field(gt=0)
    revenue: Optional[float] = Field(default=0, ge=0)

    @field_validator("destination")
    @classmethod
    def diff_src_dst(cls, v, info):
        src = info.data.get("source")
        if src and v.strip().lower() == src.strip().lower():
            raise ValueError("source and destination must differ")
        return v


class TripCompleteRequest(BaseModel):
    final_odometer: float = Field(gt=0)
    fuel_consumed: float = Field(gt=0)


class TripOut(BaseModel):
    id: str
    source: str
    destination: str
    vehicle_id: str
    driver_id: str
    cargo_weight: float
    planned_distance: float
    actual_distance: Optional[float]
    fuel_consumed: Optional[float]
    revenue: float
    status: TripStatus
    created_at: datetime
    dispatched_at: Optional[datetime]
    completed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    vehicle_registration: Optional[str] = None
    driver_name: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Maintenance ----------
class MaintenanceCreate(BaseModel):
    vehicle_id: str
    service_type: str = Field(min_length=2, max_length=100)
    description: Optional[str] = ""
    cost: float = Field(ge=0, default=0)


class MaintenanceOut(BaseModel):
    id: str
    vehicle_id: str
    service_type: str
    description: str
    cost: float
    status: MaintenanceStatus
    created_at: datetime
    closed_at: Optional[datetime]
    vehicle_registration: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Fuel ----------
class FuelLogCreate(BaseModel):
    vehicle_id: str
    liters: float = Field(gt=0)
    cost: float = Field(gt=0)
    date: Optional[date] = None


class FuelLogOut(BaseModel):
    id: str
    vehicle_id: str
    liters: float
    cost: float
    date: date
    vehicle_registration: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Expense ----------
class ExpenseCreate(BaseModel):
    vehicle_id: str
    category: str = Field(min_length=2, max_length=50)
    amount: float = Field(gt=0)
    date: Optional[date] = None
    notes: Optional[str] = ""


class ExpenseOut(BaseModel):
    id: str
    vehicle_id: str
    category: str
    amount: float
    date: date
    notes: str
    vehicle_registration: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Dashboard / Reports ----------
class DashboardKPIs(BaseModel):
    active_vehicles: int
    available_vehicles: int
    vehicles_in_maintenance: int
    active_trips: int
    pending_trips: int
    drivers_on_duty: int
    fleet_utilization_pct: float


class VehicleReport(BaseModel):
    vehicle_id: str
    registration_number: str
    total_distance: float
    total_fuel: float
    fuel_efficiency: Optional[float]  # distance / fuel
    fuel_cost: float
    maintenance_cost: float
    other_expenses: float
    operational_cost: float
    revenue: float
    roi_pct: Optional[float]
