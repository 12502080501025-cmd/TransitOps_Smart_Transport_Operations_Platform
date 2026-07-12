/* ==========================================================================
   TransitOps — Frontend Demo
   NOTE: `API` below simulates a REST backend (async, in-memory "DB").
   In production this layer is replaced by real fetch() calls to /backend
   (see server.js / schema.sql in the accompanying project export).
   ========================================================================== */

/* ---------------- MOCK BACKEND / DB LAYER ---------------- */
const DB = {
  vehicles: [
    {id:'V1', reg:'GJ-01-AB-4521', name:'Van-05', type:'Van', capacity:500, odometer:18420, cost:1450000, status:'Available', region:'Ahmedabad'},
    {id:'V2', reg:'GJ-01-CD-7788', name:'Truck-11', type:'Truck', capacity:3000, odometer:52110, cost:3200000, status:'In Shop', region:'Surat'},
    {id:'V3', reg:'GJ-05-EF-1190', name:'Mini-Van-02', type:'Van', capacity:350, odometer:9210, cost:980000, status:'On Trip', region:'Vadodara'},
    {id:'V4', reg:'GJ-01-GH-3345', name:'Truck-04', type:'Truck', capacity:5000, odometer:71300, cost:4100000, status:'Available', region:'Ahmedabad'},
    {id:'V5', reg:'GJ-03-IJ-9082', name:'Pickup-09', type:'Pickup', capacity:800, odometer:31200, cost:1200000, status:'Retired', region:'Rajkot'},
    {id:'V6', reg:'GJ-01-KL-5567', name:'Van-12', type:'Van', capacity:600, odometer:14040, cost:1550000, status:'Available', region:'Surat'},
  ],
  drivers: [
    {id:'D1', name:'Alex Menon', license:'DL-KA-2019-0451', category:'LMV', expiry:'2027-03-14', contact:'+91 98200 11223', score:92, status:'Available'},
    {id:'D2', name:'Priya Nair', license:'DL-GJ-2020-1187', category:'HMV', expiry:'2026-08-02', contact:'+91 98450 33112', score:88, status:'On Trip'},
    {id:'D3', name:'Rakesh Bhatt', license:'DL-GJ-2017-0932', category:'HMV', expiry:'2026-01-30', contact:'+91 97120 88765', score:64, status:'Suspended'},
    {id:'D4', name:'Farhan Sheikh', license:'DL-MH-2021-2245', category:'LMV', expiry:'2025-11-01', contact:'+91 90210 44551', score:79, status:'Available'},
    {id:'D5', name:'Sunita Rao', license:'DL-GJ-2018-0673', category:'HMV', expiry:'2027-06-20', contact:'+91 91234 65432', score:95, status:'Off Duty'},
  ],
  trips: [
    {id:'T1', source:'Ahmedabad', dest:'Surat', vehicleId:'V3', driverId:'D2', cargo:280, distance:265, revenue:18000, status:'Dispatched', fuelUsed:0, odometerEnd:null, created:'2026-07-08'},
    {id:'T2', source:'Ahmedabad', dest:'Vadodara', vehicleId:'V1', driverId:'D1', cargo:410, distance:110, revenue:9500, status:'Completed', fuelUsed:14, odometerEnd:18420, created:'2026-07-05'},
    {id:'T3', source:'Rajkot', dest:'Ahmedabad', vehicleId:'V4', driverId:'D5', cargo:1200, distance:220, revenue:21000, status:'Draft', fuelUsed:0, odometerEnd:null, created:'2026-07-10'},
  ],
  maintenance: [
    {id:'M1', vehicleId:'V2', type:'Brake Service', desc:'Full brake pad replacement + fluid change', cost:12500, opened:'2026-07-09', status:'Open'},
    {id:'M2', vehicleId:'V1', type:'Oil Change', desc:'Routine engine oil & filter change', cost:2200, opened:'2026-06-20', status:'Closed'},
  ],
  fuelLogs: [
    {id:'F1', vehicleId:'V1', liters:32, cost:3520, date:'2026-06-19'},
    {id:'F2', vehicleId:'V3', liters:21, cost:2331, date:'2026-07-08'},
    {id:'F3', vehicleId:'V4', liters:58, cost:6438, date:'2026-07-02'},
  ],
  expenses: [
    {id:'E1', vehicleId:'V3', type:'Toll', amount:640, date:'2026-07-08', note:'Ahmedabad–Surat expressway'},
    {id:'E2', vehicleId:'V4', type:'Parking', amount:150, date:'2026-07-02', note:'Rajkot yard'},
  ],
  _seq:100,
  nextId(prefix){ this._seq++; return prefix+this._seq; }
};

const ROLES = {
  fleet_manager: {label:'Fleet Manager', nav:['dashboard','vehicles','drivers','trips','maintenance','fuel','reports']},
  driver:        {label:'Driver',         nav:['dashboard','trips']},
  safety_officer:{label:'Safety Officer', nav:['dashboard','drivers','reports']},
  finance:       {label:'Financial Analyst', nav:['dashboard','fuel','reports']},
};
const NAV_META = {
  dashboard:{label:'Dashboard', ic:'▤'},
  vehicles:{label:'Vehicles', ic:'🚚'},
  drivers:{label:'Drivers', ic:'🪪'},
  trips:{label:'Trips', ic:'⇢'},
  maintenance:{label:'Maintenance', ic:'🔧'},
  fuel:{label:'Fuel & Expenses', ic:'⛽'},
  reports:{label:'Reports', ic:'📊'},
};

/* Simulated async API — mirrors what a real REST backend would expose.
   Swap the body of each method for a fetch() call to go live. */
const api = {
  delay: (v)=> new Promise(res=>setTimeout(()=>res(v), 120)),
  listVehicles(){ return this.delay([...DB.vehicles]); },
  listDrivers(){ return this.delay([...DB.drivers]); },
  listTrips(){ return this.delay([...DB.trips]); },
  listMaintenance(){ return this.delay([...DB.maintenance]); },
  listFuel(){ return this.delay([...DB.fuelLogs]); },
  listExpenses(){ return this.delay([...DB.expenses]); },
};

