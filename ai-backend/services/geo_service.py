"""
Geospatial Data & Location Analysis Service
Handles spatial hazard detection, flood zone queries, shelter proximity, and Indian geography matching.
"""

import math
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from routing.safe_route_engine import haversine_km, route_engine, SafeRouteRequest
from prediction.predictor import predictor, FloodPredictionInput


class LocationAnalysisRequest(BaseModel):
    user_id: Optional[str] = "trainee_user_01"
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    rainfall_override_mm: Optional[float] = None
    river_discharge_override_m3_s: Optional[float] = None


class LocationAnalysisResponse(BaseModel):
    user_location: Dict[str, float]
    nearest_region_name: str
    flood_prediction: Dict[str, Any]
    flood_probability: float
    risk_level: str
    current_water_level_m: float
    nearby_hazards: List[Dict[str, Any]]
    nearest_safe_shelter: Dict[str, Any]
    safe_route: Dict[str, Any]
    distance_to_shelter_km: float
    estimated_travel_time_min: float
    evacuation_urgency: str


class GeoService:
    def __init__(self):
        # Flood Zones with typical regional baseline profiles
        self.flood_zones = [
            {
                "id": "z1",
                "name": "Guwahati Brahmaputra Lowlands (Zone A)",
                "state": "Assam",
                "center_lat": 26.1722,
                "center_lng": 91.7458,
                "radius_km": 8.0,
                "baseline_rain": 240.0,
                "discharge": 2100.0,
                "water_level": 3.4,
                "elevation": 52.0,
                "land_cover": "Urban",
                "soil_type": "Alluvial",
                "population_density": 2100.0,
                "infrastructure": "Poor",
                "historical_floods": 5,
                "polygon": [
                    [26.190, 91.710], [26.200, 91.760], [26.160, 91.780], [26.140, 91.730]
                ]
            },
            {
                "id": "z2",
                "name": "Ernakulam-Aluva Periyar Lowlands (Zone B)",
                "state": "Kerala",
                "center_lat": 9.9816,
                "center_lng": 76.2999,
                "radius_km": 6.5,
                "baseline_rain": 190.0,
                "discharge": 1450.0,
                "water_level": 2.1,
                "elevation": 18.0,
                "land_cover": "Urban",
                "soil_type": "Clayey",
                "population_density": 1850.0,
                "infrastructure": "Moderate",
                "historical_floods": 3,
                "polygon": [
                    [10.010, 76.280], [10.020, 76.320], [9.970, 76.330], [9.950, 76.290]
                ]
            },
            {
                "id": "z3",
                "name": "Patna Ganges Lowland Corridor (Zone C)",
                "state": "Bihar",
                "center_lat": 25.6120,
                "center_lng": 85.1440,
                "radius_km": 9.0,
                "baseline_rain": 175.0,
                "discharge": 1800.0,
                "water_level": 2.9,
                "elevation": 53.0,
                "land_cover": "Agricultural",
                "soil_type": "Alluvial",
                "population_density": 2400.0,
                "infrastructure": "Poor",
                "historical_floods": 4,
                "polygon": [
                    [25.630, 85.110], [25.640, 85.180], [25.590, 85.170], [25.580, 85.120]
                ]
            },
            {
                "id": "z4",
                "name": "Mumbai Mithi River Basin (Zone D)",
                "state": "Maharashtra",
                "center_lat": 19.0680,
                "center_lng": 72.8700,
                "radius_km": 5.0,
                "baseline_rain": 260.0,
                "discharge": 1200.0,
                "water_level": 2.8,
                "elevation": 12.0,
                "land_cover": "Urban",
                "soil_type": "Clayey",
                "population_density": 4500.0,
                "infrastructure": "Moderate",
                "historical_floods": 6,
                "polygon": [
                    [19.090, 72.850], [19.100, 72.890], [19.050, 72.900], [19.040, 72.860]
                ]
            },
            {
                "id": "z5",
                "name": "Cuttack Mahanadi Floodplain (Zone E)",
                "state": "Odisha",
                "center_lat": 20.4625,
                "center_lng": 85.8828,
                "radius_km": 7.0,
                "baseline_rain": 120.0,
                "discharge": 850.0,
                "water_level": 1.1,
                "elevation": 36.0,
                "land_cover": "Agricultural",
                "soil_type": "Alluvial",
                "population_density": 1100.0,
                "infrastructure": "Good",
                "historical_floods": 2,
                "polygon": [
                    [20.490, 85.860], [20.500, 85.910], [20.440, 85.920], [20.430, 85.870]
                ]
            }
        ]

    def find_nearest_zone(self, lat: float, lng: float) -> Dict[str, Any]:
        best_zone = self.flood_zones[0]
        min_d = float('inf')
        for zone in self.flood_zones:
            d = haversine_km(lat, lng, zone["center_lat"], zone["center_lng"])
            if d < min_d:
                min_d = d
                best_zone = zone
        return best_zone

    def get_active_hazards(self, lat: float, lng: float, search_radius_km: float = 10.0) -> List[Dict[str, Any]]:
        nearby = []
        for h in route_engine.hazards:
            d_km = haversine_km(lat, lng, h["lat"], h["lng"])
            if d_km <= search_radius_km:
                nearby.append({
                    "id": h["id"],
                    "type": h["type"],
                    "description": h["desc"],
                    "latitude": h["lat"],
                    "longitude": h["lng"],
                    "severity": "CRITICAL" if h["severity"] >= 4.0 else ("HIGH" if h["severity"] >= 3.0 else "MEDIUM"),
                    "distance_meters": round(d_km * 1000.0, 1),
                    "impact_radius_m": h["radius_m"]
                })
        return sorted(nearby, key=lambda x: x["distance_meters"])

    def analyze_location(self, request: LocationAnalysisRequest) -> LocationAnalysisResponse:
        lat = request.latitude
        lng = request.longitude

        zone = self.find_nearest_zone(lat, lng)

        # Hydrological input synthesized from nearest regional parameters + overrides
        rain = request.rainfall_override_mm if request.rainfall_override_mm is not None else zone["baseline_rain"]
        discharge = request.river_discharge_override_m3_s if request.river_discharge_override_m3_s is not None else zone["discharge"]

        # Run AI prediction
        pred_input = FloodPredictionInput(
            Latitude=lat,
            Longitude=lng,
            Rainfall_mm=rain,
            Temperature_C=28.5,
            Humidity_pct=84.0,
            River_Discharge_m3_s=discharge,
            Water_Level_m=zone["water_level"],
            Elevation_m=zone["elevation"],
            Land_Cover=zone["land_cover"],
            Soil_Type=zone["soil_type"],
            Population_Density=zone["population_density"],
            Infrastructure=zone["infrastructure"],
            Historical_Floods=zone["historical_floods"]
        )

        prediction_result = predictor.predict(pred_input)

        # Identify nearby hazards
        hazards = self.get_active_hazards(lat, lng)

        # Identify nearest safe shelter
        nearest_shelter = route_engine.find_nearest_shelter(lat, lng)
        dist_to_shelter = round(haversine_km(lat, lng, nearest_shelter["lat"], nearest_shelter["lng"]), 2)

        # Compute safe evacuation route
        route_req = SafeRouteRequest(
            origin_latitude=lat,
            origin_longitude=lng,
            destination_latitude=nearest_shelter["lat"],
            destination_longitude=nearest_shelter["lng"]
        )
        safe_route_res = route_engine.compute_safe_route(route_req)

        if prediction_result.risk_level == "HIGH":
            urgency = "IMMEDIATE_EVACUATION_REQUIRED"
        elif prediction_result.risk_level == "MEDIUM":
            urgency = "ADVISORY_STANDBY"
        else:
            urgency = "MONITORING_NORMAL"

        return LocationAnalysisResponse(
            user_location={"latitude": lat, "longitude": lng},
            nearest_region_name=zone["name"],
            flood_prediction=prediction_result.dict(),
            flood_probability=prediction_result.flood_probability,
            risk_level=prediction_result.risk_level,
            current_water_level_m=prediction_result.water_level_m,
            nearby_hazards=hazards,
            nearest_safe_shelter=nearest_shelter,
            safe_route=safe_route_res.dict(),
            distance_to_shelter_km=dist_to_shelter,
            estimated_travel_time_min=safe_route_res.primary_safest_route.estimated_time_min,
            evacuation_urgency=urgency
        )

    analyze_user_location = analyze_location


geo_service = GeoService()
