"""
Preprocessing and Feature Engineering Pipeline for Flood Prediction
Adheres strictly to ML Best Practices: Feature engineering & fit only on training split.
"""

import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer


NUMERICAL_BASE_FEATURES = [
    'Latitude',
    'Longitude',
    'Rainfall_mm',
    'Temperature_C',
    'Humidity_pct',
    'River_Discharge_m3_s',
    'Water_Level_m',
    'Elevation_m',
    'Population_Density',
    'Historical_Floods'
]

CATEGORICAL_FEATURES = [
    'Land_Cover',
    'Soil_Type',
    'Infrastructure'
]

TARGET_COLUMN = 'Flood_Occurred'


class FloodFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Creates physically grounded hydrological features:
    - Hydrological_Pressure_Ratio: River_Discharge_m3_s / (Water_Level_m + 0.1)
    - Runoff_Index: Rainfall_mm / (Elevation_m + 10.0)
    - Water_Accumulation_Proxy: (Rainfall_mm * Humidity_pct) / 100.0
    - Topographic_Vulnerability: 100.0 / (Elevation_m + 5.0)
    - Historical_Risk_Index: Historical_Floods * (Rainfall_mm / 100.0)
    """
    def __init__(self):
        self.engineered_feature_names = [
            'Hydrological_Pressure_Ratio',
            'Runoff_Index',
            'Water_Accumulation_Proxy',
            'Topographic_Vulnerability',
            'Historical_Risk_Index'
        ]

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X_df = X.copy()
        if isinstance(X_df, np.ndarray):
            # Not expected directly with DataFrame inputs, but safe fallback
            pass

        # Calculate engineered indicators
        X_df['Hydrological_Pressure_Ratio'] = X_df['River_Discharge_m3_s'] / (X_df['Water_Level_m'] + 0.1)
        X_df['Runoff_Index'] = X_df['Rainfall_mm'] / (X_df['Elevation_m'] + 10.0)
        X_df['Water_Accumulation_Proxy'] = (X_df['Rainfall_mm'] * X_df['Humidity_pct']) / 100.0
        X_df['Topographic_Vulnerability'] = 100.0 / (X_df['Elevation_m'] + 5.0)
        X_df['Historical_Risk_Index'] = X_df['Historical_Floods'] * (X_df['Rainfall_mm'] / 100.0)

        return X_df


def build_preprocessor() -> ColumnTransformer:
    """
    Constructs the ColumnTransformer for numerical and categorical features.
    """
    all_numerical = NUMERICAL_BASE_FEATURES + [
        'Hydrological_Pressure_Ratio',
        'Runoff_Index',
        'Water_Accumulation_Proxy',
        'Topographic_Vulnerability',
        'Historical_Risk_Index'
    ]

    num_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    cat_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', num_pipeline, all_numerical),
            ('cat', cat_pipeline, CATEGORICAL_FEATURES)
        ],
        remainder='drop'
    )

    full_preprocessing_pipeline = Pipeline([
        ('feature_engineer', FloodFeatureEngineer()),
        ('column_transformer', preprocessor)
    ])

    return full_preprocessing_pipeline
