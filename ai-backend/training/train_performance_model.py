"""
Train the AI model that predicts VR trainee performance.

This model is intentionally based on VR telemetry-derived features rather than
hard-coded competency rules. The initial dataset is synthetic so the project
can be developed without needing real trainees. Replace/augment the synthetic
CSV with real trainee sessions when available.
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "dataset")
MODEL_DIR = os.path.join(ROOT, "models")
CSV_PATH = os.path.join(DATA_DIR, "trainee_performance.csv")
MODEL_PATH = os.path.join(MODEL_DIR, "trainee_performance_model.joblib")
META_PATH = os.path.join(MODEL_DIR, "trainee_performance_metadata.json")

FEATURES = [
    "safety_awareness", "rescue_effectiveness", "decision_quality",
    "route_efficiency", "response_time", "communication", "tool_usage",
    "adaptability", "overall_score", "reaction_time_sec", "decision_time_sec",
    "mistakes", "hazard_violations", "victims_total", "victims_rescued",
    "evacuation_time_sec", "distance_travelled_m", "route_deviation_pct",
    "difficulty_encoded"
]
TARGET = "performance_class"


def generate_synthetic_dataset(n=5000, seed=42):
    rng = np.random.default_rng(seed)
    difficulties = rng.choice(["EASY", "MEDIUM", "HARD", "EXTREME"], n, p=[.25, .35, .30, .10])
    diff_code = {"EASY": 0, "MEDIUM": 1, "HARD": 2, "EXTREME": 3}

    overall = np.clip(rng.normal(72, 17, n), 20, 100)
    skills = {}
    for name in ["safety_awareness", "rescue_effectiveness", "decision_quality", "route_efficiency",
                 "response_time", "communication", "tool_usage", "adaptability"]:
        skills[name] = np.clip(overall + rng.normal(0, 12, n), 10, 100)

    reaction = np.clip(12 - skills["response_time"] * 0.085 + rng.normal(0, 1.5, n), .8, 15)
    decision = np.clip(15 - skills["decision_quality"] * 0.10 + rng.normal(0, 2.0, n), 1, 20)
    mistakes = np.clip(np.round((100 - overall) / 12 + rng.normal(0, 1.5, n)), 0, 15).astype(int)
    hazards = np.clip(np.round((100 - skills["safety_awareness"]) / 20 + rng.normal(0, .8, n)), 0, 8).astype(int)
    victims_total = rng.integers(2, 9, n)
    rescue_probability = np.clip(skills["rescue_effectiveness"] / 100, .15, .99)
    victims_rescued = np.array([rng.binomial(t, p) for t, p in zip(victims_total, rescue_probability)])
    evacuation = np.clip(420 - skills["response_time"] * 2.2 + rng.normal(0, 35, n), 60, 600)
    distance = np.clip(rng.normal(140, 45, n) + mistakes * 5, 30, 400)
    route_dev = np.clip((100 - skills["route_efficiency"]) * .65 + rng.normal(0, 4, n), 0, 60)

    df = pd.DataFrame(skills)
    df["overall_score"] = np.mean([df[c] for c in skills], axis=0)
    df["reaction_time_sec"] = reaction.round(2)
    df["decision_time_sec"] = decision.round(2)
    df["mistakes"] = mistakes
    df["hazard_violations"] = hazards
    df["victims_total"] = victims_total
    df["victims_rescued"] = victims_rescued
    df["evacuation_time_sec"] = evacuation.round(1)
    df["distance_travelled_m"] = distance.round(1)
    df["route_deviation_pct"] = route_dev.round(1)
    df["difficulty"] = difficulties
    df["difficulty_encoded"] = [diff_code[x] for x in difficulties]

    # Labels are generated from observable performance, not from the model.
    # They simulate expert-assigned training tiers for initial development.
    adjusted = (
        0.30 * df["overall_score"] +
        0.15 * df["safety_awareness"] +
        0.15 * df["decision_quality"] +
        0.10 * df["rescue_effectiveness"] +
        0.10 * df["route_efficiency"] +
        0.10 * df["response_time"] +
        0.10 * (100 - df["mistakes"].clip(0, 10) * 7)
    )
    df[TARGET] = pd.cut(adjusted, bins=[-1, 55, 75, 90, 101], labels=["NEEDS_RETRAINING", "DEVELOPING", "PROFICIENT", "EXPERT"]).astype(str)
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(CSV_PATH, index=False)
    return df


def train():
    os.makedirs(MODEL_DIR, exist_ok=True)
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
    else:
        df = generate_synthetic_dataset()

    X = df[FEATURES].copy()
    y = df[TARGET].astype(str)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.2, stratify=y, random_state=42)

    model = RandomForestClassifier(
        n_estimators=350, max_depth=14, min_samples_leaf=2,
        class_weight="balanced", random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "precision_weighted": round(float(precision_score(y_test, pred, average="weighted", zero_division=0)), 4),
        "recall_weighted": round(float(recall_score(y_test, pred, average="weighted", zero_division=0)), 4),
        "f1_weighted": round(float(f1_score(y_test, pred, average="weighted", zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
        "classification_report": classification_report(y_test, pred, output_dict=True, zero_division=0)
    }

    importances = dict(sorted(zip(FEATURES, model.feature_importances_), key=lambda x: x[1], reverse=True))
    metadata = {
        "model_name": "RandomForestTraineePerformanceClassifier",
        "model_version": "1.0.0",
        "features": FEATURES,
        "classes": list(model.classes_),
        "metrics": metrics,
        "top_features": {k: round(float(v), 4) for k, v in list(importances.items())[:10]},
        "dataset": os.path.basename(CSV_PATH),
        "note": "Initial dataset is synthetic. Retrain with real VR trainee sessions when available."
    }
    joblib.dump(model, MODEL_PATH)
    with open(META_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    print("\nTrainee Performance AI trained successfully")
    print("Dataset:", CSV_PATH)
    print("Model:", MODEL_PATH)
    print("Accuracy:", metrics["accuracy"])
    print("Weighted F1:", metrics["f1_weighted"])
    print("Classes:", list(model.classes_))
    print("Top features:", metadata["top_features"])
    return metadata


if __name__ == "__main__":
    train()