/* ---------------- APP / AUTH / NAV ---------------- */
const App = {
  currentUser:null,
  selectedRole:'fleet_manager',
  theme:'dark',
  init(){
    const grid = document.getElementById('roleGrid');
    grid.innerHTML = Object.entries(ROLES).map(([k,r])=>
      `<button class="role-pick ${k==='fleet_manager'?'active':''}" data-role="${k}" onclick="App.pickRole('${k}')">
        <b>${r.label}</b>${k.replace('_',' ')}
      </button>`).join('');
  },
  pickRole(k){
    this.selectedRole = k;
    document.querySelectorAll('.role-pick').forEach(el=>el.classList.toggle('active', el.dataset.role===k));
  },
  login(){
    const email = document.getElementById('loginEmail').value.trim();
    const pass = document.getElementById('loginPass').value.trim();
    const err = document.getElementById('loginErr');
    if(!email || !pass){ err.classList.add('active'); return; }
    err.classList.remove('active');
    this.currentUser = {email, role:this.selectedRole, name: email.split('@')[0].replace(/[._]/g,' ').replace(/\b\w/g,c=>c.toUpperCase())};
    document.getElementById('loginScreen').style.display='none';
    document.getElementById('app').classList.add('active');
    document.getElementById('userName').textContent = this.currentUser.name;
    document.getElementById('userRole').textContent = ROLES[this.selectedRole].label;
    document.getElementById('userAvatar').textContent = this.currentUser.name.charAt(0).toUpperCase();
    Nav.build();
    Nav.go(ROLES[this.selectedRole].nav[0]);
    Toast.show(`Signed in as ${ROLES[this.selectedRole].label}`);
  },
  logout(){
    this.currentUser = null;
    document.getElementById('app').classList.remove('active');
    document.getElementById('loginScreen').style.display='flex';
  },
  toggleTheme(){
    this.theme = this.theme==='dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', this.theme);
    document.getElementById('themeBtn').textContent = this.theme==='dark' ? '🌙' : '☀️';
    Dash.renderCharts(); Reports.renderCharts();
  }
};

const Nav = {
  build(){
    const role = ROLES[App.selectedRole];
    const c = document.getElementById('navContainer');
    c.innerHTML = `<div class="nav-group"><div class="nav-label">Operations</div>` +
      role.nav.map(k=>`<div class="nav-item" data-key="${k}" onclick="Nav.go('${k}')"><span class="ic">${NAV_META[k].ic}</span>${NAV_META[k].label}</div>`).join('') +
      `</div>`;
  },
  go(key){
    document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
    document.getElementById('sec-'+key).classList.add('active');
    document.querySelectorAll('.nav-item').forEach(n=>n.classList.toggle('active', n.dataset.key===key));
    const renderers = {dashboard:Dash.render, vehicles:Vehicles.render, drivers:Drivers.render, trips:Trips.render, maintenance:Maint.render, fuel:Fuel.render, reports:Reports.render};
    renderers[key] && renderers[key]();
  }
};

/* ---------------- HELPERS ---------------- */
const fmt = n => new Intl.NumberFormat('en-IN').format(Math.round(n));
const fmtMoney = n => '₹'+fmt(n);
const vName = id => { const v = DB.vehicles.find(v=>v.id===id); return v? v.name : '—'; };
const vReg = id => { const v = DB.vehicles.find(v=>v.id===id); return v? v.reg : '—'; };
const dName = id => { const d = DB.drivers.find(d=>d.id===id); return d? d.name : '—'; };
const isExpired = dateStr => new Date(dateStr) < new Date('2026-07-12');
const statusBadge = (status, map) => `<span class="badge ${map[status]||'b-gray'}">${status}</span>`;

const Toast = {
  show(msg, isErr){
    const t = document.getElementById('toast');
    t.textContent = (isErr?'⚠ ':'✓ ') + msg;
    t.classList.toggle('err', !!isErr);
    t.classList.add('show');
    clearTimeout(this._to);
    this._to = setTimeout(()=>t.classList.remove('show'), 2600);
  }
};
const Modal = {
  open(html){ document.getElementById('modalHost').innerHTML = html; document.getElementById('modalBackdrop').classList.add('active'); },
  close(){ document.getElementById('modalBackdrop').classList.remove('active'); }
};

