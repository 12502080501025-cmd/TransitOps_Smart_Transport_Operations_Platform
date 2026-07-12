-- ============================================================
-- TransitOps — Relational schema reference (PostgreSQL)
-- The bundled server.js uses a JSON file store for zero-setup demo
-- purposes. Migrate to this schema for a production deployment.
-- ============================================================

CREATE TYPE user_role AS ENUM ('fleet_manager', 'driver', 'safety_officer', 'finance');
CREATE TYPE vehicle_status AS ENUM ('Available', 'On Trip', 'In Shop', 'Retired');
CREATE TYPE driver_status AS ENUM ('Available', 'On Trip', 'Off Duty', 'Suspended');
CREATE TYPE trip_status AS ENUM ('Draft', 'Dispatched', 'Completed', 'Cancelled');
CREATE TYPE maintenance_status AS ENUM ('Open', 'Closed');

CREATE TABLE users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email         TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  name          TEXT NOT NULL,
  role          user_role NOT NULL,
  created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE vehicles (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reg_number        TEXT UNIQUE NOT NULL,
  name              TEXT NOT NULL,
  type              TEXT NOT NULL,
  max_load_capacity NUMERIC NOT NULL CHECK (max_load_capacity > 0),
  odometer          NUMERIC NOT NULL DEFAULT 0,
  acquisition_cost  NUMERIC NOT NULL DEFAULT 0,
  region            TEXT,
  status            vehicle_status NOT NULL DEFAULT 'Available',
  created_at        TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE drivers (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name            TEXT NOT NULL,
  license_number  TEXT UNIQUE NOT NULL,
  license_category TEXT,
  license_expiry  DATE NOT NULL,
  contact_number  TEXT,
  safety_score    INTEGER CHECK (safety_score BETWEEN 0 AND 100) DEFAULT 90,
  status          driver_status NOT NULL DEFAULT 'Available',
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE trips (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source          TEXT NOT NULL,
  destination     TEXT NOT NULL,
  vehicle_id      UUID NOT NULL REFERENCES vehicles(id),
  driver_id       UUID NOT NULL REFERENCES drivers(id),
  cargo_weight    NUMERIC NOT NULL,
  planned_distance NUMERIC NOT NULL,
  revenue         NUMERIC DEFAULT 0,
  status          trip_status NOT NULL DEFAULT 'Draft',
  fuel_used       NUMERIC DEFAULT 0,
  odometer_end    NUMERIC,
  created_at      TIMESTAMPTZ DEFAULT now(),
  -- business rule: cargo weight must not exceed vehicle capacity (enforced in app layer,
  -- since it requires a cross-table lookup; kept here as a documented invariant)
  CONSTRAINT chk_cargo_positive CHECK (cargo_weight > 0)
);

CREATE TABLE maintenance_logs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vehicle_id  UUID NOT NULL REFERENCES vehicles(id),
  type        TEXT NOT NULL,
  description TEXT,
  cost        NUMERIC DEFAULT 0,
  opened_at   DATE NOT NULL DEFAULT CURRENT_DATE,
  closed_at   DATE,
  status      maintenance_status NOT NULL DEFAULT 'Open'
);

CREATE TABLE fuel_logs (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vehicle_id UUID NOT NULL REFERENCES vehicles(id),
  liters     NUMERIC NOT NULL CHECK (liters > 0),
  cost       NUMERIC NOT NULL CHECK (cost >= 0),
  log_date   DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE expenses (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vehicle_id UUID NOT NULL REFERENCES vehicles(id),
  type       TEXT NOT NULL,
  amount     NUMERIC NOT NULL CHECK (amount >= 0),
  exp_date   DATE NOT NULL DEFAULT CURRENT_DATE,
  note       TEXT
);

-- Helpful indexes
CREATE INDEX idx_trips_vehicle ON trips(vehicle_id);
CREATE INDEX idx_trips_driver ON trips(driver_id);
CREATE INDEX idx_fuel_vehicle ON fuel_logs(vehicle_id);
CREATE INDEX idx_expenses_vehicle ON expenses(vehicle_id);
CREATE INDEX idx_maintenance_vehicle ON maintenance_logs(vehicle_id);