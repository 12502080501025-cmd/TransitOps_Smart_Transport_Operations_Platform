/**
 * TransitOps Backend API
 * ------------------------------------------------------------------
 * Node.js + Express REST API implementing the TransitOps business
 * rules described in the spec: RBAC auth, vehicle/driver registries,
 * trip lifecycle with validation, maintenance workflow, fuel/expense
 * tracking, and reports.
 *
 * Storage: a local JSON file (db.json) via a tiny file-backed store —
 * zero external database required to run this. Swap `store.js` for a
 * real Postgres/Mongo layer in production (see schema.sql for a
 * relational schema you can migrate to).
 *
 * Run:
 *   cd backend
 *   npm install
 *   npm start          # http://localhost:4000
 * ------------------------------------------------------------------
 */
const express = require('express');
const cors = require('cors');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const { db, save } = require('./store');

const app = express();
app.use(cors());
app.use(express.json());

const JWT_SECRET = process.env.JWT_SECRET || 'transitops-dev-secret-change-me';
const TODAY = () => new Date();

/* -------------------------------------------------------------- */
/* AUTH                                                             */
/* -------------------------------------------------------------- */
// Seeded demo users (in production, store hashed passwords in DB)
const USERS = [
  { id: 'U1', email: 'fleet@transitops.io',  passwordHash: bcrypt.hashSync('password', 8), name: 'Fleet Manager', role: 'fleet_manager' },
  { id: 'U2', email: 'driver@transitops.io', passwordHash: bcrypt.hashSync('password', 8), name: 'Driver',        role: 'driver' },
  { id: 'U3', email: 'safety@transitops.io', passwordHash: bcrypt.hashSync('password', 8), name: 'Safety Officer',role: 'safety_officer' },
  { id: 'U4', email: 'finance@transitops.io',passwordHash: bcrypt.hashSync('password', 8), name: 'Financial Analyst', role: 'finance' },
];

const ROLE_PERMISSIONS = {
  fleet_manager:  ['dashboard', 'vehicles', 'drivers', 'trips', 'maintenance', 'fuel', 'reports'],
  driver:         ['dashboard', 'trips'],
  safety_officer: ['dashboard', 'drivers', 'reports'],
  finance:        ['dashboard', 'fuel', 'reports'],
};

app.post('/api/auth/login', (req, res) => {
  const { email, password } = req.body;
  const user = USERS.find(u => u.email === email);
  if (!user || !bcrypt.compareSync(password, user.passwordHash)) {
    return res.status(401).json({ error: 'Invalid email or password.' });
  }
  const token = jwt.sign({ sub: user.id, role: user.role, name: user.name }, JWT_SECRET, { expiresIn: '8h' });
  res.json({ token, user: { id: user.id, name: user.name, role: user.role, permissions: ROLE_PERMISSIONS[user.role] } });
});

function auth(req, res, next) {
  const header = req.headers.authorization || '';
  const token = header.startsWith('Bearer ') ? header.slice(7) : null;
  if (!token) return res.status(401).json({ error: 'Missing bearer token.' });
  try {
    req.user = jwt.verify(token, JWT_SECRET);
    next();
  } catch {
    return res.status(401).json({ error: 'Invalid or expired token.' });
  }
}
function requirePermission(section) {
  return (req, res, next) => {
    const allowed = ROLE_PERMISSIONS[req.user.role] || [];
    if (!allowed.includes(section)) return res.status(403).json({ error: `Role "${req.user.role}" cannot access "${section}".` });
    next();
  };
}

app.use('/api', auth); // everything below requires a valid token

/* -------------------------------------------------------------- */
/* VEHICLES                                                         */
/* -------------------------------------------------------------- */
app.get('/api/vehicles', requirePermission('vehicles'), (req, res) => {
  res.json(db.vehicles);
});