/* ---------------- CHARTS (pure inline SVG, zero external deps) ---------------- */
const Charts = {
  esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;'); },

  donut(labels, values, colors){
    const total = values.reduce((a,b)=>a+b,0);
    const r = 62, cx = 90, cy = 90, sw = 26, circ = 2*Math.PI*r;
    let offset = 0;
    const segs = labels.map((lab,i)=>{
      const val = values[i];
      if(total===0 || val===0) return '';
      const len = (val/total)*circ;
      const dash = `${len} ${circ-len}`;
      const rot = (offset/circ)*360 - 90;
      offset += len;
      return `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${colors[i]}" stroke-width="${sw}"
        stroke-dasharray="${dash}" transform="rotate(${rot} ${cx} ${cy})"><title>${this.esc(lab)}: ${val}</title></circle>`;
    }).join('');
    const legend = labels.map((lab,i)=>`
      <div style="display:flex;align-items:center;gap:6px;font-size:11.5px;color:var(--text-muted)">
        <span style="width:9px;height:9px;border-radius:2px;background:${colors[i]};display:inline-block;flex-shrink:0"></span>
        ${this.esc(lab)} <b style="color:var(--text);margin-left:2px">${values[i]}</b>
      </div>`).join('');
    return `
      <div style="display:flex; align-items:center; gap:22px; height:100%">
        <svg viewBox="0 0 180 180" style="width:150px;height:150px;flex-shrink:0">
          ${total===0 ? `<circle cx="90" cy="90" r="62" fill="none" stroke="var(--border)" stroke-width="26"/>` : segs}
          <text x="90" y="86" text-anchor="middle" font-family="Space Grotesk" font-weight="700" font-size="24" fill="var(--text)">${total}</text>
          <text x="90" y="104" text-anchor="middle" font-family="Inter" font-size="10.5" fill="var(--text-faint)">vehicles</text>
        </svg>
        <div style="display:flex; flex-direction:column; gap:10px">${legend}</div>
      </div>`;
  },

  bar(labels, values, color){
    const max = Math.max(1, ...values);
    const W = 460, H = 190, padB = 26, padT = 18, barGap = 18;
    const barW = (W - barGap*(labels.length+1)) / labels.length;
    const bars = labels.map((lab,i)=>{
      const val = values[i];
      const h = max ? (val/max) * (H-padT-padB) : 0;
      const x = barGap + i*(barW+barGap);
      const y = H - padB - h;
      return `
        <rect x="${x}" y="${y}" width="${barW}" height="${h}" rx="6" fill="${color}"><title>${this.esc(lab)}: ${val}</title></rect>
        <text x="${x+barW/2}" y="${y-8}" text-anchor="middle" font-family="Space Grotesk" font-weight="700" font-size="13" fill="var(--text)">${val}</text>
        <text x="${x+barW/2}" y="${H-8}" text-anchor="middle" font-family="Inter" font-size="10.5" fill="var(--text-faint)">${this.esc(lab)}</text>`;
    }).join('');
    return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;height:100%">
      <line x1="0" y1="${H-padB}" x2="${W}" y2="${H-padB}" stroke="var(--border-soft)" stroke-width="1"/>
      ${bars}
    </svg>`;
  },

  stackedBar(labels, series){
    const totals = labels.map((_,i)=> series.reduce((s,ser)=>s+ser.values[i],0));
    const max = Math.max(1, ...totals);
    const W = 460, H = 190, padB = 26, padT = 14, barGap = 20;
    const barW = (W - barGap*(labels.length+1)) / labels.length;
    const bars = labels.map((lab,i)=>{
      const x = barGap + i*(barW+barGap);
      let yCursor = H - padB;
      const rects = series.map(ser=>{
        const val = ser.values[i];
        const h = max ? (val/max) * (H-padT-padB) : 0;
        yCursor -= h;
        return `<rect x="${x}" y="${yCursor}" width="${barW}" height="${h}" fill="${ser.color}"><title>${this.esc(ser.label)}: ${this.esc(lab)} — ${fmtMoney(val)}</title></rect>`;
      }).join('');
      return rects + `<text x="${x+barW/2}" y="${H-8}" text-anchor="middle" font-family="Inter" font-size="10" fill="var(--text-faint)">${this.esc(lab)}</text>`;
    }).join('');
    const legend = series.map(ser=>`
      <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:var(--text-muted)">
        <span style="width:9px;height:9px;border-radius:2px;background:${ser.color};display:inline-block"></span>${this.esc(ser.label)}
      </div>`).join('');
    return `
      <div style="height:calc(100% - 24px)">
        <svg viewBox="0 0 ${W} ${H}" style="width:100%;height:100%">
          <line x1="0" y1="${H-padB}" x2="${W}" y2="${H-padB}" stroke="var(--border-soft)" stroke-width="1"/>
          ${bars}
        </svg>
      </div>
      <div style="display:flex; gap:16px; justify-content:center; margin-top:4px">${legend}</div>`;
  },

  line(labels, values, color, fmtVal){
    fmtVal = fmtVal || (v=>v);
    const max = Math.max(1, ...values, 1);
    const W = 460, H = 190, padB = 26, padT = 22, padX = 26;
    const stepX = labels.length>1 ? (W - padX*2) / (labels.length-1) : 0;
    const pts = values.map((v,i)=>{
      const x = padX + i*stepX;
      const y = H - padB - (v/max)*(H-padT-padB);
      return [x,y];
    });
    const path = pts.map((p,i)=> (i===0?'M':'L')+p[0].toFixed(1)+','+p[1].toFixed(1)).join(' ');
    const area = path + ` L${pts[pts.length-1][0].toFixed(1)},${H-padB} L${pts[0][0].toFixed(1)},${H-padB} Z`;
    const dots = pts.map((p,i)=>`
      <circle cx="${p[0]}" cy="${p[1]}" r="4" fill="${color}"><title>${this.esc(labels[i])}: ${fmtVal(values[i])}</title></circle>
      <text x="${p[0]}" y="${p[1]-10}" text-anchor="middle" font-family="Space Grotesk" font-weight="700" font-size="11" fill="var(--text)">${fmtVal(values[i])}</text>
      <text x="${p[0]}" y="${H-8}" text-anchor="middle" font-family="Inter" font-size="10" fill="var(--text-faint)">${this.esc(labels[i])}</text>`).join('');
    return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;height:100%">
      <line x1="0" y1="${H-padB}" x2="${W}" y2="${H-padB}" stroke="var(--border-soft)" stroke-width="1"/>
      <path d="${area}" fill="${color}" opacity="0.12" stroke="none"/>
      <path d="${path}" fill="none" stroke="${color}" stroke-width="2.5"/>
      ${dots}
    </svg>`;
  }
};

/* ---------------- DASHBOARD ---------------- */
const Dash = {
  populateFilters(){
    const types = [...new Set(DB.vehicles.map(v=>v.type))];
    const regions = [...new Set(DB.vehicles.map(v=>v.region))];
    const statuses = ['Available','On Trip','In Shop','Retired'];
    const set = (id, arr) => { const el=document.getElementById(id); const cur=el.value;
      el.innerHTML = el.querySelector('option').outerHTML + arr.map(v=>`<option>${v}</option>`).join('');
      el.value = cur; };
    set('fltType', types); set('fltRegion', regions); set('fltStatus', statuses);
  },
  render(){
    this.populateFilters();
    const type = document.getElementById('fltType').value;
    const status = document.getElementById('fltStatus').value;
    const region = document.getElementById('fltRegion').value;
    const veh = DB.vehicles.filter(v => (!type||v.type===type) && (!status||v.status===status) && (!region||v.region===region));

    const active = veh.filter(v=>v.status!=='Retired').length;
    const available = veh.filter(v=>v.status==='Available').length;
    const inShop = veh.filter(v=>v.status==='In Shop').length;
    const onTrip = veh.filter(v=>v.status==='On Trip').length;
    const activeTrips = DB.trips.filter(t=>t.status==='Dispatched').length;
    const pendingTrips = DB.trips.filter(t=>t.status==='Draft').length;
    const driversOnDuty = DB.drivers.filter(d=>d.status==='On Trip'||d.status==='Available').length;
    const utilization = veh.length ? Math.round((onTrip/veh.length)*100) : 0;

    const kpis = [
      {label:'Active Vehicles', val:active, sub:`of ${veh.length} in view`, color:'var(--accent)'},
      {label:'Available Vehicles', val:available, sub:'ready to dispatch', color:'var(--teal)'},
      {label:'In Maintenance', val:inShop, sub:'currently in shop', color:'var(--red)'},
      {label:'Active Trips', val:activeTrips, sub:'dispatched now', color:'var(--blue)'},
      {label:'Pending Trips', val:pendingTrips, sub:'in draft', color:'var(--accent)'},
      {label:'Drivers On Duty', val:driversOnDuty, sub:`of ${DB.drivers.length} total`, color:'var(--teal)'},
      {label:'Fleet Utilization', val:utilization+'%', sub:'on-trip share', color:'var(--blue)'},
    ];
    document.getElementById('kpiRow').innerHTML = kpis.map(k=>`
      <div class="kpi" style="--accent-color:${k.color}">
        <div class="k-label">${k.label}</div>
        <div class="k-val">${k.val}</div>
        <div class="k-sub">${k.sub}</div>
      </div>`).join('');
    this.renderCharts(veh);
  },
  renderCharts(veh){
    veh = veh || DB.vehicles;
    const statuses = ['Available','On Trip','In Shop','Retired'];
    const statusColors = ['var(--teal)','var(--blue)','var(--accent)','var(--red)'];
    const counts = statuses.map(s=>veh.filter(v=>v.status===s).length);
    document.getElementById('chartFleetStatus').innerHTML = Charts.donut(statuses, counts, statusColors);

    const tripStatuses = ['Draft','Dispatched','Completed','Cancelled'];
    const tripCounts = tripStatuses.map(s=>DB.trips.filter(t=>t.status===s).length);
    document.getElementById('chartTrips').innerHTML = Charts.bar(tripStatuses, tripCounts, 'var(--accent)');
  }
};

