/**
 * Minimal file-backed data store (db.json).
 * Swap this module for a real database client (pg, mongoose, etc.)
 * in production — every other file only talks to `db` and `save()`,
 * so the rest of the API is unaffected by the swap.
 */
const fs = require('fs');
const path = require('path');
const FILE = path.join(__dirname, 'db.json');

const SEED = {
  seq: 100,
  vehicles: [
    { id: 'V1', reg: 'GJ-01-AB-4521', name: 'Van-05', type: 'Van', capacity: 500, odometer: 18420, cost: 1450000, status: 'Available', region: 'Ahmedabad' },
    { id: 'V2', reg: 'GJ-01-CD-7788', name: 'Truck-11', type: 'Truck', capacity: 3000, odometer: 52110, cost: 3200000, status: 'In Shop', region: 'Surat' },
    { id: 'V3', reg: 'GJ-05-EF-1190', name: 'Mini-Van-02', type: 'Van', capacity: 350, odometer: 9210, cost: 980000, status: 'On Trip', region: 'Vadodara' },
    { id: 'V4', reg: 'GJ-01-GH-3345', name: 'Truck-04', type: 'Truck', capacity: 5000, odometer: 71300, cost: 4100000, status: 'Available', region: 'Ahmedabad' },
  ],
  drivers: [
    { id: 'D1', name: 'Alex Menon', license: 'DL-KA-2019-0451', category: 'LMV', expiry: '2027-03-14', contact: '+91 98200 11223', score: 92, status: 'Available' },
    { id: 'D2', name: 'Priya Nair', license: 'DL-GJ-2020-1187', category: 'HMV', expiry: '2026-08-02', contact: '+91 98450 33112', score: 88, status: 'On Trip' },
    { id: 'D3', name: 'Rakesh Bhatt', license: 'DL-GJ-2017-0932', category: 'HMV', expiry: '2026-01-30', contact: '+91 97120 88765', score: 64, status: 'Suspended' },
  ],
  trips: [],
  maintenance: [
    { id: 'M1', vehicleId: 'V2', type: 'Brake Service', desc: 'Full brake pad replacement + fluid change', cost: 12500, opened: '2026-07-09', status: 'Open' },
  ],
  fuelLogs: [
    { id: 'F1', vehicleId: 'V1', liters: 32, cost: 3520, date: '2026-06-19' },
  ],
  expenses: [
    { id: 'E1', vehicleId: 'V3', type: 'Toll', amount: 640, date: '2026-07-08', note: 'Ahmedabad–Surat expressway' },
  ],
};

function load() {
  if (!fs.existsSync(FILE)) {
    fs.writeFileSync(FILE, JSON.stringify(SEED, null, 2));
    return JSON.parse(JSON.stringify(SEED));
  }
  return JSON.parse(fs.readFileSync(FILE, 'utf-8'));
}

const db = load();

function save() {
  fs.writeFileSync(FILE, JSON.stringify(db, null, 2));
}

module.exports = { db, save };