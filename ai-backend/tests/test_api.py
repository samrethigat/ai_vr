"""
Integration and Unit Test Suite for AI Flood Response and VR Training API Server
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

# Ensure ai-backend directory is in Python path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from main import app


class TestFloodVRApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_root_and_health(self):
        """Verify root and health check endpoints respond with OPERATIONAL status."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["ml_predictor"], "ready")

        root_res = self.client.get("/")
        self.assertEqual(root_res.status_code, 200)
        self.assertEqual(root_res.json()["system"], "AI-Powered Smart Flood Disaster Response & VR Training System")

    def test_02_predict_flood_risk_high(self):
        """Verify high flood risk prediction during extreme rainfall and river discharge."""
        payload = {
            "Latitude": 26.1722,
            "Longitude": 91.7458,
            "Rainfall_mm": 290.0,
            "Temperature_C": 27.5,
            "Humidity_pct": 92.0,
            "River_Discharge_m3_s": 2450.0,
            "Water_Level_m": 3.8,
            "Elevation_m": 12.0,
            "Land_Cover": "Urban",
            "Soil_Type": "Alluvial",
            "Population_Density": 2200.0,
            "Infrastructure": "Poor",
            "Historical_Floods": 5
        }
        response = self.client.post("/api/v1/predict/flood-risk", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("flood_probability", data)
        self.assertIn("risk_level", data)
        self.assertGreaterEqual(data["flood_probability"], 0.6)
        self.assertEqual(data["risk_level"], "HIGH")
        self.assertIn("top_contributing_factors", data)
        self.assertIn("action_recommendation", data)

    def test_03_predict_flood_risk_low(self):
        """Verify low flood risk prediction under dry conditions."""
        payload = {
            "Latitude": 12.9716,
            "Longitude": 77.5946,
            "Rainfall_mm": 5.0,
            "Temperature_C": 26.0,
            "Humidity_pct": 50.0,
            "River_Discharge_m3_s": 120.0,
            "Water_Level_m": 0.4,
            "Elevation_m": 920.0,
            "Land_Cover": "Urban",
            "Soil_Type": "Red_Soil",
            "Population_Density": 1500.0,
            "Infrastructure": "Good",
            "Historical_Floods": 0
        }
        response = self.client.post("/api/v1/predict/flood-risk", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertLessEqual(data["flood_probability"], 0.35)
        self.assertEqual(data["risk_level"], "LOW")

    def test_04_safe_route_astar(self):
        """Verify A* safe evacuation route calculation avoids high hazards."""
        payload = {
            "origin_latitude": 26.1722,
            "origin_longitude": 91.7458,
            "algorithm": "A_STAR",
            "avoid_water_above_meters": 0.6,
            "hazard_penalty_weight": 5.0,
            "flood_risk_weight": 4.0
        }
        response = self.client.post("/api/v1/routing/safe-route", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("primary_safest_route", data)
        self.assertIn("alternative_route", data)
        primary = data["primary_safest_route"]
        self.assertGreater(primary["distance_km"], 0.0)
        self.assertGreater(primary["safety_score"], 0.0)
        self.assertGreater(len(primary["waypoints"]), 0)
        self.assertGreater(len(primary["turn_by_turn_instructions"]), 0)

    def test_05_location_analysis_endpoint(self):
        """Verify unified location analysis matches closest zone and returns route to nearest shelter."""
        payload = {
            "user_id": "trainee_test_01",
            "latitude": 26.1700,
            "longitude": 91.7400
        }
        response = self.client.post("/api/v1/geo/location-analysis", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["nearest_region_name"], "Guwahati Brahmaputra Lowlands (Zone A)")
        self.assertIn("nearest_safe_shelter", data)
        self.assertIn("safe_route", data)
        self.assertIn("evacuation_urgency", data)

    def test_06_virtual_instructor_guidance(self):
        """Verify deterministic safety warnings for live electrical line proximity."""
        payload = {
            "user_position": {"x": 10.0, "y": 0.0, "z": 15.0},
            "current_zone_id": "Zone_A",
            "water_level_m": 0.8,
            "water_level_rate_m_per_min": 0.04,
            "nearest_hazard_type": "ELECTRICAL",
            "nearest_hazard_dist_m": 5.5,
            "equipped_tool": "Life Jacket"
        }
        response = self.client.post("/api/v1/vr/virtual-instructor/guidance", json=payload)
        self.assertEqual(response.status_code, 200)
        prompts = response.json()
        self.assertGreater(len(prompts), 0)
        first_prompt = prompts[0]
        self.assertEqual(first_prompt["priority"], "CRITICAL_WARNING")
        self.assertEqual(first_prompt["safety_rule_code"], "SOP_ELEC_01")
        self.assertIn("ELECTRICAL", first_prompt["headline"])

    def test_07_vr_telemetry_evaluation_and_curriculum(self):
        """Verify 8-vector competency evaluation and adaptive curriculum synthesis."""
        payload = {
            "session_id": "sess-test-01",
            "trainee_id": "trainee-rahul-09",
            "scenario_id": "SCEN_URBAN_DELUGE_01",
            "scenario_title": "Brahmaputra Lowlands Urban Deluge & Substation Isolation",
            "difficulty": "MEDIUM",
            "total_duration_seconds": 240.0,
            "victims_total": 4,
            "victims_rescued": 4,
            "hazards_triggered": 0,
            "telemetry_stream": [
                {"timestamp_sec": 10.0, "position_x": 0.0, "position_y": 0.0, "position_z": 0.0, "speed": 1.2, "action_type": "MOVE", "hazard_proximity_m": 12.0},
                {"timestamp_sec": 45.0, "position_x": 25.0, "position_y": 0.0, "position_z": 30.0, "speed": 0.5, "action_type": "TOOL_EQUIP", "tool_in_hand": "Insulated Probe", "hazard_proximity_m": 9.0},
                {"timestamp_sec": 90.0, "position_x": 50.0, "position_y": 0.0, "position_z": 60.0, "speed": 0.0, "action_type": "VICTIM_TRIAGE", "target_entity": "Victim 1 (Child)"},
                {"timestamp_sec": 130.0, "position_x": 55.0, "position_y": 0.0, "position_z": 65.0, "speed": 1.0, "action_type": "VICTIM_RESCUE", "target_entity": "Victim 1 (Child)"},
                {"timestamp_sec": 170.0, "position_x": 75.0, "position_y": 0.0, "position_z": 80.0, "speed": 1.1, "action_type": "RADIO_CALL", "notes": "Convoy status clear"},
                {"timestamp_sec": 230.0, "position_x": 100.0, "position_y": 0.0, "position_z": 110.0, "speed": 1.0, "action_type": "ROUTE_CHOICE", "target_entity": "North High Ridge"}
            ]
        }
        response = self.client.post("/api/v1/vr/telemetry-evaluate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        scores = data["competency_scores"]
        
        # Verify 8 competency metrics exist
        self.assertIn("safety_awareness", scores)
        self.assertIn("rescue_effectiveness", scores)
        self.assertIn("decision_quality", scores)
        self.assertIn("route_efficiency", scores)
        self.assertIn("response_time", scores)
        self.assertIn("communication", scores)
        self.assertIn("tool_usage", scores)
        self.assertIn("adaptability", scores)
        self.assertIn("overall_score", scores)

        self.assertGreaterEqual(scores["overall_score"], 70.0)
        self.assertIn("performance_tier", data)
        self.assertIn("next_training_recommendation", data)

    def test_08_hazards_and_alerts_crud(self):
        """Verify listing and creating dynamic environmental hazards and broadcast alerts."""
        # List hazards
        hazards_res = self.client.get("/api/v1/hazards")
        self.assertEqual(hazards_res.status_code, 200)
        initial_count = len(hazards_res.json()["hazards"])

        # Add new hazard
        new_hazard = {
            "hazard_type": "BLOCKED_ROAD",
            "latitude": 26.1600,
            "longitude": 91.7300,
            "radius_meters": 75.0,
            "severity": 4.0,
            "description": "Flash landslide blocking North Bypass"
        }
        create_res = self.client.post("/api/v1/hazards", json=new_hazard)
        self.assertEqual(create_res.status_code, 200)
        created_id = create_res.json()["hazard"]["id"]

        # Check count increased
        updated_res = self.client.get("/api/v1/hazards")
        self.assertEqual(len(updated_res.json()["hazards"]), initial_count + 1)

        # Delete hazard
        del_res = self.client.delete(f"/api/v1/hazards/{created_id}")
        self.assertEqual(del_res.status_code, 200)

        # Test alerts
        alerts_res = self.client.get("/api/v1/alerts")
        self.assertEqual(alerts_res.status_code, 200)
        self.assertGreater(len(alerts_res.json()["alerts"]), 0)


if __name__ == "__main__":
    unittest.main()