/* ---------------- VEHICLES ---------------- */
const Vehicles = {
  render(){
    const search = (document.getElementById('vehSearch').value||'').toLowerCase();
    const statusF = document.getElementById('vehStatusFilter').value;
    let list = DB.vehicles.filter(v => (!statusF||v.status===statusF) &&
      (v.reg.toLowerCase().includes(search) || v.name.toLowerCase().includes(search)));
    document.getElementById('vehCount').textContent = `${list.length} vehicle(s)`;
    const map = {Available:'b-teal','On Trip':'b-amber','In Shop':'b-red',Retired:'b-gray'};
    document.getElementById('vehTableBody').innerHTML = list.length ? list.map(v=>{
      const fuel = DB.fuelLogs.filter(f=>f.vehicleId===v.id).reduce((s,f)=>s+f.cost,0);
      const maint = DB.maintenance.filter(m=>m.vehicleId===v.id).reduce((s,m)=>s+m.cost,0);
      const km = v.odometer||1;
      return `<tr>
        <td><span class="reg-tag">${v.reg}</span></td>
        <td>${v.name}</td><td>${v.type}</td>
        <td>${fmt(v.capacity)} kg</td><td>${fmt(v.odometer)} km</td><td>${v.region}</td>
        <td>${statusBadge(v.status, map)}</td>
        <td>${fmtMoney((fuel+maint)/km)}</td>
        <td><div class="row-actions">
          <button class="icon-btn" title="Edit" onclick="Vehicles.openForm('${v.id}')">✎</button>
          <button class="icon-btn" title="Delete" onclick="Vehicles.remove('${v.id}')">🗑</button>
        </div></td>
      </tr>`;
    }).join('') : `<tr class="empty-row"><td colspan="9">No vehicles match your filters yet.</td></tr>`;
  },
  openForm(id){
    const v = id ? DB.vehicles.find(x=>x.id===id) : null;
    Modal.open(`
      <h3>${v?'Edit Vehicle':'Register Vehicle'}</h3>
      <div class="m-sub">${v?'Update this vehicle\'s master record.':'Add a new vehicle to the fleet registry.'}</div>
      <div class="form-grid">
        <div class="field full"><label>Registration Number (unique)</label><input id="f_reg" value="${v?v.reg:''}" placeholder="GJ-01-AB-1234"></div>
        <div class="field"><label>Vehicle Name / Model</label><input id="f_name" value="${v?v.name:''}" placeholder="Van-07"></div>
        <div class="field"><label>Type</label>
          <select id="f_type"><option>Van</option><option>Truck</option><option>Pickup</option><option>Trailer</option></select></div>
        <div class="field"><label>Max Load Capacity (kg)</label><input id="f_cap" type="number" value="${v?v.capacity:''}"></div>
        <div class="field"><label>Odometer (km)</label><input id="f_odo" type="number" value="${v?v.odometer:0}"></div>
        <div class="field"><label>Acquisition Cost (₹)</label><input id="f_cost" type="number" value="${v?v.cost:''}"></div>
        <div class="field"><label>Region</label><input id="f_region" value="${v?v.region:''}" placeholder="Ahmedabad"></div>
        <div class="field"><label>Status</label>
          <select id="f_status"><option>Available</option><option>On Trip</option><option>In Shop</option><option>Retired</option></select></div>
      </div>
      <div class="form-err" id="f_err"></div>
      <div class="modal-foot">
        <button class="btn-ghost" onclick="Modal.close()">Cancel</button>
        <button class="btn-primary" style="margin-top:0" onclick="Vehicles.save('${v?v.id:''}')">${v?'Save Changes':'Register Vehicle'}</button>
      </div>
    `);
    if(v){ document.getElementById('f_type').value=v.type; document.getElementById('f_status').value=v.status; }
  },
  save(id){
    const reg = document.getElementById('f_reg').value.trim();
    const name = document.getElementById('f_name').value.trim();
    const type = document.getElementById('f_type').value;
    const cap = parseFloat(document.getElementById('f_cap').value);
    const odo = parseFloat(document.getElementById('f_odo').value)||0;
    const cost = parseFloat(document.getElementById('f_cost').value)||0;
    const region = document.getElementById('f_region').value.trim() || 'Unassigned';
    const status = document.getElementById('f_status').value;
    const err = document.getElementById('f_err');
    if(!reg || !name || !cap){ err.textContent='Registration number, name and max load capacity are required.'; err.classList.add('active'); return; }
    const dup = DB.vehicles.find(v=>v.reg.toLowerCase()===reg.toLowerCase() && v.id!==id);
    if(dup){ err.textContent='This registration number is already in use — it must be unique.'; err.classList.add('active'); return; }
    if(id){
      const v = DB.vehicles.find(x=>x.id===id);
      Object.assign(v, {reg,name,type,capacity:cap,odometer:odo,cost,region,status});
    } else {
      DB.vehicles.push({id:DB.nextId('V'), reg,name,type,capacity:cap,odometer:odo,cost,region,status});
    }
    Modal.close(); Vehicles.render(); Toast.show(`Vehicle ${reg} saved.`);
  },
  remove(id){
    const v = DB.vehicles.find(x=>x.id===id);
    if(DB.trips.some(t=>t.vehicleId===id && (t.status==='Dispatched'))){ Toast.show('Cannot delete — vehicle is currently on a dispatched trip.', true); return; }
    DB.vehicles = DB.vehicles.filter(x=>x.id!==id);
    Vehicles.render(); Toast.show(`Vehicle ${v.reg} removed.`);
  },
  exportCSV(){
    const rows = [['Reg Number','Name','Type','Capacity','Odometer','Region','Status','Acquisition Cost']];
    DB.vehicles.forEach(v=>rows.push([v.reg,v.name,v.type,v.capacity,v.odometer,v.region,v.status,v.cost]));
    downloadCSV(rows, 'vehicles.csv');
  }
};

