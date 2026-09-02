-- ============================================================================
-- AI-Powered Smart Flood Disaster Response, VR Training and Live Location Guidance System
-- PostgreSQL Database Schema & Initial Seed Data
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. USERS & ROLES
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('User', 'Trainee', 'Trainer', 'Administrator')),
    organization VARCHAR(150),
    phone_number VARCHAR(30),
    emergency_contact VARCHAR(30),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. USER LIVE LOCATIONS
CREATE TABLE IF NOT EXISTS user_locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    altitude DOUBLE PRECISION DEFAULT 0.0,
    speed DOUBLE PRECISION DEFAULT 0.0,
    heading DOUBLE PRECISION DEFAULT 0.0,
    accuracy DOUBLE PRECISION DEFAULT 5.0,
    in_danger_zone BOOLEAN DEFAULT FALSE,
    current_zone_id UUID,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_locations_user_id ON user_locations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_locations_timestamp ON user_locations(timestamp DESC);

-- 3. FLOOD ZONES
CREATE TABLE IF NOT EXISTS flood_zones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zone_name VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    river_basin VARCHAR(100) NOT NULL,
    center_latitude DOUBLE PRECISION NOT NULL,
    center_longitude DOUBLE PRECISION NOT NULL,
    radius_km DOUBLE PRECISION NOT NULL DEFAULT 5.0,
    polygon_coordinates JSONB,
    current_risk_level VARCHAR(20) NOT NULL CHECK (current_risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    flood_probability DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    water_level_m DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    flow_velocity_ms DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    rainfall_accumulated_mm DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. FLOOD PREDICTIONS (ML Inference History)
CREATE TABLE IF NOT EXISTS flood_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    rainfall_mm DOUBLE PRECISION NOT NULL,
    temperature_c DOUBLE PRECISION NOT NULL,
    humidity_pct DOUBLE PRECISION NOT NULL,
    river_discharge_m3_s DOUBLE PRECISION NOT NULL,
    water_level_m DOUBLE PRECISION NOT NULL,
    elevation_m DOUBLE PRECISION NOT NULL,
    land_cover VARCHAR(50) NOT NULL,
    soil_type VARCHAR(50) NOT NULL,
    population_density DOUBLE PRECISION NOT NULL,
    infrastructure VARCHAR(50) NOT NULL,
    historical_floods INT NOT NULL,
    flood_probability DOUBLE PRECISION NOT NULL,
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    model_name VARCHAR(100) NOT NULL DEFAULT 'RandomForestClassifier',
    model_version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_flood_predictions_lat_lng ON flood_predictions(latitude, longitude);

-- 5. HAZARDS
CREATE TABLE IF NOT EXISTS hazards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hazard_type VARCHAR(50) NOT NULL CHECK (hazard_type IN ('ELECTRICAL', 'BLOCKED_ROAD', 'DEEP_WATER', 'FALLEN_TREE', 'BRIDGE_FAILURE', 'LANDSLIDE')),
    title VARCHAR(150) NOT NULL,
    description TEXT,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    radius_meters DOUBLE PRECISION NOT NULL DEFAULT 50.0,
    is_active BOOLEAN DEFAULT TRUE,
    reported_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_hazards_active ON hazards(is_active) WHERE is_active = TRUE;

-- 6. SAFE SHELTERS
CREATE TABLE IF NOT EXISTS safe_shelters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(150) NOT NULL,
    address TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    elevation_m DOUBLE PRECISION NOT NULL,
    total_capacity INT NOT NULL,
    current_occupancy INT NOT NULL DEFAULT 0,
    has_medical_facility BOOLEAN DEFAULT TRUE,
    has_power_backup BOOLEAN DEFAULT TRUE,
    has_clean_water BOOLEAN DEFAULT TRUE,
    contact_phone VARCHAR(50),
    is_operational BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. ROUTES & NAVIGATION AUDIT
CREATE TABLE IF NOT EXISTS routes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    origin_lat DOUBLE PRECISION NOT NULL,
    origin_lng DOUBLE PRECISION NOT NULL,
    destination_shelter_id UUID REFERENCES safe_shelters(id) ON DELETE SET NULL,
    dest_lat DOUBLE PRECISION NOT NULL,
    dest_lng DOUBLE PRECISION NOT NULL,
    algorithm_used VARCHAR(50) NOT NULL DEFAULT 'A_STAR',
    distance_km DOUBLE PRECISION NOT NULL,
    estimated_time_min DOUBLE PRECISION NOT NULL,
    safety_score DOUBLE PRECISION NOT NULL,
    waypoints_geojson JSONB NOT NULL,
    avoided_hazards_count INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. VR TRAINING SESSIONS
CREATE TABLE IF NOT EXISTS training_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trainee_id UUID REFERENCES users(id) ON DELETE CASCADE,
    scenario_id VARCHAR(100) NOT NULL,
    scenario_title VARCHAR(150) NOT NULL,
    difficulty VARCHAR(30) NOT NULL CHECK (difficulty IN ('EASY', 'MEDIUM', 'HARD', 'EXTREME')),
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds INT DEFAULT 0,
    status VARCHAR(30) NOT NULL CHECK (status IN ('IN_PROGRESS', 'COMPLETED', 'FAILED', 'ABORTED')),
    victims_rescued INT DEFAULT 0,
    victims_total INT DEFAULT 0,
    hazards_triggered INT DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_training_sessions_trainee ON training_sessions(trainee_id);

-- 9. VR TELEMETRY STREAM
CREATE TABLE IF NOT EXISTS telemetry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES training_sessions(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    elapsed_seconds DOUBLE PRECISION NOT NULL,
    pos_x DOUBLE PRECISION NOT NULL,
    pos_y DOUBLE PRECISION NOT NULL,
    pos_z DOUBLE PRECISION NOT NULL,
    speed DOUBLE PRECISION NOT NULL,
    current_zone VARCHAR(100),
    action_type VARCHAR(100) NOT NULL,
    target_entity VARCHAR(100),
    hazard_proximity_m DOUBLE PRECISION,
    tool_in_hand VARCHAR(50),
    metadata_json JSONB
);

CREATE INDEX IF NOT EXISTS idx_telemetry_session_id ON telemetry(session_id);

-- 10. COMPETENCY SCORES (8-Vector Evaluation)
CREATE TABLE IF NOT EXISTS competency_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID UNIQUE REFERENCES training_sessions(id) ON DELETE CASCADE,
    trainee_id UUID REFERENCES users(id) ON DELETE CASCADE,
    safety_awareness DOUBLE PRECISION NOT NULL CHECK (safety_awareness BETWEEN 0 AND 100),
    rescue_effectiveness DOUBLE PRECISION NOT NULL CHECK (rescue_effectiveness BETWEEN 0 AND 100),
    decision_quality DOUBLE PRECISION NOT NULL CHECK (decision_quality BETWEEN 0 AND 100),
    route_efficiency DOUBLE PRECISION NOT NULL CHECK (route_efficiency BETWEEN 0 AND 100),
    response_time DOUBLE PRECISION NOT NULL CHECK (response_time BETWEEN 0 AND 100),
    communication DOUBLE PRECISION NOT NULL CHECK (communication BETWEEN 0 AND 100),
    tool_usage DOUBLE PRECISION NOT NULL CHECK (tool_usage BETWEEN 0 AND 100),
    adaptability DOUBLE PRECISION NOT NULL CHECK (adaptability BETWEEN 0 AND 100),
    overall_score DOUBLE PRECISION NOT NULL CHECK (overall_score BETWEEN 0 AND 100),
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 11. AI FEEDBACK & VIRTUAL INSTRUCTOR REPORT
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID UNIQUE REFERENCES training_sessions(id) ON DELETE CASCADE,
    summary_evaluation TEXT NOT NULL,
    strengths JSONB NOT NULL DEFAULT '[]'::jsonb,
    weaknesses JSONB NOT NULL DEFAULT '[]'::jsonb,
    unsafe_decisions JSONB NOT NULL DEFAULT '[]'::jsonb,
    missed_actions JSONB NOT NULL DEFAULT '[]'::jsonb,
    improvement_suggestions JSONB NOT NULL DEFAULT '[]'::jsonb,
    instructor_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 12. PERSONALIZED ADAPTIVE LEARNING PATHS
CREATE TABLE IF NOT EXISTS learning_paths (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trainee_id UUID REFERENCES users(id) ON DELETE CASCADE,
    current_tier VARCHAR(50) NOT NULL DEFAULT 'Level 1: Basic Disaster Preparedness',
    recommended_scenario_id VARCHAR(100) NOT NULL,
    recommended_scenario_title VARCHAR(150) NOT NULL,
    focus_competency VARCHAR(100) NOT NULL,
    target_difficulty VARCHAR(30) NOT NULL,
    rationale TEXT NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed BOOLEAN DEFAULT FALSE
);

-- 13. EMERGENCY ALERTS & BROADCASTS
CREATE TABLE IF NOT EXISTS emergency_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(30) NOT NULL CHECK (severity IN ('ADVISORY', 'WATCH', 'WARNING', 'CRITICAL_EMERGENCY')),
    region VARCHAR(100) NOT NULL,
    affected_latitude DOUBLE PRECISION NOT NULL,
    affected_longitude DOUBLE PRECISION NOT NULL,
    radius_km DOUBLE PRECISION NOT NULL DEFAULT 20.0,
    issued_by VARCHAR(100) NOT NULL DEFAULT 'National Disaster Response Force (NDRF)',
    is_active BOOLEAN DEFAULT TRUE,
    broadcast_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- 14. AUDIT LOGS
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(100),
    details JSONB,
    ip_address VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SEED DATA (Indian Flood Zones, Shelters, Hazards, Initial Admins & Scenarios)
-- ============================================================================

-- Seed Users
INSERT INTO users (id, email, password_hash, full_name, role, organization, phone_number, emergency_contact)
VALUES 
('11111111-1111-1111-1111-111111111111', 'admin@disaster.gov.in', '$2b$12$e80yqX3p9qX3p9qX3p9qXe80yqX3p9qX3p9qX3p9qX3p9qX3p9qX3', 'Dr. Rajesh Verma', 'Administrator', 'National Disaster Management Authority', '+91 98765 43210', '+91 98765 00000'),
('22222222-2222-2222-2222-222222222222', 'trainer.sharma@ndrf.gov.in', '$2b$12$e80yqX3p9qX3p9qX3p9qXe80yqX3p9qX3p9qX3p9qX3p9qX3p9qX3', 'Commander Vikram Sharma', 'Trainer', 'NDRF Battalion 1', '+91 98111 22334', '+91 98111 00000'),
('33333333-3333-3333-3333-333333333333', 'trainee.ananya@disaster.org', '$2b$12$e80yqX3p9qX3p9qX3p9qXe80yqX3p9qX3p9qX3p9qX3p9qX3p9qX3', 'Ananya Deshmukh', 'Trainee', 'State Disaster Response Force', '+91 99222 33445', '+91 99222 00000'),
('44444444-4444-4444-4444-444444444444', 'citizen.rahul@gmail.com', '$2b$12$e80yqX3p9qX3p9qX3p9qXe80yqX3p9qX3p9qX3p9qX3p9qX3p9qX3', 'Rahul Nair', 'User', 'Public Citizen (Kochi Basin)', '+91 97333 44556', '+91 97333 00000')
ON CONFLICT (id) DO NOTHING;

-- Seed Safe Shelters (Major High-Elevation Designated Flood Relief Centers)
INSERT INTO safe_shelters (id, name, address, city, state, latitude, longitude, elevation_m, total_capacity, current_occupancy, has_medical_facility, has_power_backup, has_clean_water, contact_phone, is_operational)
VALUES 
('a1111111-1111-1111-1111-111111111111', 'NDRF Regional Shelter 1 - Guwahati Hills', 'Sector 4, Dispur Hill Top', 'Guwahati', 'Assam', 26.1445, 91.7362, 110.0, 1500, 320, TRUE, TRUE, TRUE, '+91 361 223344', TRUE),
('a2222222-2222-2222-2222-222222222222', 'Kochi High Elevation Evacuation Center', 'Hill Palace Road, Tripunithura', 'Kochi', 'Kerala', 9.9468, 76.3533, 42.0, 1200, 480, TRUE, TRUE, TRUE, '+91 484 2778899', TRUE),
('a3333333-3333-3333-3333-333333333333', 'Patna Elevated Disaster Shelter Complex', 'Kankarbagh High Grounds', 'Patna', 'Bihar', 25.5941, 85.1376, 58.0, 2000, 750, TRUE, TRUE, TRUE, '+91 612 2556677', TRUE),
('a4444444-4444-4444-4444-444444444444', 'Mumbai Hillview Relief Center', 'Powai Heights Complex', 'Mumbai', 'Maharashtra', 19.1197, 72.9051, 65.0, 1800, 610, TRUE, TRUE, TRUE, '+91 22 25701122', TRUE),
('a5555555-5555-5555-5555-555555555555', 'Cuttack Mahanadi North Relief Shelter', 'Chahata Ghat Elevation Zone', 'Cuttack', 'Odisha', 20.4625, 85.8828, 38.0, 1400, 290, TRUE, TRUE, TRUE, '+91 671 2309988', TRUE)
ON CONFLICT (id) DO NOTHING;

-- Seed Hazards
INSERT INTO hazards (id, hazard_type, title, description, severity, latitude, longitude, radius_meters, is_active)
VALUES
('h1111111-1111-1111-1111-111111111111', 'ELECTRICAL', 'Submerged High Voltage Transformer 11kV', 'Water level reached 1.8m touching active transformer casing. Severe electrocution zone.', 'CRITICAL', 26.1550, 91.7500, 80.0, TRUE),
('h2222222-2222-2222-2222-222222222222', 'BLOCKED_ROAD', 'National Highway 27 Breach & Debris', 'Heavy sediment and collapsed retaining wall blocking all four lanes.', 'HIGH', 26.1380, 91.7200, 120.0, TRUE),
('h3333333-3333-3333-3333-333333333333', 'DEEP_WATER', 'Mithi River Rapid Current Flash Zone', 'Water velocity exceeding 3.5 m/s with 2.4m depth near bridge culvert.', 'CRITICAL', 19.0750, 72.8770, 100.0, TRUE),
('h4444444-4444-4444-4444-444444444444', 'FALLEN_TREE', 'Uprooted Banyan Tree & Snapped Cables', 'Tree fallen across MG Road obstructing rescue vehicle access.', 'MEDIUM', 9.9816, 76.2999, 45.0, TRUE)
ON CONFLICT (id) DO NOTHING;

-- Seed Flood Zones
INSERT INTO flood_zones (id, zone_name, state, river_basin, center_latitude, center_longitude, radius_km, current_risk_level, flood_probability, water_level_m, flow_velocity_ms, rainfall_accumulated_mm)
VALUES
('z1111111-1111-1111-1111-111111111111', 'Guwahati Brahmaputra Lowlands (Zone A)', 'Assam', 'Brahmaputra Basin', 26.1722, 91.7458, 6.5, 'HIGH', 0.88, 3.4, 2.9, 185.4),
('z2222222-2222-2222-2222-222222222222', 'Ernakulam Urban Canal Basin (Zone B)', 'Kerala', 'Periyar Basin', 9.9816, 76.2999, 5.0, 'MEDIUM', 0.54, 1.6, 1.2, 98.2),
('z3333333-3333-3333-3333-333333333333', 'Patna Ganga Floodplain (Zone C)', 'Bihar', 'Ganges Basin', 25.6120, 85.1440, 8.0, 'HIGH', 0.82, 3.1, 2.5, 142.0),
('z4444444-4444-4444-4444-444444444444', 'Kurla-BKC Lowland Corridor (Zone D)', 'Maharashtra', 'Mithi River Basin', 19.0680, 72.8700, 4.0, 'HIGH', 0.79, 2.8, 1.8, 160.5),
('z5555555-5555-5555-5555-555555555555', 'Cuttack Ring Road Sector (Zone E)', 'Odisha', 'Mahanadi Basin', 20.4625, 85.8828, 5.5, 'LOW', 0.22, 0.6, 0.5, 34.0)
ON CONFLICT (id) DO NOTHING;

-- Seed Emergency Alerts
INSERT INTO emergency_alerts (id, title, message, severity, region, affected_latitude, affected_longitude, radius_km, issued_by, is_active)
VALUES
('e1111111-1111-1111-1111-111111111111', 'FLASH FLOOD RED ALERT: Brahmaputra River Basin', 'River water levels have crossed the danger mark by 1.85m at Guwahati gauge station. Immediate evacuation recommended to designated hill shelters.', 'CRITICAL_EMERGENCY', 'Guwahati / Kamrup Metro', 26.1722, 91.7458, 15.0, 'Central Water Commission & ASDMA', TRUE),
('e2222222-2222-2222-2222-222222222222', 'FLOOD INUNDATION WATCH: Periyar River Downstream', 'Sholayar and Idukki dam spillways operating at 400 m3/s. Low-lying areas in Aluva and Kalamassery on high alert.', 'WATCH', 'Ernakulam / Kochi', 10.1076, 76.3516, 12.0, 'KSDMA Emergency Operations', TRUE)
ON CONFLICT (id) DO NOTHING;
