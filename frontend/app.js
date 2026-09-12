/**
 * FloodShield AI & VR - Core Frontend Application
 * Real-Time Geospatial Safe Navigation, AI ML Flood Risk Prediction,
 * VR Simulation Sandbox & 8-Vector Telemetry Evaluation, Virtual Instructor Speech HUD
 */

// ============================================================================
// GLOBAL STATE
// ============================================================================
const STATE = {
  activeTab: 'tab-map',
  apiBase: window.location.origin,
  wsBase: `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/vr-telemetry`,
  
  // Geospatial Map State
  map: null,
  originMarker: null,
  destMarker: null,
  routePolylines: [],
  zonePolygons: [],
  hazardMarkers: [],
  shelterMarkers: [],
  originCoords: { lat: 26.1722, lng: 91.7458 },
  selectedShelterId: 's1',
  
  // Data Cache
  hazards: [],
  shelters: [],
  zones: [],
  alerts: [],
  scenarios: [],
  
  // Charts
  radarChart: null,
  
  // VR Simulation Sandbox State
  vr: {
    running: false,
    autoPlaying: false,
    trainee: { x: 80, y: 340, speed: 2.2, tool: 'Life Jacket' },
    victims: [
      { id: 'v1', x: 220, y: 220, name: 'Child (Triage 1)', rescued: false, color: '#38BDF8', priority: 'CRITICAL' },
      { id: 'v2', x: 380, y: 150, name: 'Elder (Triage 2)', rescued: false, color: '#FCD34D', priority: 'HIGH' },
      { id: 'v3', x: 500, y: 280, name: 'Citizen (Triage 3)', rescued: false, color: '#A7F3D0', priority: 'MODERATE' }
    ],
    hazards: [
      { id: 'vh1', x: 280, y: 200, radius: 45, type: 'ELECTRICAL', name: '11kV Submerged Transformer' },
      { id: 'vh2', x: 440, y: 240, radius: 50, type: 'BLOCKED_ROAD', name: 'Culvert Collapse' }
    ],
    shelterZone: { x: 660, y: 60, width: 80, height: 80, name: 'Elevated Shelter Safe Zone' },
    waterLevel: 0.45,
    waterRiseRate: 0.05,
    elapsedSec: 45,
    timerInterval: null,
    telemetryStream: [],
    keys: {}
  },
  
  // Voice & Instructor Settings
  speechEnabled: true,
  lastSpokenMessage: ''
};

// ============================================================================
// INITIALIZATION
// ============================================================================
document.addEventListener('DOMContentLoaded', async () => {
  initTabs();
  initMap();
  initSliders();
  initModals();
  initVRSimulation();
  initSpeechSynthesis();

  // Load initial backend datasets
  await loadInitialBackendData();

  // Attach event handlers
  setupEventHandlers();

  // Initial ML Prediction run with default inputs
  runFloodRiskPrediction();

  // Setup periodic polling for alerts & hazards (every 20s)
  setInterval(refreshDynamicData, 20000);
});

// ============================================================================
// TAB NAVIGATION
// ============================================================================
function initTabs() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetTab = tab.getAttribute('data-tab');
      switchTab(targetTab);
    });
  });
}

function switchTab(tabId) {
  STATE.activeTab = tabId;
  
  document.querySelectorAll('.nav-tab').forEach(t => {
    t.classList.toggle('active', t.getAttribute('data-tab') === tabId);
  });

  document.querySelectorAll('.tab-pane').forEach(p => {
    p.classList.toggle('active', p.id === tabId);
  });

  // Trigger leaflet resize on map tab
  if (tabId === 'tab-map' && STATE.map) {
    setTimeout(() => { STATE.map.invalidateSize(); }, 200);
  }

  // Trigger chart resize on VR tab
  if (tabId === 'tab-vr' && STATE.radarChart) {
    setTimeout(() => { STATE.radarChart.resize(); }, 200);
  }
}

