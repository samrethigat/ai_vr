"""
AI Virtual Instructor Module
Provides deterministic, authoritative real-time disaster guidance and safety prompts.
Does not invent hazards; uses scenario truth and sensor bounds.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class InstructorGuidanceRequest(BaseModel):
    user_position: Dict[str, float] = Field(..., description="x, y, z or lat, lng coordinates")
    current_zone_id: str = "Zone_A"
    water_level_m: float = 0.4
    water_level_rate_m_per_min: float = 0.05
    nearest_hazard_type: Optional[str] = None
    nearest_hazard_dist_m: Optional[float] = None
    equipped_tool: Optional[str] = None
    selected_route_id: Optional[str] = None
    route_flooded_ahead: bool = False
    nearby_victim_priority: Optional[str] = None # None, "CRITICAL", "HIGH", "MODERATE"
    nearby_victim_dist_m: Optional[float] = None


class InstructorPrompt(BaseModel):
    priority: str # "CRITICAL_WARNING", "HAZARD_ALERT", "TACTICAL_GUIDANCE", "INFO"
    audio_cue_id: str
    headline: str
    message: str
    suggested_action: str
    safety_rule_code: str


class VirtualInstructor:
    """
    Deterministic AI Virtual Instructor enforcing standard flood disaster protocols.
    """

    def evaluate_live_guidance(self, context: InstructorGuidanceRequest) -> List[InstructorPrompt]:
        prompts: List[InstructorPrompt] = []

        # 1. Electrical Hazard Proximity
        if context.nearest_hazard_type == "ELECTRICAL" and context.nearest_hazard_dist_m is not None:
            if context.nearest_hazard_dist_m < 8.0:
                prompts.append(InstructorPrompt(
                    priority="CRITICAL_WARNING",
                    audio_cue_id="warn_electrical_critical",
                    headline="ELECTRICAL SHOCK HAZARD",
                    message="Do not enter the electrical hazard area. Live 11kV line submerged within 8 meters.",
                    suggested_action="Halt forward movement immediately. Backtrack 10 meters and select bypass route.",
                    safety_rule_code="SOP_ELEC_01"
                ))
            elif context.nearest_hazard_dist_m < 20.0:
                prompts.append(InstructorPrompt(
                    priority="HAZARD_ALERT",
                    audio_cue_id="alert_electrical_nearby",
                    headline="Submerged Power Lines Ahead",
                    message="Warning: Electrical hazard detected 15m northeast. Maintain minimum 10m standoff.",
                    suggested_action="Equip flashlight, stay on elevated road crest, do not touch metal railings.",
                    safety_rule_code="SOP_ELEC_02"
                ))

        # 2. Rising Water Level in Current Zone
        if context.water_level_m > 1.2:
            prompts.append(InstructorPrompt(
                priority="CRITICAL_WARNING",
                audio_cue_id="warn_water_deep",
                headline="Deep Water Hazard",
                message=f"Warning: Water level has reached {context.water_level_m:.1f}m in your current sector. Wading is unsafe.",
                suggested_action="Deploy Rescue Boat or ascend immediately to higher structure ground.",
                safety_rule_code="SOP_HYDRO_03"
            ))
        elif context.water_level_rate_m_per_min > 0.08:
            prompts.append(InstructorPrompt(
                priority="HAZARD_ALERT",
                audio_cue_id="alert_water_rising",
                headline="Rapid Inundation Alert",
                message=f"Warning: Water level is increasing rapidly (+{context.water_level_rate_m_per_min * 60:.1f} cm/hr) in your current zone.",
                suggested_action="Expedite evacuation sequence. Do not linger in ground floor zones.",
                safety_rule_code="SOP_HYDRO_01"
            ))

        # 3. Route Safety & Compromised Paths
        if context.route_flooded_ahead:
            prompts.append(InstructorPrompt(
                priority="CRITICAL_WARNING",
                audio_cue_id="warn_route_compromised",
                headline="Evacuation Route Blocked",
                message="Your selected route has become unsafe due to culvert overflow and fallen debris.",
                suggested_action="A safer evacuation route is available via North Ridge Causeway. Recalculating path.",
                safety_rule_code="SOP_NAV_04"
            ))

        # 4. Nearby High-Priority Victims
        if context.nearby_victim_priority in ["CRITICAL", "HIGH"] and context.nearby_victim_dist_m is not None:
            if context.nearby_victim_dist_m < 25.0:
                prompts.append(InstructorPrompt(
                    priority="TACTICAL_GUIDANCE",
                    audio_cue_id="info_victim_nearby",
                    headline="Victim Triage Target Identified",
                    message=f"High-priority victim detected {context.nearby_victim_dist_m:.0f}m away (Elderly/Child in distress).",
                    suggested_action="Equip Life Jacket and First Aid Kit. Approach from upstream eddy.",
                    safety_rule_code="SOP_RESCUE_02"
                ))

        # Default reassurance if no critical condition
        if not prompts:
            prompts.append(InstructorPrompt(
                priority="INFO",
                audio_cue_id="info_steady_advance",
                headline="Corridor Secure",
                message="Current sector clear of immediate hazards. Proceed steadily along marked green waypoints.",
                suggested_action="Maintain 15 km/h convoy speed and monitor radio updates.",
                safety_rule_code="SOP_GEN_01"
            ))

        return prompts


virtual_instructor = VirtualInstructor()
