"""
Model Training, Cross-Validation, Evaluation, Comparison and Joblib Serialization
Implements Random Forest, XGBoost, and Baselines on Kaggle Flood Risk Dataset.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any

# Ensure ai-backend root is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_BACKEND_ROOT = os.path.dirname(CURRENT_DIR)
if AI_BACKEND_ROOT not in sys.path:
    sys.path.insert(0, AI_BACKEND_ROOT)

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
)
import xgboost as xgb

from dataset.dataset_builder import load_or_generate_dataset
from preprocessing.pipeline import build_preprocessor, TARGET_COLUMN

MODELS_DIR = os.path.join(AI_BACKEND_ROOT, "models")


def train_and_evaluate() -> Dict[str, Any]:
    os.makedirs(MODELS_DIR, exist_ok=True)
    print("=" * 70)
    print("AI FLOOD RISK PREDICTION ENGINE - TRAINING & EVALUATION PIPELINE")
    print("=" * 70)

    # 1. Load Dataset
    df = load_or_generate_dataset()
    print(f"[1/6] Dataset loaded successfully. Shape: {df.shape}")

    X = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN]

    # 2. Strict Featurization Ordering: Split BEFORE Fitting Transformers
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"[2/6] Train/Test Split complete. Train samples: {len(X_train)}, Test samples: {len(X_test)}")

    # 3. Fit Preprocessing Pipeline on Training Data Only
    preprocessor = build_preprocessor()
    X_train_transformed = preprocessor.fit_transform(X_train)
    X_test_transformed = preprocessor.transform(X_test)
    print(f"[3/6] Preprocessing & feature engineering fit. Transformed feature dim: {X_train_transformed.shape[1]}")

    # Extract feature names after transformation
    col_transformer = preprocessor.named_steps['column_transformer']
    num_cols = col_transformer.transformers_[0][2]
    cat_cols_raw = col_transformer.transformers_[1][2]
    cat_encoder = col_transformer.transformers_[1][1].named_steps['encoder']
    cat_feature_names = list(cat_encoder.get_feature_names_out(cat_cols_raw))
    all_feature_names = list(num_cols) + cat_feature_names

    # 4. Candidate Models Definition
    models = {
        "RandomForestClassifier": RandomForestClassifier(
            n_estimators=180,
            max_depth=12,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        ),
        "XGBoostClassifier": xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=42,
            eval_metric='logloss',
            n_jobs=-1
        ),
        "GradientBoostingClassifier": GradientBoostingClassifier(
            n_estimators=120,
            learning_rate=0.1,
            max_depth=4,
            random_state=42
        ),
        "LogisticRegressionBaseline": LogisticRegression(
            max_iter=1000,
            random_state=42
        )
    }

    results = {}
    best_model_name = None
    best_f1 = -1.0
    best_model = None

    print("\n[4/6] Training and evaluating candidate models across metrics...")
    print("-" * 70)
    print(f"{'Model Name':<28} | {'Accuracy':<8} | {'Precision':<9} | {'Recall':<8} | {'F1-Score':<8} | {'ROC-AUC':<8}")
    print("-" * 70)

    for name, model in models.items():
        # Train
        model.fit(X_train_transformed, y_train)

        # Predict
        y_pred = model.predict(X_test_transformed)
        y_proba = model.predict_proba(X_test_transformed)[:, 1] if hasattr(model, "predict_proba") else y_pred

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))
        auc = float(roc_auc_score(y_test, y_proba))
        cm = confusion_matrix(y_test, y_pred).tolist()

        # 5-Fold Stratified Cross-Validation on training set
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(model, X_train_transformed, y_train, cv=cv, scoring='f1', n_jobs=-1)
        cv_f1_mean = float(np.mean(cv_scores))
        cv_f1_std = float(np.std(cv_scores))

        results[name] = {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(auc, 4),
            "cv_f1_mean": round(cv_f1_mean, 4),
            "cv_f1_std": round(cv_f1_std, 4),
            "confusion_matrix": cm
        }

        print(f"{name:<28} | {acc:<8.4f} | {prec:<9.4f} | {rec:<8.4f} | {f1:<8.4f} | {auc:<8.4f}")

        # Model Selection criterion: Highest Test F1 and ROC-AUC
        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_model = model

    print("-" * 70)
    print(f"\n[5/6] Selected Best Model: {best_model_name} (F1: {best_f1:.4f})")

    # Extract Feature Importances for best model
    feature_importances = {}
    if hasattr(best_model, "feature_importances_"):
        importances = best_model.feature_importances_
        sorted_idx = np.argsort(importances)[::-1]
        for idx in sorted_idx[:15]:
            feature_importances[all_feature_names[idx]] = round(float(importances[idx]), 4)

    # 5. Persist Model & Preprocessor via Joblib
    model_path = os.path.join(MODELS_DIR, "flood_model.joblib")
    preprocessor_path = os.path.join(MODELS_DIR, "preprocessor.joblib")
    metadata_path = os.path.join(MODELS_DIR, "model_metadata.json")

    joblib.dump(best_model, model_path)
    joblib.dump(preprocessor, preprocessor_path)

    metadata = {
        "model_name": best_model_name,
        "model_version": "1.0.0",
        "dataset_name": "Kaggle Flood Risk in India",
        "total_samples": len(df),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "metrics": results[best_model_name],
        "all_model_benchmarks": results,
        "feature_names": all_feature_names,
        "top_feature_importances": feature_importances,
        "risk_thresholds": {
            "LOW": [0.0, 0.30],
            "MEDIUM": [0.31, 0.60],
            "HIGH": [0.61, 1.00]
        }
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"[6/6] Artifacts serialized successfully:")
    print(f"      - {model_path}")
    print(f"      - {preprocessor_path}")
    print(f"      - {metadata_path}")
    print("=" * 70)

    return metadata


if __name__ == "__main__":
    train_and_evaluate()