// ============================================================================
// LEAFLET MAP INITIALIZATION & VISUAL LAYERS
// ============================================================================
function initMap() {
  const mapElement = document.getElementById('disasterMap');
  if (!mapElement) return;

  STATE.map = L.map('disasterMap', {
    zoomControl: true,
    attributionControl: false
  }).setView([STATE.originCoords.lat, STATE.originCoords.lng], 13);

  // High-tech dark matter map tiles
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    maxZoom: 19,
    subdomains: 'abcd'
  }).addTo(STATE.map);

  // User Draggable Origin Marker
  const originIcon = L.divIcon({
    className: 'custom-map-icon',
    html: `<div style="background: linear-gradient(135deg, #0284C7, #06B6D4); width: 34px; height: 34px; border-radius: 50%; border: 3px solid #ffffff; box-shadow: 0 0 16px #06B6D4; display: flex; align-items: center; justify-content: center; color: #ffffff; font-size: 16px;"><i class="fa-solid fa-person-walking"></i></div>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17]
  });

  STATE.originMarker = L.marker([STATE.originCoords.lat, STATE.originCoords.lng], {
    draggable: true,
    icon: originIcon
  }).addTo(STATE.map);

  STATE.originMarker.bindPopup(`<strong>Your Origin Location</strong><br>Drag pin or click map to move`);

  STATE.originMarker.on('dragend', function(e) {
    const latlng = e.target.getLatLng();
    setOriginCoords(latlng.lat, latlng.lng);
  });

  // Map click to move origin
  STATE.map.on('click', function(e) {
    setOriginCoords(e.latlng.lat, e.latlng.lng);
  });
}

function setOriginCoords(lat, lng) {
  STATE.originCoords = { lat: parseFloat(lat.toFixed(4)), lng: parseFloat(lng.toFixed(4)) };
  if (STATE.originMarker) {
    STATE.originMarker.setLatLng([STATE.originCoords.lat, STATE.originCoords.lng]);
  }
  document.getElementById('currentCoordsDisplay').textContent = `${STATE.originCoords.lat}° N, ${STATE.originCoords.lng}° E`;
  document.getElementById('predLat').value = STATE.originCoords.lat;
  document.getElementById('predLng').value = STATE.originCoords.lng;
  showToast(`Origin updated to ${STATE.originCoords.lat}, ${STATE.originCoords.lng}`, 'info');
}

// ============================================================================
// BACKEND API SYNC & INITIAL DATA LOAD
// ============================================================================
async function loadInitialBackendData() {
  try {
    // 1. Health & Root Check
    const rootRes = await fetch(`${STATE.apiBase}/`);
    if (rootRes.ok) {
      const rootData = await rootRes.json();
      document.getElementById('systemStatusText').textContent = rootData.status || 'OPERATIONAL';
      if (rootData.model_ready) {
        document.getElementById('modelStatusText').textContent = 'ML Predictor: Online';
      }
    }

    // 2. Fetch Hazards
    const hazardsRes = await fetch(`${STATE.apiBase}/api/v1/hazards`);
    if (hazardsRes.ok) {
      const data = await hazardsRes.json();
      STATE.hazards = data.hazards || [];
      document.getElementById('headerHazardCount').textContent = STATE.hazards.length;
      renderMapHazards();
      renderHazardsTable();
    }

    // 3. Fetch Shelters
    const sheltersRes = await fetch(`${STATE.apiBase}/api/v1/shelters`);
    if (sheltersRes.ok) {
      const data = await sheltersRes.json();
      STATE.shelters = data.shelters || [];
      document.getElementById('headerShelterCount').textContent = STATE.shelters.length;
      renderMapShelters();
      renderShelterSelectOptions();
      renderSheltersCards();
    }

    // 4. Fetch Monitored Flood Zones
    const zonesRes = await fetch(`${STATE.apiBase}/api/v1/zones`);
    if (zonesRes.ok) {
      const data = await zonesRes.json();
      STATE.zones = data.zones || [];
      renderMapZones();
      renderZonesCards();
    }

    // 5. Fetch Scenarios
    const scenRes = await fetch(`${STATE.apiBase}/api/v1/scenarios`);
    if (scenRes.ok) {
      const data = await scenRes.json();
      STATE.scenarios = data.scenarios || [];
    }

    // 6. Fetch Broadcast Alerts
    const alertsRes = await fetch(`${STATE.apiBase}/api/v1/alerts`);
    if (alertsRes.ok) {
      const data = await alertsRes.json();
      STATE.alerts = data.alerts || [];
      renderAlerts();
    }

    // Run initial safe route calculation
    await calculateSafeRoute();

  } catch (err) {
    console.warn('Backend connection notice:', err);
    showToast('Connecting to FloodShield AI Backend server...', 'info');
  }
}

async function refreshDynamicData() {
  try {
    const [hazardsRes, alertsRes] = await Promise.all([
      fetch(`${STATE.apiBase}/api/v1/hazards`),
      fetch(`${STATE.apiBase}/api/v1/alerts`)
    ]);
    if (hazardsRes.ok) {
      const data = await hazardsRes.json();
      STATE.hazards = data.hazards || [];
      document.getElementById('headerHazardCount').textContent = STATE.hazards.length;
      renderMapHazards();
      renderHazardsTable();
    }
    if (alertsRes.ok) {
      const data = await alertsRes.json();
      STATE.alerts = data.alerts || [];
      renderAlerts();
    }
  } catch (e) {
    // Background polling catch
  }
}

// ============================================================================
// MAP RENDERING LAYERS (Zones, Hazards, Shelters, Routes)
// ============================================================================
function renderMapZones() {
  if (!STATE.map) return;

  // Clear existing polygons
  STATE.zonePolygons.forEach(p => STATE.map.removeLayer(p));
  STATE.zonePolygons = [];

  STATE.zones.forEach(zone => {
    if (zone.polygon && zone.polygon.length > 0) {
      const polygon = L.polygon(zone.polygon, {
        color: '#EF4444',
        weight: 1.5,
        opacity: 0.8,
        fillColor: '#EF4444',
        fillOpacity: 0.15,
        dashArray: '4, 4'
      }).addTo(STATE.map);

      polygon.bindPopup(`
        <strong>${zone.name}</strong><br>
        State: ${zone.state}<br>
        Water Level: ${zone.water_level}m | Discharge: ${zone.discharge} m³/s<br>
        Baseline Rain: ${zone.baseline_rain} mm
      `);

      STATE.zonePolygons.push(polygon);
    }
  });
}

function renderMapHazards() {
  if (!STATE.map) return;

  STATE.hazardMarkers.forEach(m => STATE.map.removeLayer(m));
  STATE.hazardMarkers = [];

  STATE.hazards.forEach(h => {
    const isElectric = h.type === 'ELECTRICAL';
    const color = isElectric ? '#EF4444' : '#F59E0B';
    const iconClass = isElectric ? 'fa-bolt' : (h.type === 'BLOCKED_ROAD' ? 'fa-road-barrier' : 'fa-triangle-exclamation');

    const icon = L.divIcon({
      className: 'custom-hazard-icon',
      html: `<div style="background: ${color}; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 13px; box-shadow: 0 0 12px ${color}; border: 2px solid #ffffff;"><i class="fa-solid ${iconClass}"></i></div>`,
      iconSize: [28, 28],
      iconAnchor: [14, 14]
    });

    const marker = L.marker([h.lat, h.lng], { icon: icon }).addTo(STATE.map);
    marker.bindPopup(`
      <strong style="color: ${color};"><i class="fa-solid ${iconClass}"></i> ${h.type} HAZARD</strong><br>
      <strong>Description:</strong> ${h.desc}<br>
      <strong>Severity Multiplier:</strong> ${h.severity}x<br>
      <strong>Danger Radius:</strong> ${h.radius_m}m
    `);

    // Radius circle
    const circle = L.circle([h.lat, h.lng], {
      radius: h.radius_m,
      color: color,
      weight: 1,
      fillColor: color,
      fillOpacity: 0.12
    }).addTo(STATE.map);

    STATE.hazardMarkers.push(marker);
    STATE.hazardMarkers.push(circle);
  });
}

function renderMapShelters() {
  if (!STATE.map) return;

  STATE.shelterMarkers.forEach(m => STATE.map.removeLayer(m));
  STATE.shelterMarkers = [];

  STATE.shelters.forEach(s => {
    const icon = L.divIcon({
      className: 'custom-shelter-icon',
      html: `<div style="background: #10B981; width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-size: 14px; box-shadow: 0 0 14px #10B981; border: 2px solid #ffffff;"><i class="fa-solid fa-hospital"></i></div>`,
      iconSize: [30, 30],
      iconAnchor: [15, 15]
    });

    const marker = L.marker([s.lat, s.lng], { icon: icon }).addTo(STATE.map);
    const occupancyPct = Math.round((s.occupancy / s.capacity) * 100);

    marker.bindPopup(`
      <strong style="color: #10B981;"><i class="fa-solid fa-hospital"></i> ${s.name}</strong><br>
      Elevation: <strong>${s.elevation}m ASL</strong><br>
      Capacity: ${s.occupancy} / ${s.capacity} (${occupancyPct}% full)<br>
      <button onclick="window.selectShelterDestination('${s.id}')" style="margin-top: 6px; background: #0284C7; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 11px; cursor: pointer;">Route Here</button>
    `);

    STATE.shelterMarkers.push(marker);
  });
}

window.selectShelterDestination = function(shelterId) {
  const select = document.getElementById('destinationShelterSelect');
  if (select) {
    select.value = shelterId;
  }
  calculateSafeRoute();
};

function renderShelterSelectOptions() {
  const select = document.getElementById('destinationShelterSelect');
  if (!select) return;
  select.innerHTML = '<option value="auto">Auto Nearest Safe Shelter</option>';
  STATE.shelters.forEach(s => {
    const opt = document.createElement('option');
    opt.value = s.id;
    opt.textContent = `${s.name} (${s.elevation}m ASL)`;
    select.appendChild(opt);
  });
}

// ============================================================================
// DYNAMIC SAFE ROUTE CALCULATION (A* / Dijkstra)
// ============================================================================
async function calculateSafeRoute() {
  const btn = document.getElementById('btnCalculateSafeRoute');
  if (btn) btn.disabled = true;

  try {
    const algorithm = document.getElementById('routeAlgorithm').value;
    const destSelect = document.getElementById('destinationShelterSelect').value;
    const hazardWeight = parseFloat(document.getElementById('hazardWeightRange').value);
    const floodWeight = parseFloat(document.getElementById('floodWeightRange').value);

    let destLat = null;
    let destLng = null;
    let targetShelterId = null;

    if (destSelect !== 'auto') {
      const chosen = STATE.shelters.find(s => s.id === destSelect);
      if (chosen) {
        destLat = chosen.lat;
        destLng = chosen.lng;
        targetShelterId = chosen.id;
      }
    }

    const payload = {
      origin_latitude: STATE.originCoords.lat,
      origin_longitude: STATE.originCoords.lng,
      algorithm: algorithm,
      hazard_penalty_weight: hazardWeight,
      flood_risk_weight: floodWeight,
      avoid_water_above_meters: 0.6
    };

    if (destLat && destLng) {
      payload.destination_latitude = destLat;
      payload.destination_longitude = destLng;
      payload.destination_shelter_id = targetShelterId;
    }

    const res = await fetch(`${STATE.apiBase}/api/v1/routing/safe-route`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    // Render Routes on Leaflet Map
    renderRoutePolylines(data);

    // Update HUD metrics
    const primary = data.primary_safest_route;
    document.getElementById('metricDistance').textContent = `${primary.distance_km.toFixed(2)} km`;
    document.getElementById('metricTime').textContent = `${primary.estimated_time_min.toFixed(1)} min`;
    document.getElementById('metricSafety').textContent = `${primary.safety_score.toFixed(1)}%`;
    document.getElementById('metricWater').textContent = `${primary.average_water_level_m.toFixed(2)} m`;
    document.getElementById('currentDestDisplay').textContent = data.destination_shelter_name;
    document.getElementById('evacStatusBadge').textContent = 'ACTIVE GUIDANCE ONLINE';

    // Update Avoided Hazards list
    const badgeStrip = document.getElementById('hazardBadgeStrip');
    if (badgeStrip) {
      badgeStrip.innerHTML = '';
      if (primary.avoided_hazards && primary.avoided_hazards.length > 0) {
        primary.avoided_hazards.forEach(h => {
          const badge = document.createElement('span');
          badge.className = 'badge-chip';
          badge.innerHTML = `<i class="fa-solid fa-shield-check"></i> ${h} Bypassed`;
          badgeStrip.appendChild(badge);
        });
      } else {
        badgeStrip.innerHTML = '<span class="badge-chip"><i class="fa-solid fa-check"></i> Standard Clear Path Maintained</span>';
      }
    }

    // Turn by turn instructions
    const stepList = document.getElementById('stepInstructionList');
    if (stepList) {
      stepList.innerHTML = '';
      primary.turn_by_turn_instructions.forEach(step => {
        const li = document.createElement('li');
        li.className = 'step-item';
        li.textContent = step;
        stepList.appendChild(li);
      });
    }

    showToast(`Safe route calculated via ${algorithm} avoiding active hazards!`, 'success');

  } catch (err) {
    console.error('Safe route error:', err);
    showToast('Safe route engine offline or recalculating...', 'error');
  } finally {
    if (btn) btn.disabled = false;
  }
}

function renderRoutePolylines(routeResponse) {
  if (!STATE.map) return;

  // Remove existing polylines
  STATE.routePolylines.forEach(l => STATE.map.removeLayer(l));
  STATE.routePolylines = [];

  const primary = routeResponse.primary_safest_route;
  const alt = routeResponse.alternative_route;

  // 1. Draw Alternative Route first (underneath)
  if (alt && alt.waypoints && alt.waypoints.length > 0) {
    const altCoords = alt.waypoints.map(w => [w.latitude, w.longitude]);
    const altPolyline = L.polyline(altCoords, {
      color: '#F59E0B',
      weight: 4,
      dashArray: '6, 8',
      opacity: 0.75
    }).addTo(STATE.map);
    altPolyline.bindPopup(`<strong>Alternative Bypass Corridor</strong><br>Distance: ${alt.distance_km.toFixed(2)} km | Safety: ${alt.safety_score}%`);
    STATE.routePolylines.push(altPolyline);
  }

  // 2. Draw Primary Safest Route (Emerald Green Glow)
  if (primary && primary.waypoints && primary.waypoints.length > 0) {
    const primaryCoords = primary.waypoints.map(w => [w.latitude, w.longitude]);
    
    // Outer glow
    const glowLine = L.polyline(primaryCoords, {
      color: '#10B981',
      weight: 9,
      opacity: 0.35
    }).addTo(STATE.map);
    
    // Main solid line
    const mainLine = L.polyline(primaryCoords, {
      color: '#10B981',
      weight: 5,
      opacity: 0.95
    }).addTo(STATE.map);

    mainLine.bindPopup(`<strong>Primary Safest Evacuation Corridor</strong><br>Distance: ${primary.distance_km.toFixed(2)} km<br>Est. Time: ${primary.estimated_time_min.toFixed(1)} min<br>Safety Score: ${primary.safety_score}%`);

    STATE.routePolylines.push(glowLine);
    STATE.routePolylines.push(mainLine);

    // Fit map bounds to view both origin and destination
    STATE.map.fitBounds(mainLine.getBounds(), { padding: [40, 40] });
  }
}

// ============================================================================
// ONE-CLICK LOCATION ANALYSIS
// ============================================================================
async function runLocationAnalysis() {
  const btn = document.getElementById('btnAnalyzeLiveLocation');
  if (btn) btn.disabled = true;

  try {
    const res = await fetch(`${STATE.apiBase}/api/v1/geo/location-analysis`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        latitude: STATE.originCoords.lat,
        longitude: STATE.originCoords.lng
      })
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const card = document.getElementById('locationAnalysisResultCard');
    card.style.display = 'block';
    document.getElementById('repZoneName').textContent = data.nearest_region_name;
    document.getElementById('repFloodProb').textContent = `${(data.flood_probability * 100).toFixed(1)}%`;
    document.getElementById('repShelterName').textContent = data.nearest_safe_shelter.name;

    const badge = document.getElementById('repUrgencyBadge');
    badge.textContent = data.evacuation_urgency;
    badge.className = 'tier-badge ' + (data.evacuation_urgency.includes('CRITICAL') ? 'badge-high' : (data.evacuation_urgency.includes('ELEVATED') ? 'badge-med' : 'badge-low'));

    // Trigger route rendering from the embedded safe route
    if (data.safe_route) {
      renderRoutePolylines(data.safe_route);
    }

    showToast(`Full Geospatial Analysis Completed for ${data.nearest_region_name}!`, 'success');
  } catch (err) {
    console.error('Location analysis error:', err);
    showToast('Failed to run location analysis', 'error');
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ============================================================================
// AI FLOOD RISK ML PREDICTOR
// ============================================================================
async function runFloodRiskPrediction() {
  const btn = document.getElementById('btnRunPrediction');
  if (btn) btn.disabled = true;

  try {
    const payload = {
      Latitude: parseFloat(document.getElementById('predLat').value),
      Longitude: parseFloat(document.getElementById('predLng').value),
      Rainfall_mm: parseFloat(document.getElementById('predRainfall').value),
      Temperature_C: parseFloat(document.getElementById('predTemp').value),
      Humidity_pct: parseFloat(document.getElementById('predHumidity').value),
      River_Discharge_m3_s: parseFloat(document.getElementById('predRiverDischarge').value),
      Water_Level_m: parseFloat(document.getElementById('predWaterLevel').value),
      Elevation_m: parseFloat(document.getElementById('predElevation').value),
      Land_Cover: document.getElementById('predLandCover').value,
      Soil_Type: document.getElementById('predSoilType').value,
      Population_Density: parseFloat(document.getElementById('predPopulation').value),
      Infrastructure: document.getElementById('predInfrastructure').value,
      Historical_Floods: parseInt(document.getElementById('predHistoricalFloods').value, 10)
    };

    const res = await fetch(`${STATE.apiBase}/api/v1/predict/flood-risk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    // 1. Update Radial Gauge
    const probPct = data.flood_probability * 100;
    document.getElementById('gaugePercentVal').textContent = `${probPct.toFixed(1)}%`;
    
    // Gauge Arc math: total perimeter 251.2
    const fill = document.getElementById('gaugeProgressFill');
    const offset = 251.2 - (251.2 * (probPct / 100));
    fill.style.strokeDashoffset = offset;
    fill.style.stroke = data.risk_color || (probPct > 60 ? '#EF4444' : (probPct > 30 ? '#F59E0B' : '#10B981'));

    // 2. Risk Level Badge
    const riskBadge = document.getElementById('riskLevelBadge');
    riskBadge.textContent = data.risk_level;
    riskBadge.style.color = data.risk_color;
    riskBadge.style.borderColor = data.risk_color;

    // 3. Top Contributing Factors
    const factorsList = document.getElementById('factorsList');
    factorsList.innerHTML = '';
    data.top_contributing_factors.forEach(f => {
      const item = document.createElement('div');
      item.className = 'factor-bar-item';
      const pct = Math.round(f.weight * 100);
      const isNegative = f.factor.includes('Elevation');
      const fillClass = isNegative ? 'fill-success' : (pct > 30 ? 'fill-danger' : 'fill-warning');
      
      item.innerHTML = `
        <div class="factor-info">
          <span>${f.factor}</span>
          <strong class="mono ${isNegative ? 'text-success' : 'text-danger'}">${isNegative ? '-' : '+'}${pct}%</strong>
        </div>
        <div class="progress-track"><div class="progress-fill ${fillClass}" style="width: ${pct}%;"></div></div>
      `;
      factorsList.appendChild(item);
    });

    // 4. Recommendation Directive
    document.getElementById('recommendationText').textContent = data.action_recommendation;

    showToast(`ML Inference: ${data.risk_level} Risk (${probPct.toFixed(1)}%)`, 'info');

  } catch (err) {
    console.error('Prediction error:', err);
    showToast('ML inference service error', 'error');
  } finally {
    if (btn) btn.disabled = false;
  }
}

