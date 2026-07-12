from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from transit_ops.models import get_db_engine, get_db_session, init_db
from transit_ops.config import DATABASE_URL, DEBUG
from transit_ops.routes import auth, vehicles, drivers, trips, maintenance, fuel, dashboard

# Initialize database
engine = get_db_engine(DATABASE_URL)
SessionLocal = get_db_session(engine)

# Create tables if they don't exist
init_db(engine)

# FastAPI app
app = FastAPI(title="TransitOps", debug=DEBUG)

# CORS middleware (allow frontend requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency: get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Register routes
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(vehicles.router, prefix="/api/vehicles", tags=["vehicles"])
app.include_router(drivers.router, prefix="/api/drivers", tags=["drivers"])
app.include_router(trips.router, prefix="/api/trips", tags=["trips"])
app.include_router(maintenance.router, prefix="/api/maintenance", tags=["maintenance"])
app.include_router(fuel.router, prefix="/api/fuel", tags=["fuel"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)