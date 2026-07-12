import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
import models  # ensure all models are registered

from routers import auth_router, dashboard, vehicles, drivers, trips, maintenance, fuel_logs, expenses, reports

# Create all DB tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TransitOps API",
    description="Smart Transport Operations Platform",
    version="1.0.0",
    root_path="/api",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["health"])
def healthz():
    return {"status": "ok"}


# Register all routers
app.include_router(auth_router.router)
app.include_router(dashboard.router)
app.include_router(vehicles.router)
app.include_router(drivers.router)
app.include_router(trips.router)
app.include_router(maintenance.router)
app.include_router(fuel_logs.router)
app.include_router(expenses.router)
app.include_router(reports.router)
