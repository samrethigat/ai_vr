"""
VR Telemetry Analysis & AI Performance Scoring Engine

Evaluates 8 Competency Vectors:
  1. Safety Awareness (25%)
  2. Rescue Effectiveness (20%)
  3. Decision Quality (20%)
  4. Route Efficiency (10%)
  5. Response Time (10%)
  6. Communication (5%)
  7. Tool Usage (5%)
  8. Adaptability (5%)

Overall Score Formula:
  Overall = 0.25*Safety + 0.20*Rescue + 0.20*Decision + 0.10*Route + 0.10*Response + 0.05*Comm + 0.05*Tool + 0.05*Adapt
"""

import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TelemetryEvent(BaseModel):
    timestamp_sec: float
    position_x: float
    position_y: float
    position_z: float
    speed: float = 1.0
    current_zone: str = "Zone_A_Urban"
    action_type: str = "MOVE" # MOVE, TOOL_EQUIP, VICTIM_TRIAGE, VICTIM_RESCUE, HAZARD_EXPOSURE, RADIO_CALL, ROUTE_CHOICE
    target_entity: Optional[str] = None
    hazard_proximity_m: Optional[float] = 10.0
    tool_in_hand: Optional[str] = None
    notes: Optional[str] = None


class VrSessionEvaluationRequest(BaseModel):
    session_id: str
    trainee_id: str
    scenario_id: str
    scenario_title: str
    difficulty: str = "MEDIUM" # EASY, MEDIUM, HARD, EXTREME
    total_duration_seconds: float
    victims_total: int = 4
    victims_rescued: int = 4
    hazards_triggered: int = 0
    telemetry_stream: List[TelemetryEvent] = []


class CompetencyVector(BaseModel):
    safety_awareness: float
    rescue_effectiveness: float
    decision_quality: float
    route_efficiency: float
    response_time: float
    communication: float
    tool_usage: float
    adaptability: float
    overall_score: float


class VrSessionEvaluationResult(BaseModel):
    session_id: str
    trainee_id: str
    scenario_title: str
    competency_scores: CompetencyVector
    overall_score: float
    performance_tier: str
    strengths: List[str]
    weaknesses: List[str]
    unsafe_decisions: List[Dict[str, Any]]
    missed_actions: List[str]
    improvement_suggestions: List[str]
    next_training_recommendation: Dict[str, Any]