/* ---------------- DRIVERS ---------------- */
const Drivers = {
  render(){
    const search = (document.getElementById('drvSearch').value||'').toLowerCase();
    const statusF = document.getElementById('drvStatusFilter').value;
    let list = DB.drivers.filter(d => (!statusF||d.status===statusF) &&
      (d.name.toLowerCase().includes(search) || d.license.toLowerCase().includes(search)));
    document.getElementById('drvCount').textContent = `${list.length} driver(s)`;
    const map = {Available:'b-teal','On Trip':'b-amber','Off Duty':'b-gray',Suspended:'b-red'};
    document.getElementById('drvTableBody').innerHTML = list.length ? list.map(d=>{
      const expired = isExpired(d.expiry);
      return `<tr>
        <td>${d.name}</td>
        <td><span class="reg-tag">${d.license}</span></td>
        <td>${d.category}</td>
        <td>${d.expiry} ${expired?'<span class="badge b-red" style="margin-left:6px">Expired</span>':''}</td>
        <td>${d.contact}</td>
        <td>${d.score}</td>
        <td>${statusBadge(d.status, map)}</td>
        <td><div class="row-actions">
          <button class="icon-btn" title="Edit" onclick="Drivers.openForm('${d.id}')">✎</button>
          <button class="icon-btn" title="Delete" onclick="Drivers.remove('${d.id}')">🗑</button>
        </div></td>
      </tr>`;
    }).join('') : `<tr class="empty-row"><td colspan="8">No drivers match your filters yet.</td></tr>`;
  },
  openForm(id){
    const d = id ? DB.drivers.find(x=>x.id===id) : null;
    Modal.open(`
      <h3>${d?'Edit Driver':'Add Driver'}</h3>
      <div class="m-sub">${d?'Update this driver\'s profile.':'Register a new driver profile.'}</div>
      <div class="form-grid">
        <div class="field full"><label>Full Name</label><input id="f_dname" value="${d?d.name:''}"></div>
        <div class="field"><label>License Number</label><input id="f_lic" value="${d?d.license:''}"></div>
        <div class="field"><label>License Category</label>
          <select id="f_cat"><option>LMV</option><option>HMV</option><option>Trailer</option></select></div>
        <div class="field"><label>License Expiry</label><input id="f_exp" type="date" value="${d?d.expiry:''}"></div>
        <div class="field"><label>Contact Number</label><input id="f_contact" value="${d?d.contact:''}"></div>
        <div class="field"><label>Safety Score (0-100)</label><input id="f_score" type="number" min="0" max="100" value="${d?d.score:90}"></div>
        <div class="field full"><label>Status</label>
          <select id="f_dstatus"><option>Available</option><option>On Trip</option><option>Off Duty</option><option>Suspended</option></select></div>
      </div>
      <div class="form-err" id="f_derr"></div>
      <div class="modal-foot">
        <button class="btn-ghost" onclick="Modal.close()">Cancel</button>
        <button class="btn-primary" style="margin-top:0" onclick="Drivers.save('${d?d.id:''}')">${d?'Save Changes':'Add Driver'}</button>
      </div>
    `);
    if(d){ document.getElementById('f_cat').value=d.category; document.getElementById('f_dstatus').value=d.status; }
  },
  save(id){
    const name = document.getElementById('f_dname').value.trim();
    const license = document.getElementById('f_lic').value.trim();
    const category = document.getElementById('f_cat').value;
    const expiry = document.getElementById('f_exp').value;
    const contact = document.getElementById('f_contact').value.trim();
    const score = parseInt(document.getElementById('f_score').value)||0;
    const status = document.getElementById('f_dstatus').value;
    const err = document.getElementById('f_derr');
    if(!name || !license || !expiry){ err.textContent='Name, license number and expiry date are required.'; err.classList.add('active'); return; }
    if(id){ Object.assign(DB.drivers.find(x=>x.id===id), {name,license,category,expiry,contact,score,status}); }
    else{ DB.drivers.push({id:DB.nextId('D'), name,license,category,expiry,contact,score,status}); }
    Modal.close(); Drivers.render(); Toast.show(`Driver ${name} saved.`);
  },
  remove(id){
    const d = DB.drivers.find(x=>x.id===id);
    if(DB.trips.some(t=>t.driverId===id && t.status==='Dispatched')){ Toast.show('Cannot delete — driver is on a dispatched trip.', true); return; }
    DB.drivers = DB.drivers.filter(x=>x.id!==id);
    Drivers.render(); Toast.show(`Driver ${d.name} removed.`);
  }
};

