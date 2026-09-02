"""
Flood Risk Prediction Service
Loads Joblib serialized ML models and provides inference with risk stratification.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
MODEL_PATH = os.path.join(MODELS_DIR, "flood_model.joblib")
PREPROCESSOR_PATH = os.path.join(MODELS_DIR, "preprocessor.joblib")
METADATA_PATH = os.path.join(MODELS_DIR, "model_metadata.json")


class FloodPredictionInput(BaseModel):
    Latitude: float = Field(..., ge=-90.0, le=90.0, description="Geographic Latitude in decimal degrees")
    Longitude: float = Field(..., ge=-180.0, le=180.0, description="Geographic Longitude in decimal degrees")
    Rainfall_mm: float = Field(..., ge=0.0, description="24-hour rainfall accumulation in mm")
    Temperature_C: float = Field(default=28.0, ge=-20.0, le=60.0, description="Ambient temperature in Celsius")
    Humidity_pct: float = Field(default=80.0, ge=0.0, le=100.0, description="Relative humidity percentage")
    River_Discharge_m3_s: float = Field(..., ge=0.0, description="River discharge rate in cubic meters per second")
    Water_Level_m: float = Field(..., ge=0.0, description="Gauge water level stage above baseline in meters")
    Elevation_m: float = Field(..., ge=0.0, description="Topographic elevation in meters above sea level")
    Land_Cover: str = Field(default="Urban", description="Land cover type (Urban, Agricultural, Forest, Wetland, Water_Body, Barren)")
    Soil_Type: str = Field(default="Alluvial", description="Soil type (Alluvial, Black_Soil, Red_Soil, Laterite, Clayey, Sandy_Loam)")
    Population_Density: float = Field(default=1200.0, ge=0.0, description="Population density per sq km")
    Infrastructure: str = Field(default="Moderate", description="Infrastructure quality (Poor, Moderate, Good, Critical)")
    Historical_Floods: int = Field(default=2, ge=0, description="Count of historical flood events in region")


class FloodPredictionResult(BaseModel):
    flood_probability: float
    risk_level: str
    risk_color: str
    water_level_m: float
    rainfall_mm: float
    river_discharge_m3_s: float
    elevation_m: float
    model_name: str
    model_version: str
    top_contributing_factors: List[Dict[str, Any]]
    action_recommendation: str


class FloodPredictor:
    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.metadata = {}
        self.load_artifacts()

    def load_artifacts(self):
        if os.path.exists(MODEL_PATH) and os.path.exists(PREPROCESSOR_PATH):
            self.model = joblib.load(MODEL_PATH)
            self.preprocessor = joblib.load(PREPROCESSOR_PATH)
        if os.path.exists(METADATA_PATH):
            with open(METADATA_PATH, "r") as f:
                self.metadata = json.load(f)

    def is_ready(self) -> bool:
        return self.model is not None and self.preprocessor is not None

    def predict(self, input_data: FloodPredictionInput) -> FloodPredictionResult:
        if not self.is_ready():
            self.load_artifacts()
            if not self.is_ready():
                raise RuntimeError("ML model and preprocessor are not trained or loaded.")

        # Convert to single-row DataFrame
        df_input = pd.DataFrame([input_data.dict()])

        # Transform using fitted preprocessor
        transformed = self.preprocessor.transform(df_input)

        # Predict probability
        if hasattr(self.model, "predict_proba"):
            proba = float(self.model.predict_proba(transformed)[0][1])
        else:
            proba = float(self.model.predict(transformed)[0])

        proba = round(np.clip(proba, 0.0, 1.0), 4)

        # Stratify risk level
        if proba <= 0.30:
            risk_level = "LOW"
            risk_color = "#22C55E" # Success Green
            recommendation = "Normal conditions. Routine hydrological monitoring is active. Standard precautions apply."
        elif proba <= 0.60:
            risk_level = "MEDIUM"
            risk_color = "#F59E0B" # Warning Amber
            recommendation = "Elevated risk. Local flood watch issued. Keep rescue supplies ready and inspect safe routes."
        else:
            risk_level = "HIGH"
            risk_color = "#EF4444" # Danger Red
            recommendation = "CRITICAL FLOOD RISK: Immediate evacuation to elevated shelters advised. Avoid low-lying corridors."

        # Compute key contribution factors
        factors = [
            {"factor": "Rainfall Intensity", "value": f"{input_data.Rainfall_mm:.1f} mm", "impact": "High" if input_data.Rainfall_mm > 180 else "Normal"},
            {"factor": "River Stage Level", "value": f"{input_data.Water_Level_m:.2f} m", "impact": "Critical" if input_data.Water_Level_m > 2.8 else "Moderate"},
            {"factor": "River Discharge", "value": f"{input_data.River_Discharge_m3_s:.0f} m³/s", "impact": "High" if input_data.River_Discharge_m3_s > 1400 else "Normal"},
            {"factor": "Topography Elevation", "value": f"{input_data.Elevation_m:.1f} m", "impact": "High Vulnerability" if input_data.Elevation_m < 25 else "Low Vulnerability"},
            {"factor": "Land Drainage Type", "value": f"{input_data.Land_Cover} / {input_data.Soil_Type}", "impact": "Sub-optimal" if input_data.Land_Cover in ['Urban', 'Wetland'] else "Standard"}
        ]

        return FloodPredictionResult(
            flood_probability=proba,
            risk_level=risk_level,
            risk_color=risk_color,
            water_level_m=input_data.Water_Level_m,
            rainfall_mm=input_data.Rainfall_mm,
            river_discharge_m3_s=input_data.River_Discharge_m3_s,
            elevation_m=input_data.Elevation_m,
            model_name=self.metadata.get("model_name", "XGBoostClassifier"),
            model_version=self.metadata.get("model_version", "1.0.0"),
            top_contributing_factors=factors,
            action_recommendation=recommendation
        )


predictor = FloodPredictor()
