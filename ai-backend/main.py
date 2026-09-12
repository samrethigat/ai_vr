"""
AI-Powered Smart Flood Disaster Response, VR Training and Live Location Guidance System
FastAPI Backend Application Server
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

# Ensure ai-backend directory is in Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

from prediction.predictor import predictor, FloodPredictionInput, FloodPredictionResult
from routing.safe_route_engine import route_engine, SafeRouteRequest, SafeRouteResponse, haversine_km
from scoring.telemetry_analyzer import telemetry_analyzer, VrSessionEvaluationRequest, VrSessionEvaluationResult, CompetencyVector
from services.virtual_instructor import virtual_instructor, InstructorGuidanceRequest, InstructorPrompt
from services.adaptive_learning import generate_adaptive_curriculum
from services.geo_service import geo_service, LocationAnalysisRequest, LocationAnalysisResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FloodVR-Backend")

app = FastAPI(
    title="AI Flood Disaster Response & VR Training Platform",
    description="Intelligent flood risk prediction, A*/Dijkstra hazard-avoiding safe navigation, VR 8-vector competency evaluation, and real-time AI Virtual Instructor guidance.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for local frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for active disaster alerts
ACTIVE_ALERTS = [
    {
        "id": "alt-01",
        "title": "Severe Flash Flood & Inundation Warning",
        "message": "Water levels in Brahmaputra basin exceeding danger threshold (54.2m). Low-lying sectors evacuate immediately via marked green elevation corridors.",
        "severity": "CRITICAL_EMERGENCY",
        "region": "Guwahati Brahmaputra Lowlands (Zone A)",
        "affected_lat": 26.1722,
        "affected_lng": 91.7458,
        "radius_km": 15.0,
        "issued_by": "National Disaster Response Force (NDRF)",
        "broadcast_time": "2026-09-02T05:30:00Z"
    },
    {
        "id": "alt-02",
        "title": "Periyar River Surge Watch",
        "message": "Dam discharge raised to 1450 m³/s. Standby advisory for Aluva-Ernakulam riverbank settlements.",
        "severity": "WARNING",
        "region": "Ernakulam-Aluva Periyar Lowlands (Zone B)",
        "affected_lat": 9.9816,
        "affected_lng": 76.2999,
        "radius_km": 10.0,
        "issued_by": "Kerala State Disaster Management Authority",
        "broadcast_time": "2026-09-02T05:00:00Z"
    }
]

# Available VR Scenarios
VR_SCENARIOS = [
    {
        "scenario_id": "SCEN_URBAN_DELUGE_01",
        "title": "Brahmaputra Lowlands Urban Deluge & Substation Isolation",
        "region": "Guwahati, Assam",
        "difficulty": "MEDIUM",
        "description": "Rapidly rising water (+5cm/min) in dense urban grid. Trainee must locate 4 stranded citizens, isolate submerged 11kV transformer hazard, and navigate to NDRF Elevated Shelter.",
        "victim_count": 4,
        "hazard_count": 3,
        "time_limit_sec": 360,
        "recommended_tools": ["Insulated Probe", "Life Jacket", "Medical Triage Kit", "Rescue Boat"]
    },
    {
        "scenario_id": "SCEN_COASTAL_SURGE_02",
        "title": "Periyar Flash Inundation & Night Convoy Evacuation",
        "region": "Aluva, Kerala",
        "difficulty": "HARD",
        "description": "Night-time emergency evacuation with reduced visibility, fallen trees blocking NH-544 arterial roads, and water currents reaching 2.5 m/s.",
        "victim_count": 6,
        "hazard_count": 4,
        "time_limit_sec": 420,
        "recommended_tools": ["High-Lumen Flashlight", "Tow Winch", "Emergency Radio", "Inflatable Raft"]
    },
    {
        "scenario_id": "SCEN_EXTREME_MULTI_HAZARD",
        "title": "Brahmaputra Dam Spillway Breach & Extreme Urban Deluge",
        "region": "Guwahati Basin, Assam",
        "difficulty": "EXTREME",
        "description": "Catastrophic multi-hazard crisis with live high-voltage arcing, river velocities >3.8 m/s, and mass casualty triage.",
        "victim_count": 8,
        "hazard_count": 5,
        "time_limit_sec": 300,
        "recommended_tools": ["All Equipment Unlocked"]
    },
    {
        "scenario_id": "SCEN_HAZARD_AWARENESS_REPLAY",
        "title": "Hazard Awareness & Submerged Utility Isolation",
        "region": "Patna Lowlands, Bihar",
        "difficulty": "EASY",
        "description": "Guided remedial scenario focusing on perimeter safety, utility identification, and zero-encroachment navigation.",
        "victim_count": 2,
        "hazard_count": 4,
        "time_limit_sec": 420,
        "recommended_tools": ["Insulated Probe", "High-Visibility Beacon"]
    }
]


class HazardInput(BaseModel):
    hazard_type: str = Field(..., description="ELECTRICAL, BLOCKED_ROAD, DEEP_WATER, FALLEN_TREE, BRIDGE_FAILURE")
    latitude: float
    longitude: float
    radius_meters: float = 60.0
    severity: float = 3.0
    description: str


class AlertInput(BaseModel):
    title: str
    message: str
    severity: str = "WARNING"
    region: str
    affected_lat: float
    affected_lng: float
    radius_km: float = 15.0
    issued_by: str = "NDRF Disaster Control Hub"


# ============================================================================
# 1. ROOT & HEALTH ENDPOINTS
# ============================================================================

@app.get("/", summary="System Root Info")
async def root(request: Request):
    accept = request.headers.get("accept", "")
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if "text/html" in accept and os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "system": "AI-Powered Smart Flood Disaster Response & VR Training System",
        "status": "OPERATIONAL",
        "version": "1.0.0",
        "model_ready": predictor.is_ready(),
        "active_hazards": len(route_engine.hazards),
        "shelters_online": len(route_engine.shelters),
        "monitored_zones": len(geo_service.flood_zones),
        "documentation": "/docs",
        "web_dashboard": "/app"
    }


@app.get("/health", summary="Health Check")
async def health_check():
    return {
        "status": "healthy",
        "ml_predictor": "ready" if predictor.is_ready() else "unloaded",
        "routing_engine": "online",
        "telemetry_analyzer": "online",
        "virtual_instructor": "online",
        "geo_service": "online"
    }


# ============================================================================
# 2. AI FLOOD RISK PREDICTION ENDPOINTS
# ============================================================================

@app.post("/api/v1/predict/flood-risk", response_model=FloodPredictionResult, summary="Predict Flood Probability & Risk Stratification")
async def predict_flood_risk(input_data: FloodPredictionInput):
    """
    Executes Machine Learning inference on hydrological, meteorological, and topographic parameters
    to calculate flood probability (0-1), risk tier (LOW, MEDIUM, HIGH), and recommended mitigation actions.
    """
    try:
        result = predictor.predict(input_data)
        return result
    except Exception as e:
        logger.error(f"Error in flood prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 3. SAFE EVACUATION ROUTE NAVIGATION (A* / DIJKSTRA)
# ============================================================================

@app.post("/api/v1/routing/safe-route", response_model=SafeRouteResponse, summary="Compute Hazard-Avoiding Safe Evacuation Route")
async def compute_safe_route(request: SafeRouteRequest):
    """
    Executes A* or Dijkstra graph traversal on the spatial navigation mesh.
    Applies real-time penalty multipliers for flood zones, rising water levels, and active hazards.
    Returns both the primary safest route and an alternative evacuation corridor.
    """
    try:
        response = route_engine.compute_safe_route(request)
        return response
    except Exception as e:
        logger.error(f"Error in safe route calculation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 4. GEOSPATIAL LOCATION ANALYSIS
# ============================================================================

@app.post("/api/v1/geo/location-analysis", response_model=LocationAnalysisResponse, summary="Analyze Live Location Against Flood Risk & Shelters")
async def analyze_location(request: LocationAnalysisRequest):
    """
    Provides comprehensive spatial analysis for a user's GPS coordinates:
    finds nearest flood zone, evaluates ML flood risk, queries nearby active hazards,
    and computes the fastest safe route to the nearest emergency shelter.
    """
    try:
        analysis = geo_service.analyze_location(request)
        return analysis
    except Exception as e:
        logger.error(f"Error in location analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 5. VR TELEMETRY EVALUATION & 8-VECTOR SCORING
# ============================================================================

@app.post("/api/v1/vr/telemetry-evaluate", response_model=VrSessionEvaluationResult, summary="Evaluate VR Session Telemetry & Compute 8 Competency Scores")
async def evaluate_vr_telemetry(session: VrSessionEvaluationRequest):
    """
    Processes fine-grained VR telemetry streams from Unity/WebXR simulation sessions.
    Evaluates the 8 competency vectors:
    - Safety Awareness (25%)
    - Rescue Effectiveness (20%)
    - Decision Quality (20%)
    - Route Efficiency (10%)
    - Response Time (10%)
    - Communication (5%)
    - Tool Usage (5%)
    - Adaptability (5%)
    
    Generates unsafe decision logs, strengths, weaknesses, and personalized adaptive next-curriculum.
    """
    try:
        result = telemetry_analyzer.analyze_session(session)
        return result
    except Exception as e:
        logger.error(f"Error in VR telemetry evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 6. DETERMINISTIC AI VIRTUAL INSTRUCTOR
# ============================================================================

@app.post("/api/v1/vr/virtual-instructor/guidance", response_model=List[InstructorPrompt], summary="Get Real-Time Virtual Instructor Guidance & Audio Cues")
async def get_instructor_guidance(request: InstructorGuidanceRequest):
    """
    Deterministic AI Virtual Instructor providing real-time disaster guidance and safety prompts.
    Evaluates distance to electrical powerlines, rising water rates, flooded corridors, and triage targets.
    """
    try:
        prompts = virtual_instructor.evaluate_live_guidance(request)
        return prompts
    except Exception as e:
        logger.error(f"Error in virtual instructor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 7. ADAPTIVE LEARNING & CURRICULUM GENERATION
# ============================================================================

@app.post("/api/v1/vr/adaptive-learning/curriculum", summary="Generate Adaptive Personalized Training Curriculum")
async def get_adaptive_curriculum(competencies: CompetencyVector, current_difficulty: str = Query(default="MEDIUM")):
    """
    Synthesizes tailored training progression based on competency weaknesses:
    - Safety < 60: Hazard Awareness Repetition
    - Rescue < 60: Focused Victim Rescue Scenario
    - Route < 60: Guided Safe Navigation
    - Response < 60: Timed Rapid-Extraction Drills
    - All >= 85: Extreme Multi-Hazard Escalation
    """
    try:
        curriculum = generate_adaptive_curriculum(competencies, current_difficulty)
        return curriculum
    except Exception as e:
        logger.error(f"Error generating adaptive curriculum: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 8. HAZARDS, SHELTERS, ZONES & ALERTS MANAGEMENT
# ============================================================================

@app.get("/api/v1/hazards", summary="List Active Environmental Hazards")
async def list_hazards():
    return {"hazards": route_engine.hazards}


@app.post("/api/v1/hazards", summary="Report New Environmental Hazard")
async def create_hazard(hazard: HazardInput):
    new_h = {
        "id": f"h{len(route_engine.hazards) + 1}",
        "type": hazard.hazard_type.upper(),
        "lat": hazard.latitude,
        "lng": hazard.longitude,
        "radius_m": hazard.radius_meters,
        "severity": hazard.severity,
        "desc": hazard.description
    }
    route_engine.hazards.append(new_h)
    return {"message": "Hazard reported and added to active navigation graph", "hazard": new_h}


@app.delete("/api/v1/hazards/{hazard_id}", summary="Clear / Resolve Hazard")
async def delete_hazard(hazard_id: str):
    initial_len = len(route_engine.hazards)
    route_engine.hazards = [h for h in route_engine.hazards if h["id"] != hazard_id]
    if len(route_engine.hazards) == initial_len:
        raise HTTPException(status_code=404, detail="Hazard ID not found")
    return {"message": f"Hazard {hazard_id} cleared from active graph"}


@app.get("/api/v1/shelters", summary="List Safe Shelters & Occupancies")
async def list_shelters():
    return {"shelters": route_engine.shelters}


@app.get("/api/v1/zones", summary="List Monitored Flood River Basins")
async def list_zones():
    return {"zones": geo_service.flood_zones}


@app.get("/api/v1/scenarios", summary="List VR Simulation Scenarios")
async def list_scenarios():
    return {"scenarios": VR_SCENARIOS}


@app.get("/api/v1/alerts", summary="List Active Disaster Broadcast Alerts")
async def list_alerts():
    return {"alerts": ACTIVE_ALERTS}


@app.post("/api/v1/alerts", summary="Broadcast New Emergency Alert")
async def broadcast_alert(alert: AlertInput):
    new_alert = {
        "id": f"alt-{len(ACTIVE_ALERTS) + 1:02d}",
        "title": alert.title,
        "message": alert.message,
        "severity": alert.severity,
        "region": alert.region,
        "affected_lat": alert.affected_lat,
        "affected_lng": alert.affected_lng,
        "radius_km": alert.radius_km,
        "issued_by": alert.issued_by,
        "broadcast_time": "2026-09-02T06:00:00Z"
    }
    ACTIVE_ALERTS.insert(0, new_alert)
    return {"message": "Emergency alert broadcast successfully", "alert": new_alert}


# ============================================================================
# 9. WEBSOCKET FOR REAL-TIME VR TELEMETRY & INSTRUCTOR CUES
# ============================================================================

@app.websocket("/ws/vr-telemetry")
async def websocket_vr_telemetry(websocket: WebSocket):
    """
    High-frequency bi-directional telemetry channel for VR Trainees.
    Receives trainee position packets (x, y, z, zone, tool), evaluates instant hazard proximity,
    and returns real-time audio cue triggers and virtual instructor safety prompts.
    """
    await websocket.accept()
    logger.info("VR Trainee connected to WebSocket telemetry channel.")
    try:
        while True:
            data_text = await websocket.receive_text()
            try:
                packet = json.loads(data_text)
                
                # Check hazard proximity in VR space
                pos_x = packet.get("pos_x", 0.0)
                pos_y = packet.get("pos_y", 0.0)
                pos_z = packet.get("pos_z", 0.0)
                equipped_tool = packet.get("tool", "None")
                water_level = packet.get("water_level_m", 0.4)
                
                # Compute guidance context from packet
                guidance_req = InstructorGuidanceRequest(
                    user_position={"x": pos_x, "y": pos_y, "z": pos_z},
                    current_zone_id=packet.get("zone", "Zone_A"),
                    water_level_m=water_level,
                    water_level_rate_m_per_min=packet.get("water_rise_rate", 0.05),
                    nearest_hazard_type=packet.get("nearest_hazard_type"),
                    nearest_hazard_dist_m=packet.get("nearest_hazard_dist_m"),
                    equipped_tool=equipped_tool,
                    nearby_victim_priority=packet.get("victim_priority"),
                    nearby_victim_dist_m=packet.get("victim_dist_m")
                )
                
                prompts = virtual_instructor.evaluate_live_guidance(guidance_req)
                
                response_payload = {
                    "status": "OK",
                    "prompts": [p.dict() for p in prompts],
                    "timestamp": packet.get("timestamp_sec", 0.0),
                    "warning_active": any(p.priority in ["CRITICAL_WARNING", "HAZARD_ALERT"] for p in prompts)
                }
                
                await websocket.send_text(json.dumps(response_payload))
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "Invalid JSON packet format"}))
    except WebSocketDisconnect:
        logger.info("VR Trainee disconnected from WebSocket telemetry channel.")


# ============================================================================
# 10. FRONTEND STATIC ASSETS MOUNT
# ============================================================================

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/app", summary="Serve Web Application Dashboard")
async def serve_app():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse({"error": "index.html not found in frontend directory"}, status_code=404)

@app.get("/style.css", include_in_schema=False)
async def serve_css():
    css_file = os.path.join(FRONTEND_DIR, "style.css")
    if os.path.exists(css_file):
        return FileResponse(css_file, media_type="text/css")
    raise HTTPException(status_code=404, detail="style.css not found")

@app.get("/app.js", include_in_schema=False)
async def serve_js():
    js_file = os.path.join(FRONTEND_DIR, "app.js")
    if os.path.exists(js_file):
        return FileResponse(js_file, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="app.js not found")