/* ---------------- TRIPS ---------------- */
const Trips = {
  render(){
    const statusF = document.getElementById('tripStatusFilter').value;
    let list = DB.trips.filter(t=>!statusF||t.status===statusF);
    document.getElementById('tripCount').textContent = `${list.length} trip(s)`;
    const steps = ['Draft','Dispatched','Completed'];
    document.getElementById('tripTableBody').innerHTML = list.length ? list.slice().reverse().map(t=>{
      const flow = t.status==='Cancelled'
        ? `<div class="trip-flow"><span class="step done">Draft</span><span class="arrow">→</span><span class="step" style="color:var(--red);border-color:rgba(240,84,106,.35)">Cancelled</span></div>`
        : `<div class="trip-flow">${steps.map((s,i)=>{
            const reached = steps.indexOf(t.status) >= i;
            return `<span class="step ${reached?'done':''}">${s}</span>` + (i<steps.length-1?'<span class="arrow">→</span>':'');
          }).join('')}</div>`;
      let actions = '';
      if(t.status==='Draft') actions += `<button class="icon-btn" title="Dispatch" onclick="Trips.dispatch('${t.id}')">▶</button>`;
      if(t.status==='Dispatched') actions += `<button class="icon-btn" title="Complete" onclick="Trips.complete('${t.id}')">✓</button>`;
      if(t.status==='Draft'||t.status==='Dispatched') actions += `<button class="icon-btn" title="Cancel" onclick="Trips.cancel('${t.id}')">✕</button>`;
      return `<tr>
        <td class="mono">${t.id}</td>
        <td>${t.source} → ${t.dest}<div class="small-note">${fmtMoney(t.revenue)} revenue</div></td>
        <td><span class="reg-tag">${vReg(t.vehicleId)}</span></td>
        <td>${dName(t.driverId)}</td>
        <td>${fmt(t.cargo)} kg</td>
        <td>${fmt(t.distance)} km</td>
        <td>${flow}</td>
        <td><div class="row-actions">${actions}</div></td>
      </tr>`;
    }).join('') : `<tr class="empty-row"><td colspan="8">No trips yet — create one to get started.</td></tr>`;
  },
  openForm(){
    const availVehicles = DB.vehicles.filter(v=>v.status==='Available');
    const availDrivers = DB.drivers.filter(d=>d.status==='Available' && !isExpired(d.expiry));
    Modal.open(`
      <h3>Create Trip</h3>
      <div class="m-sub">Only available vehicles and compliant drivers are selectable.</div>
      <div class="form-grid">
        <div class="field"><label>Source</label><input id="t_src" placeholder="Ahmedabad"></div>
        <div class="field"><label>Destination</label><input id="t_dst" placeholder="Surat"></div>
        <div class="field full"><label>Vehicle (${availVehicles.length} available)</label>
          <select id="t_veh">${availVehicles.length? availVehicles.map(v=>`<option value="${v.id}" data-cap="${v.capacity}">${v.reg} — ${v.name} (max ${fmt(v.capacity)} kg)</option>`).join('') : '<option value="">No available vehicles</option>'}</select></div>
        <div class="field full"><label>Driver (${availDrivers.length} available)</label>
          <select id="t_drv">${availDrivers.length? availDrivers.map(d=>`<option value="${d.id}">${d.name} — license valid to ${d.expiry}</option>`).join('') : '<option value="">No available drivers</option>'}</select></div>
        <div class="field"><label>Cargo Weight (kg)</label><input id="t_cargo" type="number" placeholder="450"></div>
        <div class="field"><label>Planned Distance (km)</label><input id="t_dist" type="number" placeholder="110"></div>
        <div class="field full"><label>Expected Revenue (₹)</label><input id="t_rev" type="number" placeholder="9500"></div>
      </div>
      <div class="form-err" id="t_err"></div>
      <div class="modal-foot"><button class="btn-ghost" onclick="Modal.close()">Cancel</button>
      <button class="btn-primary" style="margin-top:0" onclick="Trips.save()">Create Trip (Draft)</button></div>
    `);
  },
  save(){
    const source = document.getElementById('t_src').value.trim();
    const dest = document.getElementById('t_dst').value.trim();
    const vehicleId = document.getElementById('t_veh').value;
    const driverId = document.getElementById('t_drv').value;
    const cargo = parseFloat(document.getElementById('t_cargo').value);
    const distance = parseFloat(document.getElementById('t_dist').value);
    const revenue = parseFloat(document.getElementById('t_rev').value)||0;
    const err = document.getElementById('t_err');
    if(!source||!dest||!vehicleId||!driverId||!cargo||!distance){ err.textContent='All fields are required to create a trip.'; err.classList.add('active'); return; }
    const veh = DB.vehicles.find(v=>v.id===vehicleId);
    if(cargo > veh.capacity){ err.textContent=`Cargo weight (${cargo} kg) exceeds ${veh.name}'s max load capacity (${veh.capacity} kg).`; err.classList.add('active'); return; }
    const drv = DB.drivers.find(d=>d.id===driverId);
    if(drv.status==='Suspended' || isExpired(drv.expiry)){ err.textContent='Selected driver is suspended or has an expired license.'; err.classList.add('active'); return; }
    DB.trips.push({id:DB.nextId('T'), source, dest, vehicleId, driverId, cargo, distance, revenue, status:'Draft', fuelUsed:0, odometerEnd:null, created:'2026-07-12'});
    Modal.close(); Trips.render(); Toast.show('Trip created as Draft.');
  },
  dispatch(id){
    const t = DB.trips.find(x=>x.id===id);
    const veh = DB.vehicles.find(v=>v.id===t.vehicleId);
    const drv = DB.drivers.find(d=>d.id===t.driverId);
    if(veh.status!=='Available'){ Toast.show(`${veh.name} is no longer available.`, true); return; }
    if(drv.status!=='Available' || isExpired(drv.expiry)){ Toast.show(`${drv.name} is unavailable or license expired.`, true); return; }
    t.status='Dispatched'; veh.status='On Trip'; drv.status='On Trip';
    Trips.render(); Vehicles.render(); Drivers.render(); Toast.show('Trip dispatched — vehicle & driver marked On Trip.');
  },
  complete(id){
    const t = DB.trips.find(x=>x.id===id);
    const veh = DB.vehicles.find(v=>v.id===t.vehicleId);
    const drv = DB.drivers.find(d=>d.id===t.driverId);
    const fuel = prompt(`Fuel consumed for this trip (liters)?`, '15') || '0';
    t.fuelUsed = parseFloat(fuel)||0;
    t.odometerEnd = veh.odometer + t.distance;
    veh.odometer = t.odometerEnd;
    t.status='Completed'; veh.status='Available'; drv.status='Available';
    if(t.fuelUsed>0){ DB.fuelLogs.push({id:DB.nextId('F'), vehicleId:veh.id, liters:t.fuelUsed, cost:Math.round(t.fuelUsed*111), date:'2026-07-12'}); }
    Trips.render(); Vehicles.render(); Drivers.render(); Toast.show('Trip completed — vehicle & driver marked Available.');
  },
  cancel(id){
    const t = DB.trips.find(x=>x.id===id);
    const veh = DB.vehicles.find(v=>v.id===t.vehicleId);
    const drv = DB.drivers.find(d=>d.id===t.driverId);
    if(t.status==='Dispatched'){ veh.status='Available'; drv.status='Available'; }
    t.status='Cancelled';
    Trips.render(); Vehicles.render(); Drivers.render(); Toast.show('Trip cancelled.');
  }
};