// Preset Handlers for ML Predictor
function setPredictionPresets(preset) {
  if (preset === 'high') {
    document.getElementById('predRainfall').value = '290.0';
    document.getElementById('predRiverDischarge').value = '2450.0';
    document.getElementById('predWaterLevel').value = '3.8';
    document.getElementById('predElevation').value = '12.0';
    document.getElementById('predLandCover').value = 'Urban';
    document.getElementById('predSoilType').value = 'Alluvial';
    document.getElementById('predInfrastructure').value = 'Poor';
    document.getElementById('predHistoricalFloods').value = '5';
  } else if (preset === 'med') {
    document.getElementById('predRainfall').value = '140.0';
    document.getElementById('predRiverDischarge').value = '1100.0';
    document.getElementById('predWaterLevel').value = '1.8';
    document.getElementById('predElevation').value = '35.0';
    document.getElementById('predLandCover').value = 'Agricultural';
    document.getElementById('predSoilType').value = 'Clayey';
    document.getElementById('predInfrastructure').value = 'Moderate';
    document.getElementById('predHistoricalFloods').value = '2';
  } else if (preset === 'low') {
    document.getElementById('predRainfall').value = '8.0';
    document.getElementById('predRiverDischarge').value = '120.0';
    document.getElementById('predWaterLevel').value = '0.35';
    document.getElementById('predElevation').value = '340.0';
    document.getElementById('predLandCover').value = 'Forest';
    document.getElementById('predSoilType').value = 'Sandy_Loam';
    document.getElementById('predInfrastructure').value = 'Good';
    document.getElementById('predHistoricalFloods').value = '0';
  }
  runFloodRiskPrediction();
}