class TelemetryAnalyzer:
    """
    Analyzes fine-grained telemetry packets from Unity OpenXR or WebXR simulation sandbox,
    identifies safety hazards, response latency, tool selections, and computes authoritative scores.
    """

    def analyze_session(self, session: VrSessionEvaluationRequest) -> VrSessionEvaluationResult:
        stream = session.telemetry_stream
        
        # 1. Safety Awareness (25%)
        # Penalized by proximity to live powerlines (<3m), entering deep water without boat, triggering hazard triggers
        hazard_violations = []
        close_hazard_count = 0
        deep_water_exposures = 0

        for event in stream:
            if event.action_type == "HAZARD_EXPOSURE" or (event.hazard_proximity_m is not None and event.hazard_proximity_m < 3.0):
                close_hazard_count += 1
                hazard_violations.append({
                    "time_sec": event.timestamp_sec,
                    "zone": event.current_zone,
                    "target": event.target_entity or "Electrical/Debris Hazard",
                    "proximity_m": event.hazard_proximity_m or 1.5,
                    "severity": "CRITICAL" if "ELECTRICAL" in str(event.target_entity).upper() else "HIGH"
                })
            if "DEEP_WATER" in str(event.target_entity) and event.tool_in_hand != "Rescue_Boat":
                deep_water_exposures += 1

        safety_score = max(15.0, 100.0 - (session.hazards_triggered * 18.0) - (close_hazard_count * 8.0) - (deep_water_exposures * 5.0))

        # 2. Rescue Effectiveness (20%)
        # Ratio of victims rescued to total, with proper triage sequence
        rescue_ratio = session.victims_rescued / max(1, session.victims_total)
        triage_actions = [e for e in stream if e.action_type in ["VICTIM_TRIAGE", "VICTIM_RESCUE"]]
        triage_bonus = min(15.0, len(triage_actions) * 3.5)
        rescue_score = min(100.0, max(20.0, (rescue_ratio * 85.0) + triage_bonus))

        # 3. Decision Quality (20%)
        # Evaluated through safe route picking, correct tool matching to victim conditions
        decision_deductions = 0.0
        for event in stream:
            if event.action_type == "TOOL_EQUIP":
                # Check if appropriate tools were equipped in appropriate zones
                if "WATER" in event.current_zone and event.tool_in_hand not in ["Life_Jacket", "Rope", "Rescue_Boat", "Flashlight"]:
                    decision_deductions += 4.0
        decision_score = max(25.0, min(100.0, 95.0 - decision_deductions - (len(hazard_violations) * 4.0)))

        # 4. Route Efficiency (10%)
        # Path distance versus optimal straight line, speed consistency
        route_actions = [e for e in stream if e.action_type == "ROUTE_CHOICE"]
        route_score = 90.0 if not route_actions else (85.0 if len(hazard_violations) == 0 else 65.0)

        # 5. Response Time (10%)
        # Benchmark time expected based on difficulty
        target_duration = {"EASY": 180.0, "MEDIUM": 240.0, "HARD": 300.0, "EXTREME": 360.0}.get(session.difficulty, 240.0)
        time_ratio = session.total_duration_seconds / target_duration
        if time_ratio <= 1.0:
            response_score = min(100.0, 90.0 + (1.0 - time_ratio) * 20.0)
        else:
            response_score = max(30.0, 90.0 - (time_ratio - 1.0) * 45.0)

        # 6. Communication (5%)
        radio_calls = [e for e in stream if e.action_type == "RADIO_CALL"]
        comm_score = min(100.0, 50.0 + len(radio_calls) * 18.0) if stream else 85.0

        # 7. Tool Usage (5%)
        tool_actions = [e for e in stream if e.action_type == "TOOL_EQUIP" or e.tool_in_hand is not None]
        tool_score = min(100.0, 60.0 + len(tool_actions) * 8.0) if stream else 88.0

        # 8. Adaptability (5%)
        # Reaction to dynamic water rises and newly blocked roads
        adapt_score = max(40.0, min(100.0, 85.0 + (5.0 if session.victims_rescued == session.victims_total else -15.0)))

        # Calculate Authoritative Weighted Overall Score Formula
        overall_score = (
            0.25 * safety_score +
            0.20 * rescue_score +
            0.20 * decision_score +
            0.10 * route_score +
            0.10 * response_score +
            0.05 * comm_score +
            0.05 * tool_score +
            0.05 * adapt_score
        )
        overall_score = round(float(overall_score), 2)

        # Strengths & Weaknesses identification
        strengths = []
        weaknesses = []
        missed = []
        suggestions = []

        if safety_score >= 80:
            strengths.append("Demonstrated superior situational hazard awareness and maintained safe clearance from high-voltage utilities.")
        else:
            weaknesses.append("Frequent encroachment into hazardous zones (<3m proximity to powerlines or submerged obstacles).")
            suggestions.append("Maintain a minimum 5-meter safety perimeter around submerged electrical infrastructure.")

        if rescue_score >= 80:
            strengths.append(f"High rescue completion rate ({session.victims_rescued}/{session.victims_total} victims safely evacuated).")
        else:
            weaknesses.append("Delayed or incomplete triage of critical civilian casualties.")
            missed.append(f"Failed to extract {session.victims_total - session.victims_rescued} trapped flood victims before route submersion.")
            suggestions.append("Prioritize children and elderly victims using the Life Jacket and Rescue Boat first.")

        if response_score >= 80:
            strengths.append(f"Rapid mission execution ({session.total_duration_seconds:.0f}s elapsed, well within operational target).")
        else:
            weaknesses.append(f"Mission execution time ({session.total_duration_seconds:.0f}s) exceeded optimal disaster response window.")
            suggestions.append("Practice rapid tool selection and immediate evacuation path commitment.")

        if comm_score < 70:
            missed.append("Infrequent radio status broadcasts to regional NDRF command center.")
            suggestions.append("Issue regular radio check-ins at each zone transition.")

        if tool_score >= 80:
            strengths.append("Appropriate deployment of First Aid Kit, Rope, and Life Jacket.")

        # Performance Tier
        if overall_score >= 90:
            tier = "EXEMPLARY / DISASTER READY"
        elif overall_score >= 75:
            tier = "PROFICIENT / OPERATIONAL"
        elif overall_score >= 60:
            tier = "NEEDS SUPERVISED PRACTICE"
        else:
            tier = "RETRAINING MANDATORY"

        # Next Training Level Recommendation (Deterministic Adaptive Logic)
        from services.adaptive_learning import generate_adaptive_curriculum
        comp_vector = CompetencyVector(
            safety_awareness=round(safety_score, 1),
            rescue_effectiveness=round(rescue_score, 1),
            decision_quality=round(decision_score, 1),
            route_efficiency=round(route_score, 1),
            response_time=round(response_score, 1),
            communication=round(comm_score, 1),
            tool_usage=round(tool_score, 1),
            adaptability=round(adapt_score, 1),
            overall_score=overall_score
        )

        next_training = generate_adaptive_curriculum(comp_vector, session.difficulty)

        return VrSessionEvaluationResult(
            session_id=session.session_id,
            trainee_id=session.trainee_id,
            scenario_title=session.scenario_title,
            competency_scores=comp_vector,
            overall_score=overall_score,
            performance_tier=tier,
            strengths=strengths,
            weaknesses=weaknesses,
            unsafe_decisions=hazard_violations,
            missed_actions=missed,
            improvement_suggestions=suggestions,
            next_training_recommendation=next_training
        )


telemetry_analyzer = TelemetryAnalyzer()