/* ---------------- MAINTENANCE ---------------- */
const Maint = {
  render(){
    document.getElementById('maintCount').textContent = `${DB.maintenance.length} record(s)`;
    const map = {Open:'b-amber', Closed:'b-teal'};
    document.getElementById('maintTableBody').innerHTML = DB.maintenance.length ? DB.maintenance.slice().reverse().map(m=>`
      <tr>
        <td><span class="reg-tag">${vReg(m.vehicleId)}</span> ${vName(m.vehicleId)}</td>
        <td>${m.type}</td><td>${m.desc}</td><td>${fmtMoney(m.cost)}</td><td>${m.opened}</td>
        <td>${statusBadge(m.status, map)}</td>
        <td>${m.status==='Open' ? `<button class="icon-btn" title="Close" onclick="Maint.close('${m.id}')">✓</button>` : ''}</td>
      </tr>`).join('') : `<tr class="empty-row"><td colspan="7">No maintenance records yet.</td></tr>`;
  },
  openForm(){
    const vehicles = DB.vehicles.filter(v=>v.status!=='Retired');
    Modal.open(`
      <h3>New Maintenance Record</h3>
      <div class="m-sub">Opening a record automatically moves the vehicle to "In Shop".</div>
      <div class="form-grid">
        <div class="field full"><label>Vehicle</label>
          <select id="m_veh">${vehicles.map(v=>`<option value="${v.id}">${v.reg} — ${v.name} (${v.status})</option>`).join('')}</select></div>
        <div class="field"><label>Type</label><input id="m_type" placeholder="Oil Change / Brake Service"></div>
        <div class="field"><label>Cost (₹)</label><input id="m_cost" type="number"></div>
        <div class="field full"><label>Description</label><input id="m_desc" placeholder="Details of the service"></div>
      </div>
      <div class="form-err" id="m_err"></div>
      <div class="modal-foot"><button class="btn-ghost" onclick="Modal.close()">Cancel</button>
      <button class="btn-primary" style="margin-top:0" onclick="Maint.save()">Open Record</button></div>
    `);
  },
  save(){
    const vehicleId = document.getElementById('m_veh').value;
    const type = document.getElementById('m_type').value.trim();
    const cost = parseFloat(document.getElementById('m_cost').value)||0;
    const desc = document.getElementById('m_desc').value.trim();
    const err = document.getElementById('m_err');
    if(!vehicleId||!type){ err.textContent='Vehicle and maintenance type are required.'; err.classList.add('active'); return; }
    const veh = DB.vehicles.find(v=>v.id===vehicleId);
    if(veh.status==='On Trip'){ err.textContent='Vehicle is currently on a trip and cannot be sent to maintenance.'; err.classList.add('active'); return; }
    DB.maintenance.push({id:DB.nextId('M'), vehicleId, type, desc, cost, opened:'2026-07-12', status:'Open'});
    veh.status='In Shop';
    Modal.close(); Maint.render(); Vehicles.render(); Toast.show(`${veh.name} moved to In Shop.`);
  },
  close(id){
    const m = DB.maintenance.find(x=>x.id===id);
    m.status='Closed';
    const veh = DB.vehicles.find(v=>v.id===m.vehicleId);
    if(veh.status!=='Retired') veh.status='Available';
    Maint.render(); Vehicles.render(); Toast.show(`${veh.name} restored to Available.`);
  }
};

/* ---------------- FUEL & EXPENSES ---------------- */
const Fuel = {
  tab:'fuel',
  switchTab(t){ this.tab=t; document.getElementById('tabFuel').classList.toggle('active', t==='fuel'); document.getElementById('tabExp').classList.toggle('active', t==='expense'); this.render(); },
  render(){
    if(this.tab==='fuel'){
      document.getElementById('fuelHead').innerHTML = `<tr><th>Vehicle</th><th>Liters</th><th>Cost</th><th>Date</th></tr>`;
      document.getElementById('fuelTableBody').innerHTML = DB.fuelLogs.length ? DB.fuelLogs.slice().reverse().map(f=>`
        <tr><td><span class="reg-tag">${vReg(f.vehicleId)}</span> ${vName(f.vehicleId)}</td><td>${f.liters} L</td><td>${fmtMoney(f.cost)}</td><td>${f.date}</td></tr>`).join('')
        : `<tr class="empty-row"><td colspan="4">No fuel logs yet.</td></tr>`;
    } else {
      document.getElementById('fuelHead').innerHTML = `<tr><th>Vehicle</th><th>Type</th><th>Amount</th><th>Date</th><th>Note</th></tr>`;
      document.getElementById('fuelTableBody').innerHTML = DB.expenses.length ? DB.expenses.slice().reverse().map(e=>`
        <tr><td><span class="reg-tag">${vReg(e.vehicleId)}</span> ${vName(e.vehicleId)}</td><td>${e.type}</td><td>${fmtMoney(e.amount)}</td><td>${e.date}</td><td>${e.note||'—'}</td></tr>`).join('')
        : `<tr class="empty-row"><td colspan="5">No other expenses logged yet.</td></tr>`;
    }
  },
  openFuelForm(){
    Modal.open(`
      <h3>Log Fuel</h3><div class="m-sub">Records total operational cost automatically.</div>
      <div class="form-grid">
        <div class="field full"><label>Vehicle</label><select id="fu_veh">${DB.vehicles.map(v=>`<option value="${v.id}">${v.reg} — ${v.name}</option>`).join('')}</select></div>
        <div class="field"><label>Liters</label><input id="fu_liters" type="number"></div>
        <div class="field"><label>Cost (₹)</label><input id="fu_cost" type="number"></div>
        <div class="field full"><label>Date</label><input id="fu_date" type="date" value="2026-07-12"></div>
      </div>
      <div class="form-err" id="fu_err"></div>
      <div class="modal-foot"><button class="btn-ghost" onclick="Modal.close()">Cancel</button>
      <button class="btn-primary" style="margin-top:0" onclick="Fuel.saveFuel()">Save Log</button></div>
    `);
  },
  saveFuel(){
    const vehicleId = document.getElementById('fu_veh').value;
    const liters = parseFloat(document.getElementById('fu_liters').value);
    const cost = parseFloat(document.getElementById('fu_cost').value);
    const date = document.getElementById('fu_date').value;
    const err = document.getElementById('fu_err');
    if(!liters||!cost||!date){ err.textContent='All fields are required.'; err.classList.add('active'); return; }
    DB.fuelLogs.push({id:DB.nextId('F'), vehicleId, liters, cost, date});
    Modal.close(); this.tab='fuel'; Fuel.switchTab('fuel'); Toast.show('Fuel log added.');
  },
  openExpenseForm(){
    Modal.open(`
      <h3>Log Expense</h3><div class="m-sub">Tolls, parking or other operational costs.</div>
      <div class="form-grid">
        <div class="field full"><label>Vehicle</label><select id="ex_veh">${DB.vehicles.map(v=>`<option value="${v.id}">${v.reg} — ${v.name}</option>`).join('')}</select></div>
        <div class="field"><label>Type</label><input id="ex_type" placeholder="Toll / Parking / Fine"></div>
        <div class="field"><label>Amount (₹)</label><input id="ex_amt" type="number"></div>
        <div class="field"><label>Date</label><input id="ex_date" type="date" value="2026-07-12"></div>
        <div class="field full"><label>Note</label><input id="ex_note" placeholder="Optional note"></div>
      </div>
      <div class="form-err" id="ex_err"></div>
      <div class="modal-foot"><button class="btn-ghost" onclick="Modal.close()">Cancel</button>
      <button class="btn-primary" style="margin-top:0" onclick="Fuel.saveExpense()">Save Expense</button></div>
    `);
  },
  saveExpense(){
    const vehicleId = document.getElementById('ex_veh').value;
    const type = document.getElementById('ex_type').value.trim();
    const amount = parseFloat(document.getElementById('ex_amt').value);
    const date = document.getElementById('ex_date').value;
    const note = document.getElementById('ex_note').value.trim();
    const err = document.getElementById('ex_err');
    if(!type||!amount||!date){ err.textContent='Type, amount and date are required.'; err.classList.add('active'); return; }
    DB.expenses.push({id:DB.nextId('E'), vehicleId, type, amount, date, note});
    Modal.close(); this.tab='expense'; Fuel.switchTab('expense'); Toast.show('Expense logged.');
  }
};