// ============================================================================
// VR DISASTER TRAINING SIMULATION SANDBOX & 8-VECTOR SCORING
// ============================================================================
function initVRSimulation() {
  const canvas = document.getElementById('vrSimulationCanvas');
  if (!canvas) return;

  // Keyboard navigation on canvas
  window.addEventListener('keydown', (e) => {
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'w', 'a', 's', 'd', 'W', 'A', 'S', 'D'].includes(e.key)) {
      STATE.vr.keys[e.key.toLowerCase()] = true;
      e.preventDefault();
    }
  });

  window.addEventListener('keyup', (e) => {
    if (STATE.vr.keys[e.key.toLowerCase()]) {
      STATE.vr.keys[e.key.toLowerCase()] = false;
    }
  });

  // Start animation loop
  requestAnimationFrame(vrAnimationLoop);

  // Initialize Radar Chart
  initRadarChart();
}

function vrAnimationLoop() {
  updateVRSimulation();
  renderVRSimulation();
  requestAnimationFrame(vrAnimationLoop);
}

function updateVRSimulation() {
  const t = STATE.vr.trainee;
  const speed = t.speed;

  // Manual Keyboard Control
  if (STATE.vr.keys['arrowup'] || STATE.vr.keys['w']) t.y = Math.max(30, t.y - speed);
  if (STATE.vr.keys['arrowdown'] || STATE.vr.keys['s']) t.y = Math.min(390, t.y + speed);
  if (STATE.vr.keys['arrowleft'] || STATE.vr.keys['a']) t.x = Math.max(30, t.x - speed);
  if (STATE.vr.keys['arrowright'] || STATE.vr.keys['d']) t.x = Math.min(730, t.x + speed);

  // Automated drill mode
  if (STATE.vr.autoPlaying) {
    const unrescued = STATE.vr.victims.find(v => !v.rescued);
    let target = unrescued ? { x: unrescued.x, y: unrescued.y } : { x: STATE.vr.shelterZone.x + 40, y: STATE.vr.shelterZone.y + 40 };
    
    const dx = target.x - t.x;
    const dy = target.y - t.y;
    const dist = Math.sqrt(dx * dx + dy * dy);

    if (dist > 4) {
      // Avoid electrical hazard if no probe
      const h = STATE.vr.hazards[0];
      const hdx = t.x - h.x;
      const hdy = t.y - h.y;
      const hdist = Math.sqrt(hdx * hdx + hdy * hdy);
      
      let stepX = (dx / dist) * (speed * 0.9);
      let stepY = (dy / dist) * (speed * 0.9);

      if (hdist < 60 && t.tool !== 'Insulated Probe') {
        // Push outward around hazard
        stepY -= 1.5;
      }

      t.x += stepX;
      t.y += stepY;
    }
  }

  // Check victim rescues
  STATE.vr.victims.forEach(v => {
    if (!v.rescued) {
      const d = Math.sqrt((t.x - v.x) ** 2 + (t.y - v.y) ** 2);
      if (d < 24) {
        v.rescued = true;
        showToast(`Victim Secured: ${v.name}!`, 'success');
        speakInstructorDirective(`Victim secured. Commencing medical triage.`);
        recordTelemetryEvent('VICTIM_RESCUE', v.name);
      }
    }
  });

  // Calculate proximity to nearest hazard
  let minHazardDist = 999;
  let nearestHazard = null;
  STATE.vr.hazards.forEach(h => {
    const d = Math.sqrt((t.x - h.x) ** 2 + (t.y - h.y) ** 2) - (h.radius / 2);
    if (d < minHazardDist) {
      minHazardDist = d;
      nearestHazard = h;
    }
  });

  document.getElementById('vrHudHazardDist').textContent = `${Math.max(1, Math.round(minHazardDist * 0.3))} m`;
  const rescuedCount = STATE.vr.victims.filter(v => v.rescued).length;
  document.getElementById('vrHudVictims').textContent = `${rescuedCount} / ${STATE.vr.victims.length}`;

  // Callout warning trigger
  const callout = document.getElementById('vrUrgentCallout');
  if (minHazardDist < 35 && nearestHazard && nearestHazard.type === 'ELECTRICAL') {
    callout.style.display = 'flex';
    if (t.tool !== 'Insulated Probe') {
      speakInstructorDirective('Electrical hazard ahead. Maintain 10 meter standoff or equip insulated probe.');
    }
  } else {
    callout.style.display = 'none';
  }
}

