"""
Reference table of industry-standard ranges for common contract provisions.
Values are in consistent units (days) so comparisons are simple math, not string parsing.
Based on commonly cited commercial contract norms (informational reference only —
not a substitute for legal advice).
"""

# Each entry: (standard_min_days, standard_max_days, red_below_days, red_above_days)
# A provision is "green" inside [standard_min, standard_max],
# "yellow" between red threshold and standard range,
# "red" beyond the red threshold. None means no bound in that direction.
BENCHMARKS = {
    "liability_cap": {
        "label": "Liability Cap (in months of fees, treated as days for math: 1 month = 30 days)",
        "standard_min": 330,   # ~11 months
        "standard_max": 365,   # 12 months
        "red_below": 180,      # below 6 months = red
        "red_above": None,
    },
    "auto_renewal_notice": {
        "label": "Auto-Renewal Notice Period",
        "standard_min": 90,
        "standard_max": 180,
        "red_below": 60,
        "red_above": None,
    },
    "termination_notice": {
        "label": "Termination Notice Period",
        "standard_min": 60,
        "standard_max": 90,
        "red_below": 30,
        "red_above": None,
    },
    "non_compete_duration": {
        "label": "Non-Compete Duration",
        "standard_min": 365,       # 1 year
        "standard_max": 730,       # 2 years
        "red_below": None,
        "red_above": 1825,         # 5+ years = red
    },
    "confidentiality_duration": {
        "label": "Confidentiality / NDA Term",
        "standard_min": 1095,      # 3 years
        "standard_max": 1825,      # 5 years
        "red_below": 730,          # below 2 years = red
        "red_above": None,
    },
    "cure_period": {
        "label": "Cure Period (time to fix a breach before termination)",
        "standard_min": 15,
        "standard_max": 30,
        "red_below": None,
        "red_above": None,
    },
}


def evaluate_status(provision_key: str, value_days: float) -> str:
    """Returns 'green' | 'yellow' | 'red' | 'unknown' for a given extracted value."""
    bench = BENCHMARKS.get(provision_key)
    if not bench or value_days is None:
        return "unknown"

    if bench["standard_min"] <= value_days <= bench["standard_max"]:
        return "green"

    if bench["red_below"] is not None and value_days < bench["red_below"]:
        return "red"
    if bench["red_above"] is not None and value_days > bench["red_above"]:
        return "red"

    return "yellow"