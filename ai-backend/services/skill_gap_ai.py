from typing import Dict, Any, List


class SkillGapAI:

    COMPETENCIES = {
        "safety_awareness": "Safety Awareness",
        "rescue_effectiveness": "Rescue Effectiveness",
        "decision_quality": "Decision Quality",
        "route_efficiency": "Route Efficiency",
        "response_time": "Response Time",
        "communication": "Communication",
        "tool_usage": "Tool Usage",
        "adaptability": "Adaptability"
    }

    TRAINING_MAP = {
        "safety_awareness": "AI_HAZARD_AWARENESS",
        "rescue_effectiveness": "AI_VICTIM_RESCUE",
        "decision_quality": "AI_DECISION_DRILL",
        "route_efficiency": "AI_NAVIGATION",
        "response_time": "AI_RAPID_RESPONSE",
        "communication": "AI_COMMUNICATION",
        "tool_usage": "AI_TOOL_MASTERY",
        "adaptability": "AI_ADAPTABILITY"
    }

    TRAINING_TITLES = {
        "safety_awareness": "Flood Hazard Awareness",
        "rescue_effectiveness": "Victim Rescue Training",
        "decision_quality": "Rapid Disaster Decision-Making",
        "route_efficiency": "Safe Navigation Training",
        "response_time": "Rapid Emergency Response",
        "communication": "Emergency Communication Training",
        "tool_usage": "Emergency Tool Mastery",
        "adaptability": "Adaptive Disaster Response"
    }

    def _severity(self, score: float) -> str:

        if score < 50:
            return "CRITICAL"

        if score < 60:
            return "HIGH"

        if score < 75:
            return "MEDIUM"

        if score < 85:
            return "LOW"

        return "GOOD"

    def _priority(self, score: float) -> int:

        if score < 50:
            return 1

        if score < 60:
            return 2

        if score < 75:
            return 3

        if score < 85:
            return 4

        return 5

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:

        gaps: List[Dict[str, Any]] = []

        for feature, name in self.COMPETENCIES.items():

            score = float(data.get(feature, 0))

            gaps.append({
                "competency": name,
                "feature": feature,
                "score": score,
                "severity": self._severity(score),
                "priority": self._priority(score)
            })

        gaps.sort(key=lambda x: x["score"])

        weakest = gaps[0]

        mistakes = int(data.get("mistakes", 0))
        hazard_violations = int(data.get("hazard_violations", 0))
        decision_time = float(data.get("decision_time_sec", 0))
        reaction_time = float(data.get("reaction_time_sec", 0))

        evidence = []

        if mistakes > 0:
            evidence.append(
                f"{mistakes} mistake(s) recorded during the session"
            )

        if hazard_violations > 0:
            evidence.append(
                f"{hazard_violations} hazard violation(s) detected"
            )

        if weakest["feature"] == "decision_quality" and decision_time > 0:
            evidence.append(
                f"Decision time was {decision_time:.1f} seconds"
            )

        if weakest["feature"] == "response_time" and reaction_time > 0:
            evidence.append(
                f"Reaction time was {reaction_time:.1f} seconds"
            )

        if not evidence:
            evidence.append(
                "Performance score indicates a competency gap"
            )

        training_id = self.TRAINING_MAP[weakest["feature"]]
        training_title = self.TRAINING_TITLES[weakest["feature"]]

        target_score = 80

        return {
            "primary_skill_gap": {
                "competency": weakest["competency"],
                "current_score": weakest["score"],
                "target_score": target_score,
                "severity": weakest["severity"],
                "priority": weakest["priority"]
            },

            "evidence": evidence,

            "all_skill_gaps": gaps,

            "personalized_training": {
                "scenario_id": training_id,
                "scenario_title": training_title,
                "focus": weakest["competency"],
                "target_score": target_score,
                "reason": (
                    f"{weakest['competency']} is currently "
                    f"{weakest['score']:.1f}/100, so targeted "
                    f"training is recommended."
                )
            }
        }


skill_gap_ai = SkillGapAI()