function renderVRSimulation() {
  const canvas = document.getElementById('vrSimulationCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  // Background Terrain
  ctx.fillStyle = '#0B111E';
  ctx.fillRect(0, 0, w, h);

  // Grid Lines
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
  ctx.lineWidth = 1;
  for (let x = 0; x < w; x += 40) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, h);
    ctx.stroke();
  }
  for (let y = 0; y < h; y += 40) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }

  // Water Inundation Flow (Simulated moving waves)
  const time = Date.now() * 0.002;
  ctx.fillStyle = 'rgba(6, 182, 212, 0.14)';
  ctx.beginPath();
  ctx.moveTo(0, h);
  for (let x = 0; x <= w; x += 20) {
    const waveY = h - 220 + Math.sin(x * 0.015 + time) * 12;
    ctx.lineTo(x, waveY);
  }
  ctx.lineTo(w, h);
  ctx.closePath();
  ctx.fill();

  // High Elevation Shelter Safe Zone
  const s = STATE.vr.shelterZone;
  ctx.fillStyle = 'rgba(16, 185, 129, 0.18)';
  ctx.strokeStyle = '#10B981';
  ctx.lineWidth = 2;
  ctx.strokeRect(s.x, s.y, s.width, s.height);
  ctx.fillRect(s.x, s.y, s.width, s.height);
  ctx.fillStyle = '#6EE7B7';
  ctx.font = 'bold 10px Inter';
  ctx.fillText('ELEVATED SHELTER', s.x + 4, s.y + 20);

  // Hazards
  STATE.vr.hazards.forEach(hz => {
    ctx.beginPath();
    ctx.arc(hz.x, hz.y, hz.radius, 0, Math.PI * 2);
    ctx.fillStyle = hz.type === 'ELECTRICAL' ? 'rgba(239, 68, 68, 0.22)' : 'rgba(245, 158, 11, 0.22)';
    ctx.fill();
    ctx.strokeStyle = hz.type === 'ELECTRICAL' ? '#EF4444' : '#F59E0B';
    ctx.setLineDash([4, 4]);
    ctx.stroke();
    ctx.setLineDash([]);

    // Icon / Arcing
    if (hz.type === 'ELECTRICAL') {
      ctx.fillStyle = '#EF4444';
      ctx.beginPath();
      ctx.arc(hz.x, hz.y, 8, 0, Math.PI * 2);
      ctx.fill();
      // Spark spark
      ctx.strokeStyle = '#FCA5A5';
      ctx.beginPath();
      ctx.moveTo(hz.x - 10, hz.y);
      ctx.lineTo(hz.x + 10, hz.y + (Math.sin(time * 5) * 6));
      ctx.stroke();
    }
  });

  // Victims
  STATE.vr.victims.forEach(v => {
    if (!v.rescued) {
      ctx.beginPath();
      ctx.arc(v.x, v.y, 10, 0, Math.PI * 2);
      ctx.fillStyle = v.color;
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.fillStyle = '#F8FAFC';
      ctx.font = '10px Inter';
      ctx.fillText(v.name, v.x - 20, v.y - 14);
    }
  });

  // Trainee Avatar
  const t = STATE.vr.trainee;
  ctx.beginPath();
  ctx.arc(t.x, t.y, 12, 0, Math.PI * 2);
  ctx.fillStyle = '#38BDF8';
  ctx.fill();
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 2;
  ctx.stroke();

  // Glow ring
  ctx.beginPath();
  ctx.arc(t.x, t.y, 18, 0, Math.PI * 2);
  ctx.strokeStyle = 'rgba(56, 189, 248, 0.5)';
  ctx.stroke();

  // Tool label above trainee
  ctx.fillStyle = '#E2E8F0';
  ctx.font = '9.5px JetBrains Mono';
  ctx.fillText(t.tool, t.x - 20, t.y + 24);
}

function recordTelemetryEvent(action, target) {
  STATE.vr.telemetryStream.push({
    timestamp_sec: STATE.vr.elapsedSec,
    position_x: STATE.vr.trainee.x,
    position_y: STATE.vr.trainee.y,
    position_z: 0.0,
    speed: STATE.vr.trainee.speed,
    action_type: action,
    target_entity: target,
    tool_in_hand: STATE.vr.trainee.tool,
    hazard_proximity_m: 8.5
  });
}

