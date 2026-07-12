# TransitOps — Smart Transport Operations Platform

A full-stack fleet operations platform: vehicle & driver registries, trip dispatch
with business-rule validation, maintenance workflow, fuel/expense tracking, and
a KPI dashboard with reports.

## What's in this package

```
transitops/
├── preview.html          ← Single-file demo (open directly in any browser — this is the live preview)
├── frontend/
│   ├── index.html         ← Same UI, split into standalone files
│   ├── style.css
│   └── app.js
├── backend/
│   ├── server.js           ← Express REST API implementing all business rules
│   ├── store.js             ← Zero-setup JSON file "database" (swap for Postgres/Mongo later)
│   ├── schema.sql            ← Relational schema reference for a production DB
│   └── package.json
└── README.md
```

> **Note:** all charts (fleet status, trip lifecycle, operational cost, fuel
> efficiency) are hand-built inline SVG — no charting library or external
> script is loaded, so the dashboard and reports render correctly even with
> no internet access or in a locked-down preview sandbox.

## 1. Try it instantly

Open **`preview.html`** (or `frontend/index.html`) directly in a browser — no
install needed. It runs entirely client-side with an in-memory mock data layer
that behaves like the real API (same shapes, same validation rules), seeded
with sample vehicles, drivers and trips so you can explore every screen
immediately.

Demo login: any email + password, choose a role (Fleet Manager, Driver, Safety
Officer, Financial Analyst) to preview RBAC — the sidebar changes per role.

## 2. Run the real backend

```bash
cd backend
npm install
npm start
# API live at http://localhost:4000
```

Seeded login users (email / password):

| Role              | Email                     | Password |
|-------------------|----------------------------|----------|
| Fleet Manager     | fleet@transitops.io        | password |
| Driver            | driver@transitops.io       | password |
| Safety Officer    | safety@transitops.io       | password |
| Financial Analyst | finance@transitops.io      | password |

Auth: `POST /api/auth/login` → returns a JWT. Send it as
`Authorization: Bearer <token>` on every other `/api/*` call.

### Key endpoints

| Method | Endpoint | Notes |
|---|---|---|
| POST | `/api/auth/login` | email + password → JWT |
| GET/POST/PUT/DELETE | `/api/vehicles` | unique reg number enforced |
| GET/POST/PUT/DELETE | `/api/drivers` | license/status checks |
| GET/POST | `/api/trips` | validates capacity, availability, license |
| POST | `/api/trips/:id/dispatch` | vehicle+driver → On Trip |
| POST | `/api/trips/:id/complete` | vehicle+driver → Available, logs fuel |
| POST | `/api/trips/:id/cancel` | restores Available if was Dispatched |
| GET/POST | `/api/maintenance` | opening sets vehicle → In Shop |
| POST | `/api/maintenance/:id/close` | restores vehicle (unless Retired) |
| GET/POST | `/api/fuel-logs`, `/api/expenses` | |
| GET | `/api/dashboard/kpis` | supports `?type=&status=&region=` filters |
| GET | `/api/reports/vehicles` | fuel efficiency, cost, ROI per vehicle |

### Connecting frontend/app.js to the real API

`frontend/app.js` currently ships with the mock in-memory layer (`DB` /
`api` objects at the top of the file) so the demo works with zero setup.
To go live: replace those two objects with `fetch()` calls to the endpoints
above (attach the JWT from login), keeping the rest of the file — all
rendering, forms, and business-rule checks in the UI — unchanged, since it
already expects the same data shapes.

## 3. Business rules implemented

- Registration numbers are unique across vehicles.
- Retired / In Shop vehicles never appear in the trip dispatch pool.
- Drivers with expired licenses or Suspended status can't be assigned.
- A vehicle/driver already On Trip can't be double-booked.
- Cargo weight is validated against the vehicle's max load capacity.
- Dispatch → vehicle & driver become On Trip.
- Complete → vehicle & driver return to Available; odometer & fuel logged.
- Cancel (from Dispatched) → vehicle & driver restored to Available.
- Opening a maintenance record → vehicle becomes In Shop automatically.
- Closing maintenance → vehicle restored to Available (unless Retired).
- Reports compute Fuel Efficiency, Fleet Utilization, Operational Cost, and
  ROI = (Revenue − (Maintenance + Fuel)) / Acquisition Cost.

## 4. Roles

- **Fleet Manager** — full access: vehicles, drivers, trips, maintenance, reports.
- **Driver** — dashboard + trip creation/monitoring.
- **Safety Officer** — dashboard + driver compliance + reports.
- **Financial Analyst** — dashboard + fuel/expenses + reports.

## 5. Migrating to a real database

`backend/schema.sql` has a full PostgreSQL schema matching every entity in
`store.js`. Swap `store.js`'s file-read/write for a `pg` (or your ORM of
choice) client — `server.js` only imports `{ db, save }` from that one file,
so no other backend code needs to change.