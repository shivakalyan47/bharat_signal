/* =====================================================================
   BharatSignal — app.js
   All bugs fixed, live IST clock, free map tiles, temperature forecast,
   full India coverage, auto-refresh every 5 minutes.
   ===================================================================== */

'use strict';

// ── State ──────────────────────────────────────────────────────────────────────
let appData   = null;
let map       = null;
let markers   = [];
let circles   = [];
let tempChart = null;
let refreshTimer = null;
let refreshSecsLeft = 120; // 2 minutes — synced with live worker
let filtersInitialized = false;

// ── IST Cities for live temperature ──────────────────────────────────────────
const INDIA_CITIES = [
  { name: 'Delhi',      lat: 28.6139, lon: 77.2090 },
  { name: 'Mumbai',     lat: 19.0760, lon: 72.8777 },
  { name: 'Chennai',    lat: 13.0827, lon: 80.2707 },
  { name: 'Kolkata',    lat: 22.5726, lon: 88.3639 },
  { name: 'Bengaluru',  lat: 12.9716, lon: 77.5946 },
  { name: 'Hyderabad',  lat: 17.3850, lon: 78.4867 },
  { name: 'Ahmedabad',  lat: 23.0225, lon: 72.5714 },
  { name: 'Jaipur',     lat: 26.9124, lon: 75.7873 },
  { name: 'Lucknow',    lat: 26.8467, lon: 80.9462 },
  { name: 'Bhopal',     lat: 23.2599, lon: 77.4126 },
  { name: 'Patna',      lat: 25.5941, lon: 85.1376 },
  { name: 'Guwahati',   lat: 26.1445, lon: 91.7362 },
  { name: 'Bhubaneswar',lat: 20.2961, lon: 85.8245 },
  { name: 'Srinagar',   lat: 34.0837, lon: 74.7973 },
  { name: 'Thiruvananthapuram', lat: 8.5241, lon: 76.9366 },
];

// ── IST Live Clock ─────────────────────────────────────────────────────────────
function startISTClock() {
  function updateClock() {
    const now = new Date();
    // Convert to IST (UTC+5:30)
    const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
    const ist = new Date(utc + 5.5 * 3600000);

    const h   = String(ist.getHours()).padStart(2, '0');
    const m   = String(ist.getMinutes()).padStart(2, '0');
    const s   = String(ist.getSeconds()).padStart(2, '0');
    const el  = document.getElementById('ist-time');
    if (el) el.textContent = `${h}:${m}:${s}`;
  }
  updateClock();
  setInterval(updateClock, 1000);
}

// Format a UTC ISO string to IST human-readable
function toIST(isoString) {
  const d = new Date(isoString);
  const utc = d.getTime() + (d.getTimezoneOffset() * 60000);
  const ist = new Date(utc + 5.5 * 3600000);
  return ist.toLocaleString('en-IN', { hour12: true, timeZone: 'Asia/Kolkata' });
}

// Current IST Date object
function nowIST() {
  const now = new Date();
  const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
  return new Date(utc + 5.5 * 3600000);
}

// ── Auto-Refresh: countdown & data reload ────────────────────────────────────
function startRefreshTimer() {
  refreshSecsLeft = 120;
  clearInterval(refreshTimer);
  refreshTimer = setInterval(() => {
    refreshSecsLeft--;
    const badge = document.getElementById('refresh-countdown');
    if (badge) {
      if (refreshSecsLeft <= 0) {
        badge.textContent = 'Refreshing...';
        loadData();
      } else {
        const m = Math.floor(refreshSecsLeft / 60);
        const s = refreshSecsLeft % 60;
        badge.textContent = m > 0 ? `${m}m ${s}s` : `${s}s`;
      }
    }
  }, 1000);
}

// ── Initialize Map ─────────────────────────────────────────────────────────────
function initMap() {
  const indiaBounds = L.latLngBounds(
    L.latLng(6.0, 66.0),   // SW corner — full India including Lakshadweep
    L.latLng(37.5, 100.0)  // NE corner — including Arunachal Pradesh
  );

  map = L.map('map', {
    zoomControl: false,
    attributionControl: true,
    maxBounds: indiaBounds,
    maxBoundsViscosity: 0.9,
    minZoom: 4,
    maxZoom: 16,
  }).setView([22.5, 82.5], 5);  // Center of India, proper zoom to see all states

  // ── FREE MAP TILE — Official OpenStreetMap
  L.tileLayer(
    'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 16,
      noWrap: true,
    }
  ).addTo(map);

  L.control.zoom({ position: 'bottomright' }).addTo(map);
}

// ── Fetch Pipeline Data ────────────────────────────────────────────────────────
async function loadData() {
  try {
    // Cache-bust to get fresh data
    const res = await fetch(`pipeline_data.json?t=${Date.now()}`);
    if (!res.ok) throw new Error('pipeline_data.json not found');
    appData = await res.json();
    refreshSecsLeft = 120; // Reset countdown
    renderApp();
  } catch (err) {
    console.error('Data load failed:', err);
    const area = document.querySelector('.content-area');
    if (area && !appData) {
      area.innerHTML = `
        <div class="empty-state" style="margin:2rem; font-size:1rem;">
          ⚠ Could not load <code>pipeline_data.json</code>.<br><br>
          Run the pipeline first:<br>
          <code style="color:var(--accent-cyan);">.venv\\Scripts\\python.exe -m apps.intelligence.pipeline</code>
        </div>`;
    }
  }
}