// 8-Vector Spider / Radar Chart
function initRadarChart() {
  const canvas = document.getElementById('competencyRadarChart');
  if (!canvas) return;

  const labels = [
    'Safety Awareness (25%)',
    'Rescue Effectiveness (20%)',
    'Decision Quality (20%)',
    'Route Efficiency (10%)',
    'Response Time (10%)',
    'Communication (5%)',
    'Tool Usage (5%)',
    'Adaptability (5%)'
  ];

  STATE.radarChart = new Chart(canvas, {
    type: 'radar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Trainee Competency Score',
        data: [88, 95, 84, 82, 80, 75, 90, 85],
        backgroundColor: 'rgba(6, 182, 212, 0.25)',
        borderColor: '#06B6D4',
        borderWidth: 2,
        pointBackgroundColor: '#38BDF8',
        pointBorderColor: '#ffffff',
        pointHoverBackgroundColor: '#ffffff',
        pointHoverBorderColor: '#38BDF8'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          angleLines: { color: 'rgba(255, 255, 255, 0.08)' },
          grid: { color: 'rgba(255, 255, 255, 0.08)' },
          pointLabels: {
            color: '#94A3B8',
            font: { family: 'Inter', size: 10.5 }
          },
          suggestedMin: 40,
          suggestedMax: 100,
          ticks: {
            backdropColor: 'transparent',
            color: '#64748B',
            stepSize: 20
          }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}

// Evaluate Trainee Telemetry
async function evaluateVRTelemetry() {
  const btn = document.getElementById('btnEvaluateTelemetry');
  if (btn) btn.disabled = true;

  try {
    const payload = {
      session_id: `sess-${Date.now().toString().slice(-6)}`,
      trainee_id: 'trainee-rahul-09',
      scenario_id: document.getElementById('vrScenarioSelect').value,
      scenario_title: 'Brahmaputra Lowlands Urban Deluge & Substation Isolation',
      difficulty: 'MEDIUM',
      total_duration_seconds: 240.0,
      victims_total: 4,
      victims_rescued: 4,
      hazards_triggered: 0,
      telemetry_stream: [
        { timestamp_sec: 10.0, position_x: 0.0, position_y: 0.0, position_z: 0.0, speed: 1.2, action_type: "MOVE", hazard_proximity_m: 14.0 },
        { timestamp_sec: 45.0, position_x: 25.0, position_y: 0.0, position_z: 30.0, speed: 0.5, action_type: "TOOL_EQUIP", tool_in_hand: STATE.vr.trainee.tool, hazard_proximity_m: 8.5 },
        { timestamp_sec: 90.0, position_x: 50.0, position_y: 0.0, position_z: 60.0, speed: 0.0, action_type: "VICTIM_TRIAGE", target_entity: "Victim 1 (Child)" },
        { timestamp_sec: 130.0, position_x: 55.0, position_y: 0.0, position_z: 65.0, speed: 1.0, action_type: "VICTIM_RESCUE", target_entity: "Victim 1 (Child)" },
        { timestamp_sec: 170.0, position_x: 75.0, position_y: 0.0, position_z: 80.0, speed: 1.1, action_type: "RADIO_CALL", notes: "Convoy status clear" },
        { timestamp_sec: 230.0, position_x: 100.0, position_y: 0.0, position_z: 110.0, speed: 1.0, action_type: "ROUTE_CHOICE", target_entity: "North High Ridge" }
      ]
    };

    const res = await fetch(`${STATE.apiBase}/api/v1/vr/telemetry-evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    // 1. Update Radar Chart
    const s = data.competency_scores;
    if (STATE.radarChart) {
      STATE.radarChart.data.datasets[0].data = [
        s.safety_awareness,
        s.rescue_effectiveness,
        s.decision_quality,
        s.route_efficiency,
        s.response_time,
        s.communication,
        s.tool_usage,
        s.adaptability
      ];
      STATE.radarChart.update();
    }

    // 2. Update Overall Score & Tier
    document.getElementById('overallScoreVal').textContent = data.overall_score.toFixed(1);
    document.getElementById('tierNameBadge').textContent = data.performance_tier;

    // 3. Update Strengths & Weaknesses
    const strengthsList = document.getElementById('strengthsList');
    strengthsList.innerHTML = '';
    data.strengths.forEach(st => {
      const li = document.createElement('li');
      li.innerHTML = `<i class="fa-solid fa-check text-success"></i> ${st}`;
      strengthsList.appendChild(li);
    });

    const weaknessesList = document.getElementById('weaknessesList');
    weaknessesList.innerHTML = '';
    data.weaknesses.forEach(w => {
      const li = document.createElement('li');
      li.innerHTML = `<i class="fa-solid fa-exclamation text-amber"></i> ${w}`;
      weaknessesList.appendChild(li);
    });

    // 4. Update Adaptive Curriculum
    const curr = data.next_training_recommendation;
    if (curr) {
      document.getElementById('currScenarioTitle').textContent = curr.recommended_scenario_title || curr.scenario_id;
      document.getElementById('currDifficulty').textContent = curr.difficulty;
      document.getElementById('currDescription').textContent = curr.rationale;
      document.getElementById('currFocusObjectives').innerHTML = `<strong>Focus Objectives:</strong> ${curr.focus_skills ? curr.focus_skills.join(', ') : 'Hazard isolation and rapid extraction.'}`;
    }

    showToast(`VR Telemetry Evaluated: Overall Score ${data.overall_score.toFixed(1)}/100`, 'success');

  } catch (err) {
    console.error('VR Telemetry Eval Error:', err);
    showToast('Failed to evaluate VR session telemetry', 'error');
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ============================================================================
// AI VIRTUAL INSTRUCTOR & SPEECH SYNTHESIS
// ============================================================================
function initSpeechSynthesis() {
  const chk = document.getElementById('chkSpeechSynthesis');
  if (chk) {
    chk.addEventListener('change', (e) => {
      STATE.speechEnabled = e.target.checked;
    });
  }
}

function speakInstructorDirective(text) {
  if (!STATE.speechEnabled || !window.speechSynthesis) return;
  if (text === STATE.lastSpokenMessage) return;

  STATE.lastSpokenMessage = text;
  window.speechSynthesis.cancel(); // Cancel backlog
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.05;
  utterance.pitch = 0.95;
  window.speechSynthesis.speak(utterance);
}

async function testVirtualInstructor() {
  const btn = document.getElementById('btnTestInstructor');
  if (btn) btn.disabled = true;

  try {
    const hazardType = document.getElementById('instHazardType').value;
    const hazardDist = parseFloat(document.getElementById('instHazardDist').value);
    const waterLevel = parseFloat(document.getElementById('instWaterLevel').value);
    const waterRise = parseFloat(document.getElementById('instWaterRiseRate').value) / 100.0;
    const tool = document.getElementById('instTool').value;
    const victimPriority = document.getElementById('instVictimPriority').value;

    const payload = {
      user_position: { x: 10.0, y: 0.0, z: 15.0 },
      current_zone_id: 'Zone_A',
      water_level_m: waterLevel,
      water_level_rate_m_per_min: waterRise,
      nearest_hazard_type: hazardType === 'None' ? null : hazardType,
      nearest_hazard_dist_m: hazardType === 'None' ? null : hazardDist,
      equipped_tool: tool,
      nearby_victim_priority: victimPriority === 'None' ? null : victimPriority,
      nearby_victim_dist_m: victimPriority === 'None' ? null : 12.0
    };

    const res = await fetch(`${STATE.apiBase}/api/v1/vr/virtual-instructor/guidance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const prompts = await res.json();

    if (prompts.length > 0) {
      const topPrompt = prompts[0];
      
      // Update Spotlight
      document.getElementById('spotlightPriority').textContent = topPrompt.priority;
      document.getElementById('spotlightPriority').className = 'spotlight-priority-tag ' + (topPrompt.priority.includes('CRITICAL') ? 'tag-critical' : 'tag-warning');
      document.getElementById('spotlightSop').textContent = topPrompt.safety_rule_code;
      document.getElementById('spotlightHeadline').textContent = topPrompt.headline;
      document.getElementById('spotlightMessage').textContent = topPrompt.message;
      document.getElementById('spotlightAction').textContent = topPrompt.suggested_action;

      // Speak directive
      speakInstructorDirective(`${topPrompt.headline}. ${topPrompt.suggested_action}`);

      // Append to list
      const list = document.getElementById('promptStreamList');
      list.innerHTML = '';
      prompts.forEach(p => {
        const card = document.createElement('div');
        card.className = 'prompt-card';
        card.innerHTML = `
          <div class="prompt-card-top">
            <span class="prompt-card-title">${p.headline}</span>
            <span class="badge-tag ${p.priority.includes('CRITICAL') ? 'tag-critical' : 'tag-warning'}">${p.priority}</span>
          </div>
          <div class="prompt-card-body">${p.message}</div>
          <div class="prompt-card-action"><strong>Mandate:</strong> ${p.suggested_action}</div>
        `;
        list.appendChild(card);
      });

      showToast(`Instructor SOP Triggered: ${topPrompt.headline}`, 'info');
    }

  } catch (err) {
    console.error('Virtual instructor error:', err);
    showToast('Failed to evaluate virtual instructor guidance', 'error');
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ============================================================================
// HAZARDS, SHELTERS & ALERTS MANAGEMENT
// ============================================================================
function renderHazardsTable() {
  const tbody = document.getElementById('hazardsTbody');
  if (!tbody) return;
  tbody.innerHTML = '';

  STATE.hazards.forEach(h => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="mono">${h.id}</td>
      <td><span class="badge-tag ${h.type === 'ELECTRICAL' ? 'tag-critical' : 'tag-warning'}">${h.type}</span></td>
      <td>${h.desc}</td>
      <td class="mono">${h.lat.toFixed(4)}, ${h.lng.toFixed(4)}</td>
      <td>${h.radius_m} m</td>
      <td>${h.severity}x</td>
      <td>
        <button class="btn-action-delete" onclick="window.deleteHazard('${h.id}')">
          <i class="fa-solid fa-trash"></i> Clear
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

window.deleteHazard = async function(hazardId) {
  try {
    const res = await fetch(`${STATE.apiBase}/api/v1/hazards/${hazardId}`, { method: 'DELETE' });
    if (res.ok) {
      showToast(`Hazard ${hazardId} cleared from navigation mesh!`, 'success');
      await refreshDynamicData();
      await calculateSafeRoute();
    }
  } catch (e) {
    showToast('Failed to delete hazard', 'error');
  }
};

function renderSheltersCards() {
  const grid = document.getElementById('sheltersCardGrid');
  if (!grid) return;
  grid.innerHTML = '';

  STATE.shelters.forEach(s => {
    const occPct = Math.round((s.occupancy / s.capacity) * 100);
    const card = document.createElement('div');
    card.className = 'shelter-card';
    card.innerHTML = `
      <div class="shelter-card-top">
        <div class="shelter-name">${s.name}</div>
        <span class="shelter-elev"><i class="fa-solid fa-mountain"></i> ${s.elevation}m ASL</span>
      </div>
      <div class="shelter-occupancy-info">
        <span>Capacity: ${s.occupancy} / ${s.capacity}</span>
        <strong>${occPct}% Occupied</strong>
      </div>
      <div class="progress-track"><div class="progress-fill fill-success" style="width: ${occPct}%;"></div></div>
      <div class="shelter-actions">
        <button class="btn-compact" onclick="window.selectShelterDestination('${s.id}')">
          <i class="fa-solid fa-location-arrow"></i> Evacuate to this Shelter
        </button>
      </div>
    `;
    grid.appendChild(card);
  });
}

function renderAlerts() {
  // Update Ticker
  const tickerText = document.getElementById('tickerText');
  if (tickerText && STATE.alerts.length > 0) {
    tickerText.textContent = STATE.alerts.map(a => `[${a.region}] ${a.title}: ${a.message}`).join('  ✦  ');
  }

  // Update List in Hazards Tab
  const list = document.getElementById('broadcastAlertsList');
  if (!list) return;
  list.innerHTML = '';

  STATE.alerts.forEach(a => {
    const card = document.createElement('div');
    card.className = 'broadcast-alert-card';
    card.innerHTML = `
      <div class="alert-top-row">
        <span class="alert-title-text"><i class="fa-solid fa-triangle-exclamation"></i> ${a.title}</span>
        <span class="alert-meta mono">${a.broadcast_time || 'ACTIVE'}</span>
      </div>
      <div class="alert-body-text">${a.message}</div>
      <div class="alert-footer-tags">
        <span><i class="fa-solid fa-location-dot"></i> ${a.region}</span>
        <span><i class="fa-solid fa-shield-halved"></i> Issued by: ${a.issued_by}</span>
      </div>
    `;
    list.appendChild(card);
  });
}

function renderZonesCards() {
  const grid = document.getElementById('zonesCardGrid');
  if (!grid) return;
  grid.innerHTML = '';

  STATE.zones.forEach(z => {
    const card = document.createElement('div');
    card.className = 'zone-card';
    card.innerHTML = `
      <div class="zone-card-header">
        <div>
          <div class="zone-name">${z.name}</div>
          <div class="zone-state">${z.state} Basin</div>
        </div>
        <button class="btn-compact" onclick="window.focusZoneOnMap(${z.center_lat}, ${z.center_lng})">
          <i class="fa-solid fa-eye"></i> View on Map
        </button>
      </div>
      <div class="zone-metrics-grid">
        <div class="zone-metric-item">
          <div class="zone-metric-label">River Stage</div>
          <div class="zone-metric-val text-cyan">${z.water_level} m</div>
        </div>
        <div class="zone-metric-item">
          <div class="zone-metric-label">Discharge Rate</div>
          <div class="zone-metric-val text-danger">${z.discharge} m³/s</div>
        </div>
        <div class="zone-metric-item">
          <div class="zone-metric-label">24h Rainfall</div>
          <div class="zone-metric-val text-amber">${z.baseline_rain} mm</div>
        </div>
        <div class="zone-metric-item">
          <div class="zone-metric-label">Elevation</div>
          <div class="zone-metric-val">${z.elevation} m ASL</div>
        </div>
      </div>
    `;
    grid.appendChild(card);
  });
}

window.focusZoneOnMap = function(lat, lng) {
  switchTab('tab-map');
  setOriginCoords(lat, lng);
  if (STATE.map) {
    STATE.map.setView([lat, lng], 13);
  }
};

// ============================================================================
// MODALS MANAGEMENT
// ============================================================================
function initModals() {
  // Hazard Modal
  const btnOpenHazard = document.getElementById('btnOpenHazardModal');
  const modalHazard = document.getElementById('hazardModal');
  const btnCloseHazard = document.getElementById('btnCloseHazardModal');
  const btnCancelHazard = document.getElementById('btnCancelHazardModal');

  if (btnOpenHazard) btnOpenHazard.addEventListener('click', () => modalHazard.style.display = 'flex');
  if (btnCloseHazard) btnCloseHazard.addEventListener('click', () => modalHazard.style.display = 'none');
  if (btnCancelHazard) btnCancelHazard.addEventListener('click', () => modalHazard.style.display = 'none');

  const formHazard = document.getElementById('newHazardForm');
  if (formHazard) {
    formHazard.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        hazard_type: document.getElementById('newHazardType').value,
        latitude: parseFloat(document.getElementById('newHazardLat').value),
        longitude: parseFloat(document.getElementById('newHazardLng').value),
        radius_meters: parseFloat(document.getElementById('newHazardRadius').value),
        severity: parseFloat(document.getElementById('newHazardSeverity').value),
        description: document.getElementById('newHazardDesc').value
      };

      try {
        const res = await fetch(`${STATE.apiBase}/api/v1/hazards`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          modalHazard.style.display = 'none';
          showToast('Hazard reported! Navigation mesh dynamically recalculated.', 'success');
          await refreshDynamicData();
          await calculateSafeRoute();
        }
      } catch (err) {
        showToast('Error submitting hazard', 'error');
      }
    });
  }

  // Alert Modal
  const modalAlert = document.getElementById('alertModal');
  const btnOpenAlert = document.getElementById('btnOpenAlertModal');
  const btnOpenAlert2 = document.getElementById('btnOpenAlertModal2');
  const btnCloseAlert = document.getElementById('btnCloseAlertModal');
  const btnCancelAlert = document.getElementById('btnCancelAlertModal');

  const openAlert = () => modalAlert.style.display = 'flex';
  const closeAlert = () => modalAlert.style.display = 'none';

  if (btnOpenAlert) btnOpenAlert.addEventListener('click', openAlert);
  if (btnOpenAlert2) btnOpenAlert2.addEventListener('click', openAlert);
  if (btnCloseAlert) btnCloseAlert.addEventListener('click', closeAlert);
  if (btnCancelAlert) btnCancelAlert.addEventListener('click', closeAlert);

  const formAlert = document.getElementById('newAlertForm');
  if (formAlert) {
    formAlert.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        title: document.getElementById('newAlertTitle').value,
        message: document.getElementById('newAlertMessage').value,
        severity: document.getElementById('newAlertSeverity').value,
        region: document.getElementById('newAlertRegion').value,
        affected_lat: parseFloat(document.getElementById('newAlertLat').value),
        affected_lng: parseFloat(document.getElementById('newAlertLng').value),
        radius_km: parseFloat(document.getElementById('newAlertRadius').value),
        issued_by: 'NDRF Disaster Control Hub'
      };

      try {
        const res = await fetch(`${STATE.apiBase}/api/v1/alerts`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          modalAlert.style.display = 'none';
          showToast('Emergency alert broadcast across active disaster network!', 'success');
          await refreshDynamicData();
        }
      } catch (err) {
        showToast('Error broadcasting alert', 'error');
      }
    });
  }
}

// ============================================================================
// SLIDERS & EVENT HANDLERS
// ============================================================================
function initSliders() {
  const hazardRange = document.getElementById('hazardWeightRange');
  const valHazard = document.getElementById('valHazardWeight');
  if (hazardRange && valHazard) {
    hazardRange.addEventListener('input', (e) => valHazard.textContent = `${e.target.value}x`);
  }

  const floodRange = document.getElementById('floodWeightRange');
  const valFlood = document.getElementById('valFloodWeight');
  if (floodRange && valFlood) {
    floodRange.addEventListener('input', (e) => valFlood.textContent = `${e.target.value}x`);
  }

  const instDist = document.getElementById('instHazardDist');
  const valInstDist = document.getElementById('valInstHazardDist');
  if (instDist && valInstDist) {
    instDist.addEventListener('input', (e) => valInstDist.textContent = `${e.target.value} m`);
  }

  const instWater = document.getElementById('instWaterLevel');
  const valInstWater = document.getElementById('valInstWaterLevel');
  if (instWater && valInstWater) {
    instWater.addEventListener('input', (e) => valInstWater.textContent = `${e.target.value} m`);
  }

  const instWaterRate = document.getElementById('instWaterRiseRate');
  const valInstWaterRate = document.getElementById('valInstWaterRate');
  if (instWaterRate && valInstWaterRate) {
    instWaterRate.addEventListener('input', (e) => valInstWaterRate.textContent = `${e.target.value} cm/min`);
  }
}

function setupEventHandlers() {
  // Safe route button
  const btnRoute = document.getElementById('btnCalculateSafeRoute');
  if (btnRoute) btnRoute.addEventListener('click', calculateSafeRoute);

  // Full location analysis button
  const btnLoc = document.getElementById('btnAnalyzeLiveLocation');
  if (btnLoc) btnLoc.addEventListener('click', runLocationAnalysis);

  // ML Predict button
  const btnPred = document.getElementById('btnRunPrediction');
  if (btnPred) btnPred.addEventListener('click', runFloodRiskPrediction);

  // Presets
  const pHigh = document.getElementById('presetHighRisk');
  if (pHigh) pHigh.addEventListener('click', () => setPredictionPresets('high'));
  const pMed = document.getElementById('presetMedRisk');
  if (pMed) pMed.addEventListener('click', () => setPredictionPresets('med'));
  const pLow = document.getElementById('presetLowRisk');
  if (pLow) pLow.addEventListener('click', () => setPredictionPresets('low'));

  // Quick broadcast button from ML recommendation
  const btnPredAlert = document.getElementById('btnPublishAlertFromPrediction');
  if (btnPredAlert) {
    btnPredAlert.addEventListener('click', () => {
      document.getElementById('newAlertTitle').value = 'Immediate Flood Surge Warning';
      document.getElementById('newAlertMessage').value = document.getElementById('recommendationText').textContent;
      document.getElementById('alertModal').style.display = 'flex';
    });
  }

  // VR Tool Selection
  const toolBtns = document.querySelectorAll('.btn-tool');
  toolBtns.forEach(b => {
    b.addEventListener('click', () => {
      toolBtns.forEach(btn => btn.classList.remove('active'));
      b.classList.add('active');
      STATE.vr.trainee.tool = b.getAttribute('data-tool');
      showToast(`Equipped tool: ${STATE.vr.trainee.tool}`, 'info');
    });
  });

  // VR Auto Play / Reset / Evaluate
  const btnSimAuto = document.getElementById('btnSimRunAuto');
  if (btnSimAuto) {
    btnSimAuto.addEventListener('click', () => {
      STATE.vr.autoPlaying = !STATE.vr.autoPlaying;
      btnSimAuto.innerHTML = STATE.vr.autoPlaying ? '<i class="fa-solid fa-pause"></i> Pause Drill' : '<i class="fa-solid fa-play"></i> Auto Run Simulation';
    });
  }

  const btnSimReset = document.getElementById('btnSimReset');
  if (btnSimReset) {
    btnSimReset.addEventListener('click', () => {
      STATE.vr.autoPlaying = false;
      STATE.vr.trainee.x = 80;
      STATE.vr.trainee.y = 340;
      STATE.vr.victims.forEach(v => v.rescued = false);
      btnSimAuto.innerHTML = '<i class="fa-solid fa-play"></i> Auto Run Simulation';
      showToast('VR drill reset', 'info');
    });
  }

  const btnEval = document.getElementById('btnEvaluateTelemetry');
  if (btnEval) btnEval.addEventListener('click', evaluateVRTelemetry);

  // Virtual Instructor tester
  const btnInst = document.getElementById('btnTestInstructor');
  if (btnInst) btnInst.addEventListener('click', testVirtualInstructor);

  // Map zone selector
  const mapZoneSel = document.getElementById('mapZoneSelector');
  if (mapZoneSel) {
    mapZoneSel.addEventListener('change', (e) => {
      const val = e.target.value;
      if (val === 'all' && STATE.map) {
        STATE.map.setView([22.5937, 78.9629], 5);
      } else {
        const zone = STATE.zones.find(z => z.id === val);
        if (zone) {
          window.focusZoneOnMap(zone.center_lat, zone.center_lng);
        }
      }
    });
  }

  const btnResetMap = document.getElementById('btnResetMap');
  if (btnResetMap && STATE.map) {
    btnResetMap.addEventListener('click', () => {
      STATE.map.setView([STATE.originCoords.lat, STATE.originCoords.lng], 13);
    });
  }
}

// ============================================================================
// TOAST NOTIFICATIONS
// ============================================================================
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const icon = type === 'success' ? 'fa-circle-check' : (type === 'error' ? 'fa-circle-xmark' : 'fa-circle-info');
  toast.innerHTML = `<i class="fa-solid ${icon}"></i><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
