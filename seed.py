"""
Seed script — run once to populate the database with demo data.
Usage: python3 seed.py
"""
import sys
from datetime import date, timedelta
from database import SessionLocal
import models
from auth import hash_password


def seed():
    # Create all tables first (idempotent)
    from database import Base, engine
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Skip if already seeded
        if db.query(models.User).first():
            print("Database already seeded. Skipping.")
            return

        # Users (one per role)
        users = [
            models.User(email="fleet@transitops.com", password_hash=hash_password("password123"), name="Fleet Manager", role="Fleet Manager"),
            models.User(email="driver@transitops.com", password_hash=hash_password("password123"), name="Alex Driver", role="Driver"),
            models.User(email="safety@transitops.com", password_hash=hash_password("password123"), name="Safety Officer", role="Safety Officer"),
            models.User(email="finance@transitops.com", password_hash=hash_password("password123"), name="Finance Analyst", role="Financial Analyst"),
        ]
        db.add_all(users)
        db.flush()

        # Vehicles
        vehicles = [
            models.Vehicle(registration_number="VAN-001", name="Ford Transit Van", type="Van", max_load_capacity=800, odometer=45200, acquisition_cost=35000, status="Available"),
            models.Vehicle(registration_number="TRK-002", name="Isuzu NLR Truck", type="Truck", max_load_capacity=2500, odometer=120500, acquisition_cost=85000, status="Available"),
            models.Vehicle(registration_number="VAN-003", name="Toyota HiAce Van", type="Van", max_load_capacity=750, odometer=68300, acquisition_cost=42000, status="On Trip"),
            models.Vehicle(registration_number="TRK-004", name="Hino 300 Series", type="Truck", max_load_capacity=3000, odometer=98700, acquisition_cost=95000, status="In Shop"),
            models.Vehicle(registration_number="CAR-005", name="Toyota Corolla", type="Car", max_load_capacity=300, odometer=22400, acquisition_cost=28000, status="Available"),
            models.Vehicle(registration_number="BUS-006", name="Minibus 20-Seater", type="Bus", max_load_capacity=1500, odometer=180000, acquisition_cost=120000, status="Retired"),
        ]
        db.add_all(vehicles)
        db.flush()

        # Drivers
        today = date.today()
        drivers = [
            models.Driver(name="Alex Johnson", license_number="LIC-A001", license_category="C", license_expiry=today + timedelta(days=365), contact_number="+1-555-0101", safety_score=95),
            models.Driver(name="Maria Santos", license_number="LIC-B002", license_category="B", license_expiry=today + timedelta(days=180), contact_number="+1-555-0102", safety_score=88, status="On Trip"),
            models.Driver(name="James Wilson", license_number="LIC-C003", license_category="C", license_expiry=today + timedelta(days=20), contact_number="+1-555-0103", safety_score=72),
            models.Driver(name="Priya Patel", license_number="LIC-D004", license_category="D", license_expiry=today - timedelta(days=30), contact_number="+1-555-0104", safety_score=60, status="Suspended"),
            models.Driver(name="Tom Chen", license_number="LIC-E005", license_category="B", license_expiry=today + timedelta(days=500), contact_number="+1-555-0105", safety_score=98),
        ]
        db.add_all(drivers)
        db.flush()

        # Trips
        trips = [
            models.Trip(source="Warehouse A", destination="Distribution Center B", vehicle_id=vehicles[2].id, driver_id=drivers[1].id, cargo_weight=600, planned_distance=250, revenue=1200, status="Dispatched"),
            models.Trip(source="Port Logistics Hub", destination="Retail Store C", vehicle_id=vehicles[0].id, driver_id=drivers[0].id, cargo_weight=400, planned_distance=85, revenue=650, status="Draft"),
            models.Trip(source="Factory X", destination="Warehouse D", vehicle_id=vehicles[1].id, driver_id=drivers[4].id, cargo_weight=2000, planned_distance=320, actual_distance=318, fuel_consumed=85, revenue=2400, status="Completed"),
            models.Trip(source="Airport Cargo", destination="Cold Storage E", vehicle_id=vehicles[4].id, driver_id=drivers[2].id, cargo_weight=150, planned_distance=45, status="Cancelled"),
        ]
        db.add_all(trips)
        db.flush()

        # Maintenance logs
        maintenance = [
            models.MaintenanceLog(vehicle_id=vehicles[3].id, type="Engine Repair", description="Major engine overhaul due to excessive oil consumption", cost=3200, status="Active", start_date=today - timedelta(days=3)),
            models.MaintenanceLog(vehicle_id=vehicles[1].id, type="Tire Replacement", description="Replaced all 6 tires with Bridgestone", cost=1800, status="Closed", start_date=today - timedelta(days=30), end_date=today - timedelta(days=28)),
            models.MaintenanceLog(vehicle_id=vehicles[0].id, type="Oil Change", description="Routine oil change and filter replacement", cost=120, status="Closed", start_date=today - timedelta(days=60), end_date=today - timedelta(days=59)),
        ]
        db.add_all(maintenance)
        db.flush()

        # Fuel logs
        fuel_logs = [
            models.FuelLog(vehicle_id=vehicles[0].id, litres=45, cost=90, date=today - timedelta(days=5), odometer=45155),
            models.FuelLog(vehicle_id=vehicles[1].id, litres=120, cost=240, date=today - timedelta(days=3), odometer=120380),
            models.FuelLog(vehicle_id=vehicles[2].id, litres=55, cost=110, date=today - timedelta(days=1), odometer=68245),
            models.FuelLog(vehicle_id=vehicles[4].id, litres=30, cost=60, date=today - timedelta(days=7), odometer=22370),
            models.FuelLog(vehicle_id=vehicles[1].id, trip_id=trips[2].id, litres=85, cost=170, date=today - timedelta(days=10), odometer=120295),
        ]
        db.add_all(fuel_logs)
        db.flush()

        # Expenses
        expenses = [
            models.Expense(vehicle_id=vehicles[0].id, type="Toll", amount=25, date=today - timedelta(days=2), description="Highway toll charges - Route 66"),
            models.Expense(vehicle_id=vehicles[2].id, trip_id=trips[0].id, type="Toll", amount=40, date=today - timedelta(days=1), description="Bridge toll charges"),
            models.Expense(vehicle_id=vehicles[1].id, type="Insurance", amount=850, date=today - timedelta(days=15), description="Annual vehicle insurance premium"),
            models.Expense(vehicle_id=vehicles[4].id, type="Parking", amount=15, date=today - timedelta(days=3), description="Airport parking fee"),
        ]
        db.add_all(expenses)

        db.commit()
        print("✅ Database seeded successfully!")
        print("\nDemo accounts:")
        print("  fleet@transitops.com / password123 (Fleet Manager)")
        print("  driver@transitops.com / password123 (Driver)")
        print("  safety@transitops.com / password123 (Safety Officer)")
        print("  finance@transitops.com / password123 (Financial Analyst)")
    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
