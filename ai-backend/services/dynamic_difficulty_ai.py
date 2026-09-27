"""
AI Dynamic Difficulty Engine

Determines the next training difficulty using:
- Current overall performance
- Weakest skill score
- Current scenario difficulty
"""

DIFFICULTY_LEVELS = {
    "EASY": 1,
    "MEDIUM": 2,
    "HARD": 3,
    "EXTREME": 4
}


def calculate_dynamic_difficulty(
    overall_score: float,
    weakest_skill_score: float,
    current_difficulty: str = "MEDIUM"
) -> dict:
    """
    Calculate personalized next training difficulty.
    """

    current_difficulty = current_difficulty.upper()

    if current_difficulty not in DIFFICULTY_LEVELS:
        current_difficulty = "MEDIUM"

    current_level = DIFFICULTY_LEVELS[current_difficulty]

    # Strong performance in both overall and weakest skill
    if overall_score >= 80 and weakest_skill_score >= 70:
        next_level = min(current_level + 1, 4)
        reason = "Strong overall performance and improved weakest skill."

    # Very weak performance
    elif overall_score < 50 or weakest_skill_score < 40:
        next_level = max(current_level - 1, 1)
        reason = "Performance is below the required level, so difficulty is reduced."

    # Moderate performance
    else:
        next_level = current_level
        reason = "Performance is stable, so the current difficulty is maintained."

    next_difficulty = next(
        level_name
        for level_name, level_number in DIFFICULTY_LEVELS.items()
        if level_number == next_level
    )

    return {
        "current_difficulty": current_difficulty,
        "next_difficulty": next_difficulty,
        "overall_score": round(overall_score, 2),
        "weakest_skill_score": round(weakest_skill_score, 2),
        "reason": reason
    }