"""
Adaptive Learning & Personalized Training Path Engine

Rules from System Architecture:
  - If Safety < 60: Repeat hazard awareness training.
  - If Rescue < 60: Create a focused victim rescue scenario.
  - If Route < 60: Provide guided navigation training.
  - If Response Time < 60: Create timed precision tasks after basic safety is improved.
  - If all scores >= 85: Increase flood severity and scenario complexity.
"""

from typing import Dict, Any, List
from pydantic import BaseModel


class AdaptiveCurriculum(BaseModel):
    recommended_scenario_id: str
    scenario_title: str
    target_difficulty: str
    focus_competency: str
    rationale: str
    scenario_parameters: Dict[str, Any]
    unlock_badge: str
    learning_objectives: List[str]


def generate_adaptive_curriculum(competencies, current_difficulty: str = "MEDIUM") -> Dict[str, Any]:
    """
    Evaluates trainee competency vector and synthesizes the optimal next training scenario.
    """
    safety = competencies.safety_awareness
    rescue = competencies.rescue_effectiveness
    route = competencies.route_efficiency
    response = competencies.response_time
    decision = competencies.decision_quality
    overall = competencies.overall_score

    # Check if all scores >= 85
    all_scores = [
        competencies.safety_awareness,
        competencies.rescue_effectiveness,
        competencies.decision_quality,
        competencies.route_efficiency,
        competencies.response_time,
        competencies.communication,
        competencies.tool_usage,
        competencies.adaptability
    ]

    if all(s >= 85.0 for s in all_scores):
        return {
            "recommended_scenario_id": "SCEN_EXTREME_MULTI_HAZARD",
            "scenario_title": "Brahmaputra Dam Spillway Breach & Extreme Urban Deluge",
            "target_difficulty": "EXTREME",
            "focus_competency": "Multi-Hazard Crisis Mastery & High-Speed Extraction",
            "rationale": "Outstanding performance across all 8 competency metrics (>85%). Escalating to Category 5 multi-hazard surge with active electrical grid failures and night-time navigation.",
            "scenario_parameters": {
                "water_rise_rate_m_per_min": 0.18,
                "current_velocity_ms": 3.8,
                "electrical_hazards_count": 5,
                "total_victims": 8,
                "time_limit_sec": 300,
                "visibility_meters": 15.0,
                "night_mode": True
            },
            "unlock_badge": "NDRF Elite First Responder",
            "learning_objectives": [
                "Execute night-time boat extraction under 3.5 m/s river current",
                "Isolate active high-voltage substation perimeter in floodwaters",
                "Coordinate multi-casualty triage under strict 5-minute countdown"
            ]
        }

    # Rule 1: Safety < 60
    if safety < 60.0:
        return {
            "recommended_scenario_id": "SCEN_HAZARD_AWARENESS_REPLAY",
            "scenario_title": "Hazard Awareness & Submerged Utility Isolation",
            "target_difficulty": "EASY",
            "focus_competency": "Safety Awareness & Electrical Stand-Off",
            "rationale": f"Safety awareness score ({safety:.1f}/100) is below operational benchmark. Repetition of utility identification and hazard perimeter management is mandatory before advanced rescue.",
            "scenario_parameters": {
                "water_rise_rate_m_per_min": 0.03,
                "current_velocity_ms": 0.8,
                "electrical_hazards_count": 4,
                "total_victims": 2,
                "time_limit_sec": 420,
                "night_mode": False,
                "show_hazard_bounding_boxes": True
            },
            "unlock_badge": "Safety Protocol Certified",
            "learning_objectives": [
                "Identify submerged electrical transformer signatures at >10m range",
                "Use insulated probes and visual inspection before wading",
                "Maintain 0 hazard encroachment violations throughout route"
            ]
        }

    # Rule 2: Rescue < 60
    if rescue < 60.0:
        return {
            "recommended_scenario_id": "SCEN_FOCUSED_VICTIM_RESCUE",
            "scenario_title": "Priority Casualty Triage & Flotation Deployment",
            "target_difficulty": "MEDIUM",
            "focus_competency": "Rescue Effectiveness & Equipment Deployment",
            "rationale": f"Rescue effectiveness score ({rescue:.1f}/100) indicates delayed triage or missed casualty extraction. Focused victim rescue drills required.",
            "scenario_parameters": {
                "water_rise_rate_m_per_min": 0.05,
                "current_velocity_ms": 1.2,
                "electrical_hazards_count": 1,
                "total_victims": 6,
                "time_limit_sec": 360,
                "night_mode": False,
                "enable_triage_hints": True
            },
            "unlock_badge": "Rescue Specialist",
            "learning_objectives": [
                "Prioritize red-tag critical casualties (unconscious / pediatric)",
                "Deploy life vest and throw rope within 12 seconds of contact",
                "Secure 100% of trapped civilians to elevated relief craft"
            ]
        }

    # Rule 3: Route < 60
    if route < 60.0:
        return {
            "recommended_scenario_id": "SCEN_GUIDED_NAVIGATION",
            "scenario_title": "Topographic Navigation & Dynamic Ridge Evacuation",
            "target_difficulty": "MEDIUM",
            "focus_competency": "Route Efficiency & Elevated Ground Selection",
            "rationale": f"Route efficiency score ({route:.1f}/100) reflects inefficient path choices into flooded lowlands. Providing guided elevation waypoint drills.",
            "scenario_parameters": {
                "water_rise_rate_m_per_min": 0.06,
                "current_velocity_ms": 1.5,
                "electrical_hazards_count": 2,
                "total_victims": 3,
                "time_limit_sec": 300,
                "display_elevation_contour_hud": True
            },
            "unlock_badge": "Master Navigator",
            "learning_objectives": [
                "Follow A* optimal ridge routes avoiding submerged culverts",
                "Identify alternative bypasses when primary arterial is flooded",
                "Reach designated high-ground shelter with <5% path deviation"
            ]
        }

    # Rule 4: Response Time < 60
    if response < 60.0:
        return {
            "recommended_scenario_id": "SCEN_TIMED_RAPID_RESPONSE",
            "scenario_title": "Flash Inundation Rapid Sprint & Evacuation Drills",
            "target_difficulty": "HARD",
            "focus_competency": "Response Time & Urgent Decision Agility",
            "rationale": f"Response latency score ({response:.1f}/100) exceeds permissible window for sudden dam release or flash flood events. Timed precision modules activated.",
            "scenario_parameters": {
                "water_rise_rate_m_per_min": 0.12,
                "current_velocity_ms": 2.2,
                "electrical_hazards_count": 2,
                "total_victims": 4,
                "time_limit_sec": 180,
                "enable_countdown_timer": True
            },
            "unlock_badge": "Rapid Response Commendation",
            "learning_objectives": [
                "Complete full casualty extraction under 180 seconds",
                "Equip appropriate rescue gear within 5 seconds of alert",
                "Execute swift decision-making without compromising basic safety"
            ]
        }

    # Standard intermediate progression
    next_diff = "HARD" if current_difficulty == "MEDIUM" else ("MEDIUM" if current_difficulty == "EASY" else "EXTREME")
    return {
        "recommended_scenario_id": f"SCEN_URBAN_INUNDATION_{next_diff}",
        "scenario_title": f"Urban Inundation & Multi-Tier Relief ({next_diff} Tier)",
        "target_difficulty": next_diff,
        "focus_competency": "Integrated Command & Multi-Sector Coordination",
        "rationale": f"Solid foundational performance (Overall Score: {overall:.1f}/100). Advancing to {next_diff} tier scenario with dynamic road closures and changing river stages.",
        "scenario_parameters": {
            "water_rise_rate_m_per_min": 0.08,
            "current_velocity_ms": 2.0,
            "electrical_hazards_count": 3,
            "total_victims": 5,
            "time_limit_sec": 260
        },
        "unlock_badge": "Senior Disaster Responder",
        "learning_objectives": [
            "Demonstrate balanced execution across all 8 competency metrics",
            "Respond dynamically to mid-mission route compromises",
            "Achieve >80% overall score on higher difficulty tier"
        ]
    }