app.post('/api/vehicles', requirePermission('vehicles'), (req, res) => {
  const { reg, name, type, capacity, odometer = 0, cost = 0, region, status = 'Available' } = req.body;
  if (!reg || !name || !capacity) return res.status(400).json({ error: 'reg, name and capacity are required.' });
  if (db.vehicles.some(v => v.reg.toLowerCase() === reg.toLowerCase())) {
    return res.status(409).json({ error: 'Registration number must be unique.' });
  }
  const vehicle = { id: 'V' + (++db.seq), reg, name, type, capacity, odometer, cost, region, status };
  db.vehicles.push(vehicle);
  save();
  res.status(201).json(vehicle);
});

app.put('/api/vehicles/:id', requirePermission('vehicles'), (req, res) => {
  const vehicle = db.vehicles.find(v => v.id === req.params.id);
  if (!vehicle) return res.status(404).json({ error: 'Vehicle not found.' });
  if (req.body.reg && db.vehicles.some(v => v.reg.toLowerCase() === req.body.reg.toLowerCase() && v.id !== vehicle.id)) {
    return res.status(409).json({ error: 'Registration number must be unique.' });
  }
  Object.assign(vehicle, req.body);
  save();
  res.json(vehicle);
});

app.delete('/api/vehicles/:id', requirePermission('vehicles'), (req, res) => {
  const blocking = db.trips.find(t => t.vehicleId === req.params.id && t.status === 'Dispatched');
  if (blocking) return res.status(409).json({ error: 'Vehicle is on a dispatched trip and cannot be removed.' });
  db.vehicles = db.vehicles.filter(v => v.id !== req.params.id);
  save();
  res.status(204).end();
});

/* -------------------------------------------------------------- */
/* DRIVERS                                                          */
/* -------------------------------------------------------------- */
app.get('/api/drivers', requirePermission('drivers'), (req, res) => res.json(db.drivers));

app.post('/api/drivers', requirePermission('drivers'), (req, res) => {
  const { name, license, category, expiry, contact, score = 90, status = 'Available' } = req.body;
  if (!name || !license || !expiry) return res.status(400).json({ error: 'name, license and expiry are required.' });
  const driver = { id: 'D' + (++db.seq), name, license, category, expiry, contact, score, status };
  db.drivers.push(driver);
  save();
  res.status(201).json(driver);
});

app.put('/api/drivers/:id', requirePermission('drivers'), (req, res) => {
  const driver = db.drivers.find(d => d.id === req.params.id);
  if (!driver) return res.status(404).json({ error: 'Driver not found.' });
  Object.assign(driver, req.body);
  save();
  res.json(driver);
});

app.delete('/api/drivers/:id', requirePermission('drivers'), (req, res) => {
  const blocking = db.trips.find(t => t.driverId === req.params.id && t.status === 'Dispatched');
  if (blocking) return res.status(409).json({ error: 'Driver is on a dispatched trip and cannot be removed.' });
  db.drivers = db.drivers.filter(d => d.id !== req.params.id);
  save();
  res.status(204).end();
});

/* -------------------------------------------------------------- */
/* TRIPS — lifecycle: Draft -> Dispatched -> Completed / Cancelled  */
/* -------------------------------------------------------------- */
app.get('/api/trips', requirePermission('trips'), (req, res) => res.json(db.trips));

app.post('/api/trips', requirePermission('trips'), (req, res) => {
  const { source, dest, vehicleId, driverId, cargo, distance, revenue = 0 } = req.body;
  if (!source || !dest || !vehicleId || !driverId || !cargo || !distance) {
    return res.status(400).json({ error: 'source, dest, vehicleId, driverId, cargo and distance are required.' });
  }
  const vehicle = db.vehicles.find(v => v.id === vehicleId);
  const driver = db.drivers.find(d => d.id === driverId);
  if (!vehicle || vehicle.status !== 'Available') return res.status(409).json({ error: 'Vehicle is not available for dispatch.' });
  if (!driver || driver.status !== 'Available') return res.status(409).json({ error: 'Driver is not available.' });
  if (new Date(driver.expiry) < TODAY() || driver.status === 'Suspended') return res.status(409).json({ error: 'Driver license expired or driver suspended.' });
  if (cargo > vehicle.capacity) return res.status(422).json({ error: `Cargo weight exceeds vehicle max load capacity (${vehicle.capacity} kg).` });

  const trip = { id: 'T' + (++db.seq), source, dest, vehicleId, driverId, cargo, distance, revenue, status: 'Draft', fuelUsed: 0, odometerEnd: null, created: new Date().toISOString().slice(0, 10) };
  db.trips.push(trip);
  save();
  res.status(201).json(trip);
});

