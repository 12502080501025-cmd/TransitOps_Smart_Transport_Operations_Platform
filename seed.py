"""
Seed script to populate the database with test data.
Run with: python -m transit_ops.seed
"""

from datetime import datetime, timedelta
from transit_ops.models import (
    User, Vehicle, Driver, RoleEnum, VehicleStatusEnum, DriverStatusEnum,
    get_db_engine, get_db_session, init_db
)
from transit_ops.auth import hash_password
from transit_ops.config import DATABASE_URL

def seed_database():
    """Create tables and populate with test data."""
    
    # Initialize database
    engine = get_db_engine(DATABASE_URL)
    init_db(engine)
    SessionLocal = get_db_session(engine)
    db = SessionLocal()
    
    try:
        # Clear existing data (optional)
        db.query(User).delete()
        db.query(Vehicle).delete()
        db.query(Driver).delete()
        
        # Create test users
        users = [
            User(
                email="fleet_manager@transitops.com",
                password_hash=hash_password("password123"),
                full_name="Alice Manager",
                role=RoleEnum.FLEET_MANAGER
            ),
            User(
                email="driver@transitops.com",
                password_hash=hash_password("password123"),
                full_name="Bob Driver",
                role=RoleEnum.DRIVER
            ),
            User(
                email="safety@transitops.com",
                password_hash=hash_password("password123"),
                full_name="Charlie Safety",
                role=RoleEnum.SAFETY_OFFICER
            ),
            User(
                email="finance@transitops.com",
                password_hash=hash_password("password123"),
                full_name="Diana Finance",
                role=RoleEnum.FINANCIAL_ANALYST
            )
        ]
        
        db.add_all(users)
        db.commit()
        
        # Create test vehicles
        vehicles = [
            Vehicle(
                registration_number="VAN-001",
                vehicle_name="Van Alpha",
                vehicle_type="Van",
                max_load_capacity=1000.0,
                odometer=5000.0,
                acquisition_cost=25000.0,
                status=VehicleStatusEnum.AVAILABLE
            ),
            Vehicle(
                registration_number="VAN-002",
                vehicle_name="Van Beta",
                vehicle_type="Van",
                max_load_capacity=1000.0,
                odometer=3500.0,
                acquisition_cost=25000.0,
                status=VehicleStatusEnum.AVAILABLE
            ),
            Vehicle(
                registration_number="TRUCK-001",
                vehicle_name="Truck Gamma",
                vehicle_type="Truck",
                max_load_capacity=5000.0,
                odometer=12000.0,
                acquisition_cost=75000.0,
                status=VehicleStatusEnum.AVAILABLE
            ),
            Vehicle(
                registration_number="CAR-001",
                vehicle_name="Car Delta",
                vehicle_type="Car",
                max_load_capacity=300.0,
                odometer=2000.0,
                acquisition_cost=15000.0,
                status=VehicleStatusEnum.AVAILABLE
            )
        ]
        
        db.add_all(vehicles)
        db.commit()
        
        # Create test drivers
        future_date = datetime.utcnow() + timedelta(days=365)
        drivers = [
            Driver(
                name="Alex Smith",
                license_number="LIC-001",
                license_category="LMV",
                license_expiry_date=future_date,
                contact_number="9876543210",
                safety_score=95.0,
                status=DriverStatusEnum.AVAILABLE
            ),
            Driver(
                name="Betty Johnson",
                license_number="LIC-002",
                license_category="HMV",
                license_expiry_date=future_date,
                contact_number="9876543211",
                safety_score=92.0,
                status=DriverStatusEnum.AVAILABLE
            ),
            Driver(
                name="Charlie Brown",
                license_number="LIC-003",
                license_category="LMV",
                license_expiry_date=future_date,
                contact_number="9876543212",
                safety_score=88.0,
                status=DriverStatusEnum.AVAILABLE
            )
        ]
        
        db.add_all(drivers)
        db.commit()
        
        print("✓ Database seeded successfully!")
        print("\nTest Credentials:")
        print("  Fleet Manager: fleet_manager@transitops.com / password123")
        print("  Driver: driver@transitops.com / password123")
        print("  Safety Officer: safety@transitops.com / password123")
        print("  Financial Analyst: finance@transitops.com / password123")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()