# AI-Powered Smart Flood Disaster Response & VR Training System

An integrated AI and VR platform for flood disaster response, emergency simulations, VR training, telemetry scoring, and live location guidance.

## Key Features

- **AI-Powered Flood Prediction**: Predicts flood risk levels based on meteorological and terrain parameters.
- **VR Training & Telemetry Analysis**: Real-time evaluation of rescue personnel during VR disaster simulations.
- **Dynamic Safe Route Engine**: Real-time safe route calculations avoiding flooded zones and hazardous areas.
- **AI Virtual Instructor**: Context-aware live guidance during emergency drills and simulations.
- **Geographic Information Services**: Coordinates, elevation, water body proximity, and regional risk assessment.

## Project Structure

```
ai_vr/
├── ai-backend/              # FastAPI Backend Server
│   ├── dataset/             # Flood risk datasets & builder
│   ├── models/              # Pretrained ML models & metadata
│   ├── prediction/          # Flood prediction engine
│   ├── preprocessing/       # ML data pipelines
│   ├── routing/             # Safe route planning algorithm
│   ├── scoring/             # VR telemetry analysis & scoring
│   ├── services/            # Virtual instructor, adaptive learning & geo services
│   ├── tests/               # Backend API tests
│   ├── training/            # ML model training scripts
│   └── main.py              # Main FastAPI application entry point
├── database/
│   └── schema.sql           # Database schema & setup
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.10+
- pip

### Run Backend
```bash
cd ai-backend
pip install -r requirements.txt # (or install required dependencies)
uvicorn main:app --reload --port 8000
```