app.post('/api/trips/:id/dispatch', requirePermission('trips'), (req, res) => {
  const trip = db.trips.find(t => t.id === req.params.id);
  if (!trip) return res.status(404).json({ error: 'Trip not found.' });
  const vehicle = db.vehicles.find(v => v.id === trip.vehicleId);
  const driver = db.drivers.find(d => d.id === trip.driverId);
  if (vehicle.status !== 'Available') return res.status(409).json({ error: 'Vehicle no longer available.' });
  if (driver.status !== 'Available' || new Date(driver.expiry) < TODAY()) return res.status(409).json({ error: 'Driver no longer available or license expired.' });
  trip.status = 'Dispatched'; vehicle.status = 'On Trip'; driver.status = 'On Trip';
  save();
  res.json(trip);
});

app.post('/api/trips/:id/complete', requirePermission('trips'), (req, res) => {
  const trip = db.trips.find(t => t.id === req.params.id);
  if (!trip) return res.status(404).json({ error: 'Trip not found.' });
  if (trip.status !== 'Dispatched') return res.status(409).json({ error: 'Only dispatched trips can be completed.' });
  const { fuelUsed = 0, finalOdometer } = req.body;
  const vehicle = db.vehicles.find(v => v.id === trip.vehicleId);
  const driver = db.drivers.find(d => d.id === trip.driverId);
  trip.fuelUsed = fuelUsed;
  trip.odometerEnd = finalOdometer ?? vehicle.odometer + trip.distance;
  vehicle.odometer = trip.odometerEnd;
  trip.status = 'Completed'; vehicle.status = 'Available'; driver.status = 'Available';
  if (fuelUsed > 0) {
    db.fuelLogs.push({ id: 'F' + (++db.seq), vehicleId: vehicle.id, liters: fuelUsed, cost: Math.round(fuelUsed * 111), date: new Date().toISOString().slice(0, 10) });
  }
  save();
  res.json(trip);
});

app.post('/api/trips/:id/cancel', requirePermission('trips'), (req, res) => {
  const trip = db.trips.find(t => t.id === req.params.id);
  if (!trip) return res.status(404).json({ error: 'Trip not found.' });
  if (trip.status === 'Dispatched') {
    db.vehicles.find(v => v.id === trip.vehicleId).status = 'Available';
    db.drivers.find(d => d.id === trip.driverId).status = 'Available';
  }
  trip.status = 'Cancelled';
  save();
  res.json(trip);
});

/* -------------------------------------------------------------- */
/* MAINTENANCE                                                      */
/* -------------------------------------------------------------- */
app.get('/api/maintenance', requirePermission('maintenance'), (req, res) => res.json(db.maintenance));

app.post('/api/maintenance', requirePermission('maintenance'), (req, res) => {
  const { vehicleId, type, desc, cost = 0 } = req.body;
  const vehicle = db.vehicles.find(v => v.id === vehicleId);
  if (!vehicle) return res.status(404).json({ error: 'Vehicle not found.' });
  if (vehicle.status === 'On Trip') return res.status(409).json({ error: 'Vehicle is on a trip and cannot enter maintenance.' });
  const record = { id: 'M' + (++db.seq), vehicleId, type, desc, cost, opened: new Date().toISOString().slice(0, 10), status: 'Open' };
  db.maintenance.push(record);
  vehicle.status = 'In Shop'; // business rule: opening maintenance -> vehicle In Shop
  save();
  res.status(201).json(record);
});

