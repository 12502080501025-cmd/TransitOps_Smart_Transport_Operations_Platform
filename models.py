from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum

Base = declarative_base()

class RoleEnum(str, enum.Enum):
    FLEET_MANAGER = "fleet_manager"
    DRIVER = "driver"
    SAFETY_OFFICER = "safety_officer"
    FINANCIAL_ANALYST = "financial_analyst"

class VehicleStatusEnum(str, enum.Enum):
    AVAILABLE = "available"
    ON_TRIP = "on_trip"
    IN_SHOP = "in_shop"
    RETIRED = "retired"

class DriverStatusEnum(str, enum.Enum):
    AVAILABLE = "available"
    ON_TRIP = "on_trip"
    OFF_DUTY = "off_duty"
    SUSPENDED = "suspended"

class TripStatusEnum(str, enum.Enum):
    DRAFT = "draft"
    DISPATCHED = "dispatched"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class MaintenanceStatusEnum(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True)
    registration_number = Column(String(50), unique=True, nullable=False, index=True)
    vehicle_name = Column(String(255), nullable=False)
    vehicle_type = Column(String(100), nullable=False)  # e.g., "Van", "Truck", "Car"
    max_load_capacity = Column(Float, nullable=False)  # kg
    odometer = Column(Float, default=0.0)  # km
    acquisition_cost = Column(Float, nullable=False)  # for ROI calculation
    status = Column(Enum(VehicleStatusEnum), default=VehicleStatusEnum.AVAILABLE, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    trips = relationship("Trip", back_populates="vehicle")
    maintenance_logs = relationship("MaintenanceLog", back_populates="vehicle")
    fuel_logs = relationship("FuelLog", back_populates="vehicle")
    
    def __repr__(self):
        return f"<Vehicle {self.registration_number} ({self.status})>"

class Driver(Base):
    __tablename__ = "drivers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    license_number = Column(String(50), unique=True, nullable=False, index=True)
    license_category = Column(String(10), nullable=False)  # e.g., "LMV", "HMV"
    license_expiry_date = Column(DateTime, nullable=False)
    contact_number = Column(String(20), nullable=False)
    safety_score = Column(Float, default=100.0)  # starts at 100, can decrease
    status = Column(Enum(DriverStatusEnum), default=DriverStatusEnum.AVAILABLE, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    trips = relationship("Trip", back_populates="driver")
    
    def __repr__(self):
        return f"<Driver {self.name} ({self.status})>"

class Trip(Base):
    __tablename__ = "trips"
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False, index=True)
    source = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    cargo_weight = Column(Float, nullable=False)  # kg
    planned_distance = Column(Float, nullable=False)  # km
    status = Column(Enum(TripStatusEnum), default=TripStatusEnum.DRAFT, index=True)
    actual_distance = Column(Float, nullable=True)  # filled on completion
    fuel_consumed = Column(Float, nullable=True)  # liters, filled on completion
    created_at = Column(DateTime, default=datetime.utcnow)
    dispatched_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    vehicle = relationship("Vehicle", back_populates="trips")
    driver = relationship("Driver", back_populates="trips")
    
    def __repr__(self):
        return f"<Trip {self.id} {self.source}->{self.destination} ({self.status})>"

class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    maintenance_type = Column(String(100), nullable=False)  # e.g., "Oil Change", "Tire Replacement"
    status = Column(Enum(MaintenanceStatusEnum), default=MaintenanceStatusEnum.OPEN, index=True)
    cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    
    vehicle = relationship("Vehicle", back_populates="maintenance_logs")
    
    def __repr__(self):
        return f"<MaintenanceLog {self.id} {self.vehicle_id} ({self.status})>"

class FuelLog(Base):
    __tablename__ = "fuel_logs"
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    liters = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    notes = Column(Text, nullable=True)
    
    vehicle = relationship("Vehicle", back_populates="fuel_logs")
    
    def __repr__(self):
        return f"<FuelLog {self.id} {self.vehicle_id} {self.liters}L>"

# Database connection setup
def get_db_engine(database_url: str):
    """Create SQLAlchemy engine for the given database URL."""
    return create_engine(database_url, echo=False)

def get_db_session(engine):
    """Create a session factory for database operations."""
    return sessionmaker(bind=engine)

def init_db(engine):
    """Create all tables in the database."""
    Base.metadata.create_all(engine)