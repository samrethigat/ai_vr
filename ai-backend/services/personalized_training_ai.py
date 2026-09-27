"""
Personalized Training AI

Selects a training scenario based on:
- Weakest competency
- Recommended difficulty
"""

TRAINING_SCENARIOS = {
    "Safety Awareness": {
        "scenario_id": "AI_HAZARD_AWARENESS",
        "title": "Hazard Awareness Training"
    },
    "Rescue Effectiveness": {
        "scenario_id": "AI_VICTIM_RESCUE",
        "title": "Victim Rescue Training"
    },
    "Decision Quality": {
        "scenario_id": "AI_DECISION_DRILL",
        "title": "Rapid Disaster Decision-Making"
    },
    "Route Efficiency": {
        "scenario_id": "AI_NAVIGATION",
        "title": "Safe Navigation Training"
    },
    "Response Time": {
        "scenario_id": "AI_RAPID_RESPONSE",
        "title": "Rapid Emergency Response"
    },
    "Communication": {
        "scenario_id": "AI_COMMUNICATION",
        "title": "Emergency Communication Training"
    },
    "Tool Usage": {
        "scenario_id": "AI_TOOL_MASTERY",
        "title": "Emergency Tool Mastery"
    },
    "Adaptability": {
        "scenario_id": "AI_ADAPTABILITY",
        "title": "Adaptive Disaster Response"
    }
}


def select_personalized_training(
    weakest_competency: str,
    difficulty: str
) -> dict:

    scenario = TRAINING_SCENARIOS.get(
        weakest_competency,
        TRAINING_SCENARIOS["Safety Awareness"]
    )

    return {
        "scenario_id": scenario["scenario_id"],
        "scenario_title": scenario["title"],
        "difficulty": difficulty.upper(),
        "focus_competency": weakest_competency,
        "reason": (
            f"Training selected to improve "
            f"{weakest_competency}."
        )
    }