app.post('/api/maintenance/:id/close', requirePermission('maintenance'), (req, res) => {
  const record = db.maintenance.find(m => m.id === req.params.id);
  if (!record) return res.status(404).json({ error: 'Maintenance record not found.' });
  record.status = 'Closed';
  const vehicle = db.vehicles.find(v => v.id === record.vehicleId);
  if (vehicle.status !== 'Retired') vehicle.status = 'Available'; // restored unless retired
  save();
  res.json(record);
});

/* -------------------------------------------------------------- */
/* FUEL & EXPENSES                                                   */
/* -------------------------------------------------------------- */
app.get('/api/fuel-logs', requirePermission('fuel'), (req, res) => res.json(db.fuelLogs));
app.post('/api/fuel-logs', requirePermission('fuel'), (req, res) => {
  const { vehicleId, liters, cost, date } = req.body;
  if (!vehicleId || !liters || !cost || !date) return res.status(400).json({ error: 'vehicleId, liters, cost and date are required.' });
  const log = { id: 'F' + (++db.seq), vehicleId, liters, cost, date };
  db.fuelLogs.push(log); save();
  res.status(201).json(log);
});

app.get('/api/expenses', requirePermission('fuel'), (req, res) => res.json(db.expenses));
app.post('/api/expenses', requirePermission('fuel'), (req, res) => {
  const { vehicleId, type, amount, date, note } = req.body;
  if (!vehicleId || !type || !amount || !date) return res.status(400).json({ error: 'vehicleId, type, amount and date are required.' });
  const exp = { id: 'E' + (++db.seq), vehicleId, type, amount, date, note };
  db.expenses.push(exp); save();
  res.status(201).json(exp);
});

/* -------------------------------------------------------------- */
/* DASHBOARD & REPORTS                                              */
/* -------------------------------------------------------------- */
app.get('/api/dashboard/kpis', requirePermission('dashboard'), (req, res) => {
  const { type, status, region } = req.query;
  const veh = db.vehicles.filter(v => (!type || v.type === type) && (!status || v.status === status) && (!region || v.region === region));
  const onTrip = veh.filter(v => v.status === 'On Trip').length;
  res.json({
    activeVehicles: veh.filter(v => v.status !== 'Retired').length,
    availableVehicles: veh.filter(v => v.status === 'Available').length,
    inMaintenance: veh.filter(v => v.status === 'In Shop').length,
    activeTrips: db.trips.filter(t => t.status === 'Dispatched').length,
    pendingTrips: db.trips.filter(t => t.status === 'Draft').length,
    driversOnDuty: db.drivers.filter(d => d.status === 'On Trip' || d.status === 'Available').length,
    fleetUtilizationPct: veh.length ? Math.round((onTrip / veh.length) * 100) : 0,
  });
});

app.get('/api/reports/vehicles', requirePermission('reports'), (req, res) => {
  const rows = db.vehicles.map(v => {
    const fuelCost = db.fuelLogs.filter(f => f.vehicleId === v.id).reduce((s, f) => s + f.cost, 0);
    const fuelLiters = db.fuelLogs.filter(f => f.vehicleId === v.id).reduce((s, f) => s + f.liters, 0);
    const maintCost = db.maintenance.filter(m => m.vehicleId === v.id).reduce((s, m) => s + m.cost, 0);
    const completedTrips = db.trips.filter(t => t.vehicleId === v.id && t.status === 'Completed');
    const revenue = completedTrips.reduce((s, t) => s + t.revenue, 0);
    const distance = completedTrips.reduce((s, t) => s + t.distance, 0);
    const totalCost = fuelCost + maintCost;
    return {
      vehicleId: v.id, name: v.name, reg: v.reg,
      revenue, fuelCost, maintCost, totalCost,
      acquisitionCost: v.cost,
      roi: v.cost ? (revenue - totalCost) / v.cost : 0,
      fuelEfficiencyKmPerL: fuelLiters ? distance / fuelLiters : 0,
    };
  });
  res.json(rows);
});

app.listen(process.env.PORT || 4000, () => {
  console.log(`TransitOps API listening on port ${process.env.PORT || 4000}`);
});