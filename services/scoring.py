LEVEL_DEFAULT_SCORE = {"low": 20, "medium": 60, "high": 90}


def compute_overall_risk(risk_flags: list) -> tuple:
    """Averages per-flag numeric risk scores into a single 0-100 score and a letter grade."""
    scores = [
        f["risk_score"] if isinstance(f.get("risk_score"), (int, float))
        else LEVEL_DEFAULT_SCORE.get(f.get("risk_level", "").lower(), 50)
        for f in risk_flags
    ]
    if not scores:
        return 0, "N/A"
    avg = sum(scores) / len(scores)
    if avg <= 20:
        grade = "A"
    elif avg <= 40:
        grade = "B"
    elif avg <= 60:
        grade = "C"
    elif avg <= 80:
        grade = "D"
    else:
        grade = "F"
    return round(avg), grade