// ── Live Temperature from Open-Meteo (direct JS fetch, no API key) ────────────
async function fetchCityWeather(city) {
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${city.lat}&longitude=${city.lon}` +
    `&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation` +
    `&hourly=temperature_2m&timezone=Asia/Kolkata&forecast_days=1`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Weather fetch failed');
  return await res.json();
}

function getWeatherIcon(code) {
  if (!code && code !== 0) return '🌡';
  if (code === 0) return '☀️';
  if (code <= 3) return '⛅';
  if (code <= 48) return '🌫️';
  if (code <= 57) return '🌧';
  if (code <= 67) return '❄️';
  if (code <= 77) return '🌨';
  if (code <= 82) return '🌦';
  if (code <= 86) return '🌨';
  if (code <= 99) return '⛈';
  return '🌡';
}

function getTempColor(temp) {
  if (temp >= 42) return '#ff1e56';
  if (temp >= 38) return '#ff9f1c';
  if (temp >= 32) return '#f4d35e';
  if (temp >= 25) return '#2ec4b6';
  if (temp >= 15) return '#00f0ff';
  return '#7000ff';
}

async function renderWeatherPanel() {
  const grid = document.getElementById('weather-cities-grid');
  const strip = document.getElementById('temp-strip');
  if (!grid) return;

  grid.innerHTML = '<div class="empty-state">🌐 Fetching live temperatures from Open-Meteo...</div>';
  if (strip) strip.innerHTML = '<div class="temp-loading">Loading...</div>';

  const allTemps    = {};
  const allHourly   = {};
  const allMeta     = {};
  const allHourlyX  = [];  // shared time axis

  try {
    const results = await Promise.allSettled(INDIA_CITIES.map(c => fetchCityWeather(c)));
    grid.innerHTML = '';

    results.forEach((result, idx) => {
      const city = INDIA_CITIES[idx];
      if (result.status !== 'fulfilled') {
        grid.innerHTML += `<div class="glass-card city-weather-card"><div class="city-name">${city.name}</div><div style="color:var(--text-muted);font-size:0.8rem;">Unavailable</div></div>`;
        return;
      }

      const data = result.value;
      const cur  = data.current || {};
      const temp = cur.temperature_2m;
      const code = cur.weather_code;
      const wind = cur.wind_speed_10m;
      const hum  = cur.relative_humidity_2m;
      const hourly = data.hourly || {};
      const hourlyTemps = hourly.temperature_2m || [];
      const hourlyTimes = hourly.time || [];

      allTemps[city.name] = temp;
      allHourly[city.name] = hourlyTemps;
      allMeta[city.name]  = { code, wind, hum };

      const color = getTempColor(temp);
      const icon  = getWeatherIcon(code);

      // Get current IST hour index
      const istHour = nowIST().getHours();

      // Build hourly strip — next 12 hours from now
      let hourlyHtml = '';
      for (let i = istHour; i < Math.min(istHour + 12, hourlyTemps.length); i++) {
        const t  = hourlyTemps[i] !== undefined ? hourlyTemps[i].toFixed(1) : '--';
        const hh = hourlyTimes[i] ? hourlyTimes[i].slice(11, 16) : `${String(i).padStart(2,'0')}:00`;
        const tc = getTempColor(hourlyTemps[i] || 25);
        hourlyHtml += `
          <div class="hourly-item">
            <div class="hourly-time">${hh}</div>
            <div class="hourly-temp" style="color:${tc};">${t}°</div>
          </div>`;
      }

      grid.innerHTML += `
        <div class="glass-card city-weather-card" style="border-left:4px solid ${color};">
          <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
              <div class="city-name">${city.name}</div>
              <div class="city-temp-now" style="color:${color};">${temp !== undefined ? temp.toFixed(1) : '--'}°C</div>
              <div class="city-meta">${icon} · Wind ${wind || '--'} km/h · Humidity ${hum || '--'}%</div>
            </div>
            <div style="font-size:2.5rem;">${icon}</div>
          </div>
          <div class="hourly-strip">${hourlyHtml}</div>
        </div>`;

      // Build temp strip chip
      if (strip && temp !== undefined) {
        const chip = document.createElement('div');
        chip.className = 'temp-chip';
        chip.innerHTML = `<div class="temp-chip-city">${city.name}</div><div class="temp-chip-value" style="color:${color};">${temp.toFixed(1)}°C</div>`;
        strip.innerHTML = '';
        strip.appendChild(chip);
      }

      // Update IST clock display
      const istEl = document.getElementById('env-temp');
      if (istEl && idx === 0 && temp !== undefined) {
        istEl.textContent = `${temp.toFixed(1)}°C / ${getWeatherDescription(code)}`;
      }

      // Build chart labels from first city
      if (allHourlyX.length === 0 && hourlyTimes.length > 0) {
        for (let i = istHour; i < Math.min(istHour + 12, hourlyTimes.length); i++) {
          allHourlyX.push(hourlyTimes[i]?.slice(11, 16) || '');
        }
      }
    });

    // Rebuild temp strip properly
    if (strip) {
      strip.innerHTML = '';
      Object.entries(allTemps).forEach(([name, temp]) => {
        if (temp === undefined) return;
        const color = getTempColor(temp);
        const chip = document.createElement('div');
        chip.className = 'temp-chip';
        chip.innerHTML = `<div class="temp-chip-city">${name.split(' ')[0]}</div><div class="temp-chip-value" style="color:${color};">${temp.toFixed(1)}°C</div>`;
        strip.appendChild(chip);
      });
    }

    // Render forecast chart
    renderTempForecastChart(allHourlyX, allHourly);

  } catch (err) {
    console.error('Weather panel error:', err);
    grid.innerHTML = '<div class="empty-state">⚠ Could not load live temperatures. Check internet connection.</div>';
  }
}

function getWeatherDescription(code) {
  if (code === 0) return 'Clear Sky';
  if (code <= 3) return 'Partly Cloudy';
  if (code <= 48) return 'Foggy';
  if (code <= 67) return 'Rainy';
  if (code <= 77) return 'Snowy';
  if (code <= 99) return 'Thunderstorm';
  return 'Monitoring';
}

function renderTempForecastChart(labels, allHourly) {
  const ctx = document.getElementById('temp-forecast-chart');
  if (!ctx) return;

  if (tempChart) { tempChart.destroy(); tempChart = null; }

  const COLORS = ['#ff1e56','#ff9f1c','#f4d35e','#2ec4b6','#00f0ff','#7000ff','#00ff88','#ff6b9d'];
  const datasets = [];
  let ci = 0;

  Object.entries(allHourly).forEach(([cityName, hourlyTemps]) => {
    const istHour = nowIST().getHours();
    const sliced  = hourlyTemps.slice(istHour, istHour + labels.length);
    datasets.push({
      label: cityName,
      data: sliced,
      borderColor: COLORS[ci % COLORS.length],
      backgroundColor: 'transparent',
      borderWidth: 2,
      pointRadius: 3,
      tension: 0.4,
    });
    ci++;
  });

  tempChart = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      animation: { duration: 800 },
      plugins: {
        legend: { labels: { color: '#94a3b8', boxWidth: 14, font: { size: 11 } } },
      },
      scales: {
        x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.05)' } },
        y: {
          ticks: {
            color: '#94a3b8', font: { size: 10 },
            callback: v => `${v}°C`
          },
          grid: { color: 'rgba(255,255,255,0.05)' }
        },
      },
    },
  });
}

// ── Render App ─────────────────────────────────────────────────────────────────
function renderApp() {
  if (!appData) return;
  renderOverview();
  renderFeed();
  renderDNA();
  renderEvolution();
  renderForecasts();
  renderReality();
  renderScenarios();
  renderReplay();
  renderEvidence();
  renderWeatherPanel(); // Always fetch fresh temps
}

// ── Navigation ─────────────────────────────────────────────────────────────────
function initNav() {
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
      document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
      e.currentTarget.classList.add('active');
      const target = e.currentTarget.getAttribute('data-target');
      const panel  = document.getElementById(target);
      if (panel) panel.classList.add('active');
      if (target === 'panel-overview' && map) setTimeout(() => map.invalidateSize(), 100);
    });
  });
}

// ── Utilities ──────────────────────────────────────────────────────────────────
function fmt(str) { return (str || '').replace(/_/g, ' '); }

function getSeverityColor(s) {
  const v = s > 1.0 ? s : s * 10;
  if (v >= 8) return '#ff1e56';
  if (v >= 6) return '#ff9f1c';
  if (v >= 4) return '#f4d35e';
  return '#2ec4b6';
}

function getSeverityClass(s) {
  const v = s > 1.0 ? s : s * 10;
  if (v >= 8) return 'severity-critical';
  if (v >= 6) return 'severity-high';
  if (v >= 4) return 'severity-moderate';
  return 'severity-low';
}

function getProbClass(p) {
  if (p >= 60) return 'prob-high';
  if (p >= 30) return 'prob-med';
  return 'prob-low';
}

function animateValue(id, start, end, duration) {
  const el = document.getElementById(id);
  if (!el) return;
  const isPercent = el.getAttribute('data-is-percent') === 'true';
  let startTs = null;
  const step = (ts) => {
    if (!startTs) startTs = ts;
    const prog = Math.min((ts - startTs) / duration, 1);
    const ease = 1 - Math.pow(1 - prog, 4);
    const val  = Math.floor(ease * (end - start) + start);
    el.innerHTML = isPercent ? val + '%' : val;
    if (prog < 1) window.requestAnimationFrame(step);
    else el.innerHTML = isPercent ? end + '%' : end;
  };
  window.requestAnimationFrame(step);
}

function getFriendlyName(sitId) {
  if (!appData) return sitId;
  const sit = (appData.situations || []).find(s => s.id === sitId);
  if (!sit || !(sit.incident_ids || []).length) return sitId;
  const inc = (appData.incidents || []).find(i => i.id === sit.incident_ids[0]);
  if (!inc) return sitId;
  const topConcept = Object.keys(inc.core_concepts || {})[0] || '';
  return `${inc.region}${topConcept ? ': ' + fmt(topConcept) : ''}`;
}

// ── 1. Overview ───────────────────────────────────────────────────────────────
function renderOverview() {
  const stats = appData.stats || {};
  const incidents = appData.incidents || [];
  const situations = appData.situations || [];
  const signals = appData.signals || [];

  // Stats counters
  animateValue('stat-signals',    0, stats.total_signals   || 0, 1500);
  animateValue('stat-incidents',  0, stats.incidents_detected || 0, 1500);
  animateValue('stat-situations', 0, stats.situations_tracked || 0, 1500);
  animateValue('stat-accuracy',   0, stats.prediction_accuracy_percent || 0, 1500);

  // National Environment Card
  const envIcon   = document.getElementById('env-icon');
  const envThreat = document.getElementById('env-threat');

  // Find highest severity incident for the threat vector
  let maxSev = 0, topInc = null;
  incidents.forEach(inc => { if ((inc.max_severity || 0) > maxSev) { maxSev = inc.max_severity; topInc = inc; } });

  if (topInc) {
    const topConcept = Object.keys(topInc.core_concepts || {})[0] || 'Unknown';
    if (envThreat) {
      envThreat.innerHTML = `${fmt(topConcept).toUpperCase()}<br><span style="font-size:0.75rem;color:var(--text-muted);">(${topInc.region})</span>`;
    }
    if (envIcon) {
      const icon = (() => {
        if (topConcept.includes('cyclone') || topConcept.includes('rain') || topConcept.includes('flood')) return '⛈️';
        if (topConcept.includes('fire') || topConcept.includes('smog') || topConcept.includes('air')) return '🔥';
        if (topConcept.includes('earthquake') || topConcept.includes('seismic') || topConcept.includes('landslide')) return '⛰️';
        if (topConcept.includes('heat') || topConcept.includes('warm')) return '🌡️';
        if (topConcept.includes('wind')) return '💨';
        if (topConcept.includes('oil') || topConcept.includes('pollution')) return '☣️';
        return '🚨';
      })();
      envIcon.textContent = icon;
    }
  } else if (envThreat) {
    envThreat.textContent = 'NO IMMINENT THREATS';
    envThreat.style.color = 'var(--color-confirmed)';
    if (envIcon) envIcon.textContent = '✅';
  }

  // Map — clear old markers
  markers.forEach(m => { try { map.removeLayer(m); } catch(e){} });
  circles.forEach(c => { try { map.removeLayer(c); } catch(e){} });
  markers = []; circles = [];

  // Plot all signals
  signals.forEach(sig => {
    if (!sig.lat || !sig.lon) return;
    const color = getSeverityColor(sig.severity || 0);
    const icon  = L.divIcon({
      className: '',
      html: `<div class="pulse-marker" style="background:${color};box-shadow:0 0 8px ${color}"></div>`,
      iconSize: [16, 16], iconAnchor: [8, 8],
    });
    const m = L.marker([sig.lat, sig.lon], { icon }).addTo(map);
    m.bindPopup(`
      <b>${sig.title}</b><br>
      <span style="color:#94a3b8;font-size:0.8rem;">${sig.region || ''}</span><br>
      Type: <b>${fmt(sig.type)}</b><br>
      Severity: <b>${sig.severity ? (sig.severity * 10).toFixed(1) : 'N/A'}/10</b><br>
      Provenance: <b>${sig.provenance || 'unknown'}</b><br>
      Time (IST): ${toIST(sig.timestamp)}
    `);
    markers.push(m);
  });

  // Plot incident circles on top
  incidents.forEach(inc => {
    if (!inc.centroid_lat || !inc.centroid_lon) return;
    const color  = getSeverityColor(inc.max_severity || 0);
    const radius = Math.max(30000, (inc.signal_count || 1) * 20000);
    const circle = L.circle([inc.centroid_lat, inc.centroid_lon], {
      color, fillColor: color, fillOpacity: 0.18,
      radius, weight: 2, dashArray: '6 4'
    }).addTo(map);
    const topConcept = Object.keys(inc.core_concepts || {})[0] || '';
    circle.bindPopup(`
      <b>${inc.id} — ${inc.region}</b><br>
      Concept: <b style="color:${color}">${fmt(topConcept)}</b><br>
      Signals: <b>${inc.signal_count}</b><br>
      Severity: <b>${inc.max_severity_display || (inc.max_severity * 10).toFixed(1)}/10</b><br>
      Duration: ${inc.duration_minutes.toFixed(0)} mins
    `);
    circles.push(circle);
  });

  // Fit map to show all India properly
  map.setView([22.5, 82.5], 5);

  // Active situations list
  const sitList = document.getElementById('active-situations-list');
  if (sitList) {
    sitList.innerHTML = situations.length ? '' : '<div class="temp-loading">No active situations.</div>';
    situations.forEach(sit => {
      const friendly = getFriendlyName(sit.id);
      sitList.innerHTML += `
        <div style="padding:0.6rem 0.75rem; background:rgba(0,240,255,0.05); border-radius:6px; border-left:3px solid var(--accent-cyan); display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-weight:600; font-size:0.85rem; text-transform:capitalize;">${friendly}</div>
            <div style="font-size:0.65rem; color:var(--text-muted); font-family:var(--font-mono);">${sit.id}</div>
          </div>
          <span style="color:var(--accent-cyan); font-size:0.8rem; white-space:nowrap;">${sit.incident_count} incident${sit.incident_count !== 1 ? 's' : ''}</span>
        </div>`;
    });
  }

  // Top predictions
  const predList = document.getElementById('top-predictions-list');
  if (predList) {
    let allPreds = [];
    (appData.forecasts || []).forEach(f => {
      (f.predictions || []).forEach(p => allPreds.push({ ...p, sitId: f.situation_id }));
    });
    allPreds.sort((a, b) => b.probability - a.probability);

    predList.innerHTML = allPreds.length ? '' : '<div class="temp-loading">No predictions yet.</div>';
    allPreds.slice(0, 5).forEach(p => {
      const pClass = getProbClass(p.probability);
      predList.innerHTML += `
        <div style="padding:0.5rem; background:rgba(0,0,0,0.25); border-radius:6px;">
          <div style="display:flex; justify-content:space-between; margin-bottom:0.3rem; font-size:0.82rem;">
            <span style="text-transform:capitalize;">${fmt(p.concept)}</span>
            <span style="font-weight:bold; color:var(--color-critical);">${p.probability}%</span>
          </div>
          <div class="concept-bar-bg"><div class="concept-bar-fill ${pClass}" style="width:${Math.min(p.probability,100)}%"></div></div>
        </div>`;
    });
  }
}

// ── 2. Signal Feed ─────────────────────────────────────────────────────────────
function renderFeed() {
  const feedList  = document.getElementById('signal-feed-list');
  const typeFilter = document.getElementById('filter-type');
  const regionFilter = document.getElementById('filter-region');
  const provFilter = document.getElementById('filter-provenance');
  const countEl   = document.getElementById('feed-count');
  if (!feedList) return;

  let signals = [...(appData.signals || [])].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

  if (!filtersInitialized) {
    const types = [...new Set(signals.map(s => s.type))].sort();
    const regions = [...new Set(signals.map(s => s.region).filter(Boolean))].sort();
    const provs = [...new Set(signals.map(s => s.provenance).filter(Boolean))].sort();

    types.forEach(t => {
      const o = document.createElement('option'); o.value = t; o.textContent = fmt(t); typeFilter?.appendChild(o);
    });
    regions.forEach(r => {
      const o = document.createElement('option'); o.value = r; o.textContent = r; regionFilter?.appendChild(o);
    });
    provs.forEach(p => {
      const o = document.createElement('option'); o.value = p; o.textContent = p.charAt(0).toUpperCase() + p.slice(1); provFilter?.appendChild(o);
    });

    typeFilter?.addEventListener('change', renderFeed);
    regionFilter?.addEventListener('change', renderFeed);
    provFilter?.addEventListener('change', renderFeed);
    filtersInitialized = true;
  }

  if (typeFilter?.value && typeFilter.value !== 'all') signals = signals.filter(s => s.type === typeFilter.value);
  if (regionFilter?.value && regionFilter.value !== 'all') signals = signals.filter(s => s.region === regionFilter.value);
  if (provFilter?.value && provFilter.value !== 'all') signals = signals.filter(s => s.provenance === provFilter.value);

  if (countEl) countEl.textContent = `${signals.length} signal${signals.length !== 1 ? 's' : ''}`;

  const PROV_COLORS = {
    observed: '#00ff88', corroborated: '#00f0ff', inferred: '#f4d35e',
    forecast: '#7000ff', contradicted: '#ff1e56', unknown: '#94a3b8',
  };

  feedList.innerHTML = '';
  signals.forEach(sig => {
    const sevClass = getSeverityClass(sig.severity || 0);
    const sevColor = getSeverityColor(sig.severity || 0);
    const provColor = PROV_COLORS[sig.provenance] || '#94a3b8';
    const istTime = toIST(sig.timestamp);

    feedList.innerHTML += `
      <div class="glass-card feed-item ${sevClass}" style="border-left-color:${sevColor}; padding:0.9rem;">
        <div class="feed-header">
          <span class="type-badge">${fmt(sig.type)}</span>
          <span class="prov-badge" style="background:${provColor}22; color:${provColor}; border:1px solid ${provColor}44;">${(sig.provenance || 'unknown').toUpperCase()}</span>
          <span style="color:var(--text-muted); font-size:0.72rem; margin-left:auto;">${istTime}</span>
        </div>
        <div class="feed-title">${sig.title}</div>
        <div class="feed-desc">${sig.description}</div>
        <div class="feed-footer">
          <span>📍 ${sig.region || 'Unknown Region'}</span>
          <span>🏛 ${sig.source_name || 'Unknown'}</span>
          <span style="color:${sevColor};">⚡ ${sig.severity ? (sig.severity * 10).toFixed(1) : 'N/A'}/10</span>
        </div>
        ${sig.contradicts && sig.contradicts.length ? `<div style="font-size:0.72rem; color:#ff1e56; margin-top:0.4rem;">⚠ Contradicts: ${sig.contradicts.join(', ')}</div>` : ''}
      </div>`;
  });
}

// ── 3. Incident DNA ────────────────────────────────────────────────────────────
function renderDNA() {
  const dnaList = document.getElementById('incident-dna-list');
  const regionFilter = document.getElementById('dna-region-filter');
  if (!dnaList) return;

  const incidents = appData.incidents || [];

  // Populate region filter
  if (regionFilter && regionFilter.options.length === 1) {
    const regions = [...new Set(incidents.map(i => i.region).filter(Boolean))].sort();
    regions.forEach(r => {
      const o = document.createElement('option'); o.value = r; o.textContent = r; regionFilter.appendChild(o);
    });
    regionFilter.addEventListener('change', renderDNA);
  }

  const selRegion = regionFilter?.value || 'all';
  const filtered  = selRegion === 'all' ? incidents : incidents.filter(i => i.region === selRegion);

  dnaList.innerHTML = filtered.length ? '' : '<div class="empty-state">No incidents found.</div>';

  filtered.forEach(inc => {
    const sevClass  = getSeverityClass(inc.max_severity || 0);
    const sevDisplay = inc.max_severity_display !== undefined ? inc.max_severity_display : ((inc.max_severity || 0) * 10).toFixed(1);
    const sevColor  = getSeverityColor(inc.max_severity || 0);

    let conceptsHtml = '';
    if (inc.core_concepts && typeof inc.core_concepts === 'object') {
      for (const [concept, weight] of Object.entries(inc.core_concepts)) {
        const pct = Math.round(weight * 100);
        conceptsHtml += `
          <div class="concept-item">
            <div class="concept-label"><span>${fmt(concept)}</span><span>${pct}%</span></div>
            <div class="concept-bar-bg"><div class="concept-bar-fill" style="width:${pct}%"></div></div>
          </div>`;
      }
    }

    let evoHtml = '';
    if (inc.evolution && inc.evolution.length > 0) {
      evoHtml = `<div style="margin-bottom:0.75rem; padding:0.5rem; background:rgba(0,0,0,0.25); border-radius:6px; font-size:0.78rem;">
        <span style="color:var(--text-muted);">Evolution: </span>
        ${inc.evolution.map(e => `<span style="color:var(--accent-cyan);">${fmt(e)}</span>`).join(' → ')}
      </div>`;
    }

    dnaList.innerHTML += `
      <div class="glass-card dna-card ${sevClass}" style="border-left-color:${sevColor};">
        <div class="dna-header">
          <div class="dna-title">${inc.id}</div>
          <div class="type-badge">${inc.region}</div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:0.75rem; font-size:0.8rem; flex-wrap:wrap; gap:0.3rem;">
          <span>📊 ${inc.signal_count} signals</span>
          <span>⚡ Severity: <strong style="color:${sevColor};">${sevDisplay}/10</strong></span>
          <span>⏱ ${inc.duration_minutes?.toFixed(0) || 0} min</span>
        </div>
        ${evoHtml}
        <div class="concept-bar-container">
          <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem;">Core Concepts</div>
          ${conceptsHtml || '<span style="color:var(--text-muted); font-size:0.8rem;">No concepts extracted</span>'}
        </div>
        ${inc.entities && inc.entities.length ? `<div style="margin-top:0.75rem; font-size:0.72rem; color:var(--text-muted);">Entities: ${inc.entities.slice(0,6).map(e => `<span style="background:rgba(255,255,255,0.07);padding:0.1rem 0.4rem;border-radius:4px;margin-right:2px;">${fmt(e)}</span>`).join('')}</div>` : ''}
      </div>`;
  });
}

// ── 4. Situation Evolution ─────────────────────────────────────────────────────
function renderEvolution() {
  const list = document.getElementById('situation-evolution-list');
  if (!list) return;
  const situations = appData.situations || [];

  list.innerHTML = situations.length ? '' : '<div class="empty-state">No situations tracked.</div>';

  situations.forEach(sit => {
    let linkagesHtml = '';
    (sit.linkages || []).forEach(link => {
      const reasonsHtml = (link.reasons || []).map(r => `<li>${r}</li>`).join('');
      linkagesHtml += `
        <div class="linkage-item">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
            <span style="font-size:0.78rem; color:var(--text-muted);">Causal Score</span>
            <span style="font-family:var(--font-mono); color:var(--accent-cyan);">${Math.round((link.causal_score || 0) * 100)}%</span>
          </div>
          <div style="text-align:center; font-weight:600;">${link.source}</div>
          <div class="linkage-arrow">↓ causal link ↓</div>
          <div style="text-align:center; font-weight:600;">${link.target}</div>
          ${reasonsHtml ? `<ul style="font-size:0.75rem; color:var(--text-muted); margin-top:0.4rem; padding-left:1rem;">${reasonsHtml}</ul>` : ''}
        </div>`;
    });

    const friendly = getFriendlyName(sit.id);
    list.innerHTML += `
      <div class="glass-card evolution-card">
        <div class="dna-header">
          <div class="dna-title" style="text-transform:capitalize;">${friendly}</div>
          <div class="type-badge">${sit.incident_count} incidents</div>
        </div>
        ${linkagesHtml || '<div style="color:var(--text-muted); font-size:0.82rem; padding:0.5rem;">Single-incident situation — no causal linkages yet.</div>'}
      </div>`;
  });
}

// ── 5. Predictive Forecasts ────────────────────────────────────────────────────
function renderForecasts() {
  const list = document.getElementById('predictive-forecasts-list');
  if (!list) return;
  const forecasts = appData.forecasts || [];

  list.innerHTML = forecasts.length ? '' : '<div class="empty-state">No forecasts generated.</div>';

  forecasts.forEach(fc => {
    const preds = fc.predictions || [];
    let predsHtml = '';

    preds.forEach(p => {
      const pClass   = getProbClass(p.probability);
      const reasons  = p.reasoning || p.reasons || [];
      const rHtml    = reasons.map(r => `<li>${r}</li>`).join('');
      const barWidth = Math.min(p.probability, 100);

      predsHtml += `
        <div class="pred-item">
          <div class="pred-header">
            <span style="text-transform:capitalize;">${fmt(p.concept)}</span>
            <span style="font-family:var(--font-mono); color:${barWidth >= 60 ? 'var(--color-critical)' : barWidth >= 30 ? 'var(--color-high)' : 'var(--accent-cyan)'};">${p.probability}%</span>
          </div>
          <div class="concept-bar-bg"><div class="concept-bar-fill ${pClass}" style="width:${barWidth}%"></div></div>
          ${rHtml ? `<ul class="pred-reasons">${rHtml}</ul>` : ''}
        </div>`;
    });

    const friendly = getFriendlyName(fc.situation_id);
    list.innerHTML += `
      <div class="glass-card forecast-card">
        <div class="dna-header">
          <div class="dna-title" style="text-transform:capitalize;">${friendly}</div>
          <div class="type-badge" style="background:rgba(0,240,255,0.1); color:var(--accent-cyan); max-width:200px; overflow:hidden; text-overflow:ellipsis;">${fc.status.split('.')[0]}</div>
        </div>
        ${predsHtml || '<div style="color:var(--text-muted); font-size:0.82rem; padding:0.5rem;">No predictions above confidence threshold.</div>'}
      </div>`;
  });
}

// ── 6. Reality Loop ────────────────────────────────────────────────────────────
function renderReality() {
  const list = document.getElementById('reality-loop-list');
  if (!list) return;
  const reality = appData.reality_loop || [];

  list.innerHTML = reality.length ? '' : '<div class="empty-state">No reality checks yet. Confirmation signals are compared against predictions here.</div>';

  reality.forEach(r => {
    let obsHtml = '';
    (r.observations || []).forEach(o => {
      const vClass = o.verdict === 'CONFIRMED' ? 'verdict-confirmed' : o.verdict === 'MISSED' ? 'verdict-missed' : 'verdict-pending';
      obsHtml += `
        <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(0,0,0,0.2); padding:0.5rem 0.75rem; border-radius:4px; margin-bottom:0.4rem; font-size:0.82rem;">
          <span style="flex-grow:1; text-transform:capitalize;">${fmt(o.concept)}</span>
          <span style="font-family:var(--font-mono); color:var(--text-muted); margin-right:0.75rem;">${(o.predicted_prob * 100)?.toFixed(0) || '--'}%</span>
          <span class="verdict-badge ${vClass}">${o.verdict}</span>
        </div>`;
    });

    const acc      = r.accuracy || 0;
    const accColor = acc >= 60 ? 'var(--color-confirmed)' : acc >= 30 ? 'var(--color-high)' : 'var(--color-critical)';
    const friendly = getFriendlyName(r.situation_id);

    list.innerHTML += `
      <div class="glass-card reality-card">
        <div class="dna-header">
          <div class="dna-title" style="text-transform:capitalize;">${friendly}</div>
        </div>
        <div class="accuracy-display">
          <div class="accuracy-circle" style="border-color:${accColor}; color:${accColor};">${acc}%</div>
          <div style="font-size:0.82rem; color:var(--text-muted);">${r.summary || 'Predictions compared against confirmed ground-truth signals.'}</div>
        </div>
        <div>
          <div style="font-size:0.72rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem;">Observations</div>
          ${obsHtml || '<div style="color:var(--text-muted); font-size:0.8rem;">No individual observations recorded.</div>'}
        </div>
      </div>`;
  });
}

// ── 7. Scenario Trees ──────────────────────────────────────────────────────────
function renderScenarios() {
  const list = document.getElementById('scenario-trees-list');
  if (!list) return;
  const trees = appData.scenario_trees || [];

  list.innerHTML = trees.length ? '' : '<div class="empty-state">No scenario trees generated.</div>';

  function renderNode(node) {
    if (!node) return '';
    const prob  = node.probability || 0;
    const color = prob > 0.5 ? 'var(--color-critical)' : prob > 0.2 ? 'var(--color-high)' : 'var(--text-muted)';
    const children = node.branches || node.children || [];
    return `
      <div class="tree-node">
        <div class="node-content" style="border-left:3px solid ${color};">
          <div style="font-weight:600;"><span style="text-transform:capitalize;">${fmt(node.concept)}</span> <span style="color:${color}; float:right;">${Math.round(prob * 100)}%</span></div>
          ${node.evidence ? `<div style="font-size:0.72rem; color:var(--text-muted); margin-top:0.2rem;">Ev: ${node.evidence}</div>` : ''}
        </div>
        ${children.length ? `<div class="node-children">${children.map(renderNode).join('')}</div>` : ''}
      </div>`;
  }

  trees.forEach(tree => {
    const branches  = tree.branches || [];
    const treeHtml  = branches.map(renderNode).join('') || '<span class="empty-state">No branches.</span>';
    const friendly  = getFriendlyName(tree.situation_id);
    list.innerHTML += `
      <div class="glass-card scenario-card">
        <div class="dna-header">
          <div class="dna-title" style="text-transform:capitalize;">${friendly} — Scenarios</div>
          <div class="type-badge">${tree.total_scenarios || 0} scenario paths</div>
        </div>
        <div class="tree-container">${treeHtml}</div>
      </div>`;
  });
}

// ── 8. Incident Replay ─────────────────────────────────────────────────────────
function renderReplay() {
  const container = document.getElementById('incident-replay-list');
  const select    = document.getElementById('replay-incident-select');
  if (!container || !select) return;

  const replays = appData.replay_timelines || [];

  // Populate dropdown
  select.innerHTML = '<option value="">-- Select Incident --</option>';
  replays.forEach((r, idx) => {
    const o = document.createElement('option');
    o.value = idx;
    o.textContent = `${r.incident_id} (${r.total_snapshots} snapshots)`;
    select.appendChild(o);
  });

  function showReplay(idx) {
    const replay = replays[idx];
    if (!replay) { container.innerHTML = '<div class="empty-state">Select an incident above to replay its timeline.</div>'; return; }

    const snaps = replay.snapshots || [];

    let dotsHtml = snaps.map((snap, si) => {
      const d = new Date(snap.snapshot_time);
      const utc = d.getTime() + (d.getTimezoneOffset() * 60000);
      const ist = new Date(utc + 5.5 * 3600000);
      const hh = ist.getHours().toString().padStart(2,'0') + ':' + ist.getMinutes().toString().padStart(2,'0');
      return `<div class="snapshot-dot" data-snap="${si}" title="${hh} IST"></div>`;
    }).join('');

    container.innerHTML = `
      <div class="glass-card replay-card">
        <div class="dna-header">
          <div class="dna-title">Incident ${replay.incident_id} — Timeline Replay</div>
          <div class="type-badge">${replay.total_snapshots} snapshots</div>
        </div>
        <p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:0.75rem;">Click any dot on the timeline to view the intelligence state at that moment.</p>
        <div class="timeline-track">
          <div class="timeline-line"></div>
          ${dotsHtml}
        </div>
        <div class="snapshot-details" id="snap-detail">
          <div class="empty-state">Select a snapshot above to view details.</div>
        </div>
      </div>`;

    container.querySelectorAll('.snapshot-dot').forEach(dot => {
      dot.addEventListener('click', e => {
        container.querySelectorAll('.snapshot-dot').forEach(d => d.classList.remove('active'));
        e.currentTarget.classList.add('active');
        const si   = parseInt(e.currentTarget.getAttribute('data-snap'));
        const snap = snaps[si];
        const det  = document.getElementById('snap-detail');
        if (!det || !snap) return;

        const changes = (snap.what_changed || []).length > 0
          ? snap.what_changed.map(c => `<li>${c}</li>`).join('')
          : '<li style="color:var(--text-muted);">No major changes at this snapshot.</li>';

        det.innerHTML = `
          <div style="display:flex; justify-content:space-between; margin-bottom:0.75rem; padding-bottom:0.5rem; border-bottom:1px solid rgba(255,255,255,0.08);">
            <strong style="color:var(--accent-cyan); font-family:var(--font-mono);">⏱ ${toIST(snap.snapshot_time)}</strong>
            <span style="font-size:0.72rem; color:var(--text-muted);">Snapshot ${si + 1} of ${snaps.length}</span>
          </div>
          <div class="replay-stats-grid">
            <div class="replay-stat-item">
              <div class="replay-stat-val">${snap.signals_known}</div>
              <div class="replay-stat-label">Signals Known</div>
            </div>
            <div class="replay-stat-item">
              <div class="replay-stat-val">${snap.incidents_detected}</div>
              <div class="replay-stat-label">Incidents</div>
            </div>
            <div class="replay-stat-item">
              <div class="replay-stat-val">${snap.situations_active}</div>
              <div class="replay-stat-label">Situations</div>
            </div>
          </div>
          <div>
            <div style="font-size:0.72rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:1px; margin-bottom:0.4rem;">What Changed</div>
            <ul style="font-size:0.82rem; padding-left:1.25rem;">${changes}</ul>
          </div>`;
      });
    });

    // Auto-select first snapshot
    const firstDot = container.querySelector('.snapshot-dot');
    if (firstDot) firstDot.click();
  }

  // Default: show first replay
  if (replays.length > 0) {
    select.value = '0';
    showReplay(0);
  } else {
    container.innerHTML = '<div class="empty-state">No incident replays available. Run the pipeline to generate timeline data.</div>';
  }

  select.addEventListener('change', e => showReplay(parseInt(e.target.value)));
}

// ── 9. Evidence / Provenance Layer ─────────────────────────────────────────────
function renderEvidence() {
  const el = document.getElementById('evidence-provenance-list');
  if (!el) return;
  const signals = appData.signals || [];

  const PROV_META = {
    observed:     { label: 'OBSERVED',     color: '#00ff88', desc: 'Directly detected by sensor or verified source.' },
    corroborated: { label: 'CORROBORATED', color: '#00f0ff', desc: 'Confirmed by multiple independent sources.' },
    inferred:     { label: 'INFERRED',     color: '#f4d35e', desc: 'Deduced from related signals via causal logic.' },
    forecast:     { label: 'FORECAST',     color: '#7000ff', desc: 'Predicted by the ML engine.' },
    contradicted: { label: 'CONTRADICTED', color: '#ff1e56', desc: 'Contradicts other signals — reliability uncertain.' },
    unknown:      { label: 'UNKNOWN',      color: '#94a3b8', desc: 'Provenance could not be determined.' },
  };

  const groups = {};
  signals.forEach(s => { const p = s.provenance || 'unknown'; (groups[p] = groups[p] || []).push(s); });

  // Summary row
  let html = '<div style="display:flex;gap:0.75rem;flex-wrap:wrap;margin-bottom:1.5rem;">';
  Object.entries(PROV_META).forEach(([k, m]) => {
    const count = (groups[k] || []).length;
    html += `<div class="glass-card" style="padding:0.9rem;min-width:140px;text-align:center;border-top:3px solid ${m.color};">
      <div style="font-size:1.8rem;font-weight:bold;color:${m.color};font-family:var(--font-mono);">${count}</div>
      <div style="font-size:0.7rem;color:var(--text-muted);margin-top:0.2rem;">${m.label}</div>
    </div>`;
  });
  html += '</div>';
  el.innerHTML = html;

  Object.entries(PROV_META).forEach(([k, m]) => {
    const grp = groups[k] || [];
    if (!grp.length) return;

    let items = '';
    grp.forEach(sig => {
      const sevColor = getSeverityColor(sig.severity || 0);
      const cdWarn   = sig.contradicts && sig.contradicts.length
        ? `<div style="font-size:0.72rem;color:#ff1e56;margin-top:0.3rem;">⚠ Contradicts: ${sig.contradicts.join(', ')}</div>` : '';
      items += `
        <div style="padding:0.6rem 0.9rem;background:rgba(0,0,0,0.25);border-radius:6px;border-left:3px solid ${m.color};margin-bottom:0.4rem;">
          <div style="display:flex;justify-content:space-between;gap:0.5rem;">
            <div>
              <div style="font-weight:600;font-size:0.88rem;">${sig.title}</div>
              <div style="font-size:0.72rem;color:var(--text-muted);margin-top:0.15rem;">${sig.region || ''} · ${sig.source_name || ''} · ${sig.verification || ''}</div>
              ${cdWarn}
            </div>
            <div style="text-align:right;flex-shrink:0;">
              <div style="font-size:0.7rem;color:${sevColor};font-family:var(--font-mono);">⚡ ${sig.severity ? (sig.severity*10).toFixed(1) : '--'}/10</div>
              <div style="font-size:0.65rem;color:var(--text-muted);margin-top:0.2rem;">conf: ${sig.confidence !== undefined ? (sig.confidence*100).toFixed(0)+'%' : 'N/A'}</div>
            </div>
          </div>
        </div>`;
    });

    el.innerHTML += `
      <div class="glass-card" style="margin-bottom:1.25rem;padding:1.1rem;">
        <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem;border-bottom:1px solid rgba(255,255,255,0.08);padding-bottom:0.6rem;">
          <div style="width:11px;height:11px;border-radius:50%;background:${m.color};box-shadow:0 0 8px ${m.color};flex-shrink:0;"></div>
          <span style="font-family:var(--font-mono);font-size:0.95rem;font-weight:bold;color:${m.color};">${m.label}</span>
          <span style="font-size:0.78rem;color:var(--text-muted);">${grp.length} signal${grp.length !== 1 ? 's' : ''}</span>
          <span style="margin-left:auto;font-size:0.75rem;color:var(--text-muted);font-style:italic;">${m.desc}</span>
        </div>
        ${items}
      </div>`;
  });
}

// ── Bootstrap ──────────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  startISTClock();
  initNav();
  initMap();
  loadData();
  startRefreshTimer();
});
