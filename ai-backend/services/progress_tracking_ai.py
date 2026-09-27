"""
Progress Tracking AI

Compares previous and current trainee performance.
"""


def calculate_progress(previous_score: float, current_score: float) -> dict:
    improvement = current_score - previous_score

    if improvement > 5:
        status = "IMPROVED"
        message = "Trainee performance has improved."

    elif improvement < -5:
        status = "DECLINED"
        message = "Trainee performance has declined."

    else:
        status = "STABLE"
        message = "Trainee performance is stable."

    return {
        "previous_score": round(previous_score, 2),
        "current_score": round(current_score, 2),
        "improvement": round(improvement, 2),
        "status": status,
        "message": message
    }