/* ---------------- REPORTS ---------------- */
const Reports = {
  compute(){
    return DB.vehicles.map(v=>{
      const fuel = DB.fuelLogs.filter(f=>f.vehicleId===v.id);
      const fuelCost = fuel.reduce((s,f)=>s+f.cost,0);
      const fuelLiters = fuel.reduce((s,f)=>s+f.liters,0);
      const maintCost = DB.maintenance.filter(m=>m.vehicleId===v.id).reduce((s,m)=>s+m.cost,0);
      const tripsFor = DB.trips.filter(t=>t.vehicleId===v.id);
      const revenue = tripsFor.filter(t=>t.status==='Completed').reduce((s,t)=>s+t.revenue,0);
      const distance = tripsFor.filter(t=>t.status==='Completed').reduce((s,t)=>s+t.distance,0);
      const totalCost = fuelCost + maintCost;
      const roi = v.cost ? (revenue - totalCost)/v.cost : 0;
      const eff = fuelLiters ? distance/fuelLiters : 0;
      return {v, fuelCost, maintCost, totalCost, revenue, roi, eff, distance};
    });
  },
  render(){
    const data = this.compute();
    const totalVeh = DB.vehicles.length;
    const onTrip = DB.vehicles.filter(v=>v.status==='On Trip').length;
    const util = totalVeh ? Math.round((onTrip/totalVeh)*100) : 0;
    const totalCost = data.reduce((s,d)=>s+d.totalCost,0);
    const totalRevenue = data.reduce((s,d)=>s+d.revenue,0);
    document.getElementById('reportStatStrip').innerHTML = `
      <div class="s"><div class="lbl">Fleet Utilization</div><div class="v">${util}%</div><div class="progress"><i style="width:${util}%"></i></div></div>
      <div class="s"><div class="lbl">Total Revenue</div><div class="v">${fmtMoney(totalRevenue)}</div></div>
      <div class="s"><div class="lbl">Total Operational Cost</div><div class="v">${fmtMoney(totalCost)}</div></div>
      <div class="s"><div class="lbl">Net Margin</div><div class="v">${fmtMoney(totalRevenue-totalCost)}</div></div>
    `;
    document.getElementById('reportTableBody').innerHTML = data.map(d=>`
      <tr>
        <td><span class="reg-tag">${d.v.reg}</span> ${d.v.name}</td>
        <td>${fmtMoney(d.revenue)}</td><td>${fmtMoney(d.fuelCost)}</td><td>${fmtMoney(d.maintCost)}</td>
        <td>${fmtMoney(d.totalCost)}</td><td>${fmtMoney(d.v.cost)}</td>
        <td style="color:${d.roi>=0?'var(--teal)':'var(--red)'}">${(d.roi*100).toFixed(1)}%</td>
        <td>${d.eff? d.eff.toFixed(1)+' km/L' : '—'}</td>
      </tr>`).join('');
    this.renderCharts(data);
  },
  renderCharts(data){
    data = data || this.compute();
    const labels = data.map(d=>d.v.name);
    document.getElementById('chartCost').innerHTML = Charts.stackedBar(labels,
      [{label:'Fuel', color:'var(--accent)', values:data.map(d=>d.fuelCost)},
       {label:'Maintenance', color:'var(--red)', values:data.map(d=>d.maintCost)}]);
    document.getElementById('chartEff').innerHTML = Charts.line(labels, data.map(d=>d.eff), 'var(--teal)', v=>v.toFixed(1));
  },
  exportCSV(){
    const data = this.compute();
    const rows = [['Vehicle','Revenue','Fuel Cost','Maintenance Cost','Total Op Cost','Acquisition','ROI %','Fuel Efficiency (km/L)']];
    data.forEach(d=>rows.push([d.v.name, d.revenue, d.fuelCost, d.maintCost, d.totalCost, d.v.cost, (d.roi*100).toFixed(1), d.eff.toFixed(1)]));
    downloadCSV(rows, 'transitops_report.csv');
  }
};

function downloadCSV(rows, filename){
  const csv = rows.map(r=>r.map(c=>`"${String(c).replace(/"/g,'""')}"`).join(',')).join('\\n');
  const blob = new Blob([csv], {type:'text/csv'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = filename; a.click();
  Toast.show(`${filename} downloaded.`);
}

App.init();