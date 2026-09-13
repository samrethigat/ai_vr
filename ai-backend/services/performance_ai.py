"""ML-based VR trainee performance analysis and personalized training recommendation."""
import os
import json
import joblib
import pandas as pd
from typing import Dict, Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(ROOT, "models", "trainee_performance_model.joblib")
META_PATH = os.path.join(ROOT, "models", "trainee_performance_metadata.json")

FEATURES = [
    "safety_awareness", "rescue_effectiveness", "decision_quality",
    "route_efficiency", "response_time", "communication", "tool_usage",
    "adaptability", "overall_score", "reaction_time_sec", "decision_time_sec",
    "mistakes", "hazard_violations", "victims_total", "victims_rescued",
    "evacuation_time_sec", "distance_travelled_m", "route_deviation_pct",
    "difficulty_encoded"
]
DIFF_CODE = {"EASY": 0, "MEDIUM": 1, "HARD": 2, "EXTREME": 3}

class PerformanceAI:
    def __init__(self):
        self.model = None
        self.metadata = {}
        self.reload()

    def reload(self):
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)
        if os.path.exists(META_PATH):
            with open(META_PATH, "r") as f:
                self.metadata = json.load(f)

    @property
    def is_ready(self):
        return self.model is not None

    def _weakest(self, scores: Dict[str, float]):
        labels = {
            "safety_awareness": "Safety Awareness",
            "rescue_effectiveness": "Rescue Effectiveness",
            "decision_quality": "Decision Quality",
            "route_efficiency": "Route Efficiency",
            "response_time": "Response Time",
            "communication": "Communication",
            "tool_usage": "Tool Usage",
            "adaptability": "Adaptability",
        }
        return min(scores, key=scores.get), labels[min(scores, key=scores.get)]

    def recommend(self, predicted_class: str, scores: Dict[str, float], difficulty: str):
        weak_key, weak_label = self._weakest(scores)
        overall = scores["overall_score"]

        if predicted_class == "NEEDS_RETRAINING":
            next_diff = "EASY"
        elif predicted_class == "DEVELOPING":
            next_diff = "MEDIUM"
        elif predicted_class == "PROFICIENT":
            next_diff = "HARD"
        else:
            next_diff = "EXTREME"

        # Avoid jumping too far from the current difficulty.
        current = DIFF_CODE.get(difficulty, 1)
        wanted = DIFF_CODE[next_diff]
        wanted = max(0, min(3, current + (1 if wanted > current else -1 if wanted < current else 0)))
        next_diff = list(DIFF_CODE.keys())[wanted]

        scenario_map = {
            "safety_awareness": ("AI_HAZARD_AWARENESS", "Hazard Awareness & Safe Clearance"),
            "rescue_effectiveness": ("AI_VICTIM_RESCUE", "Priority Victim Rescue & Triage"),
            "decision_quality": ("AI_DECISION_DRILL", "Rapid Disaster Decision-Making"),
            "route_efficiency": ("AI_NAVIGATION", "Dynamic Safe Route Navigation"),
            "response_time": ("AI_RAPID_RESPONSE", "Rapid Response & Evacuation"),
            "communication": ("AI_COMMUNICATION", "Emergency Radio Coordination"),
            "tool_usage": ("AI_TOOL_MASTERY", "Emergency Equipment Selection"),
            "adaptability": ("AI_ADAPTABILITY", "Dynamic Hazard Adaptation"),
        }
        sid, title = scenario_map[weak_key]
        return {
            "recommended_scenario_id": sid,
            "scenario_title": title,
            "target_difficulty": next_diff,
            "focus_competency": weak_label,
            "ai_reason": f"ML classified the trainee as {predicted_class}. The lowest competency is {weak_label} ({scores[weak_key]:.1f}/100).",
            "overall_score": round(overall, 2),
            "learning_objectives": [
                f"Improve {weak_label.lower()} above 80/100",
                "Reduce repeated mistakes and unsafe decisions",
                "Maintain or improve the current strengths while completing the targeted drill"
            ]
        }

    def analyze(self, features: Dict[str, Any]):
        if not self.is_ready:
            raise RuntimeError("Trainee performance model is not trained. Run training/train_performance_model.py first.")

        row = {f: float(features.get(f, 0)) for f in FEATURES}
        df = pd.DataFrame([row], columns=FEATURES)
        predicted = str(self.model.predict(df)[0])
        probabilities = self.model.predict_proba(df)[0]
        confidence = float(max(probabilities))
        class_probs = {str(c): round(float(p), 4) for c, p in zip(self.model.classes_, probabilities)}

        score_keys = [
            "safety_awareness", "rescue_effectiveness", "decision_quality", "route_efficiency",
            "response_time", "communication", "tool_usage", "adaptability", "overall_score"
        ]
        scores = {k: float(features.get(k, 0)) for k in score_keys}
        recommendation = self.recommend(predicted, scores, str(features.get("difficulty", "MEDIUM")).upper())

        # Simple local explanation based on model feature importance.
        ranked = sorted(zip(FEATURES, self.model.feature_importances_), key=lambda x: x[1], reverse=True)
        explanation = [
            {"feature": f, "importance": round(float(i), 4), "value": row[f]}
            for f, i in ranked[:6]
        ]
        return {
            "predicted_performance": predicted,
            "confidence": round(confidence, 4),
            "class_probabilities": class_probs,
            "weakest_competency": recommendation["focus_competency"],
            "recommendation": recommendation,
            "important_features": explanation
        }

performance_ai = PerformanceAI()
