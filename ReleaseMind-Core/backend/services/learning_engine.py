"""
ReleaseMind — Historical Learning Engine
Analyzes past deployment outcomes to adapt risk scoring dynamically.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import db
from config_loader import load_config

_cfg = load_config()
_w = _cfg.get("weights", {})

# Risk band boundaries (must match thresholds in risk_config.yaml)
RISK_BANDS = [
    (0, 8, "low"),
    (8, 14, "medium"),
    (14, 20, "high"),
    (20, float("inf"), "critical"),
]


def _classify_band(score: float) -> str:
    for lo, hi, label in RISK_BANDS:
        if lo <= score < hi:
            return label
    return "critical"


def get_similar_failure_rate(risk_score: float, service: str) -> dict:
    """
    Fetch deployments in the same risk band for the same service,
    compute their failure rate, and return a structured insight.

    Returns:
        {
          "similar_count": int,
          "similar_failures": int,
          "similar_failure_rate": float,
          "risk_band": str,
          "additional_risk": float,
          "recommendation": str
        }
    """
    band = _classify_band(risk_score)

    # Band lower/upper bounds
    for lo, hi, label in RISK_BANDS:
        if label == band:
            lo_bound, hi_bound = lo, hi
            break
    else:
        lo_bound, hi_bound = 0, 8

    # Query DB for similar deployments
    all_deployments = db.get_recent_deployments(limit=200)
    similar = [
        d for d in all_deployments
        if d.get("service") == service
        and lo_bound <= (d.get("risk_score") or 0) < hi_bound
        and d.get("outcome") in ("success", "failure")
    ]

    count = len(similar)
    failures = sum(1 for d in similar if d.get("outcome") == "failure")
    failure_rate = (failures / count) if count > 0 else 0.0

    # Additional risk penalty
    penalty_threshold = _w.get("failure_rate_multiplier", 3.0)
    additional_risk = 0.0
    if failure_rate > 0.5 and count >= 3:
        additional_risk = 4.0  # Significant historical penalty
        recommendation = (
            f"⚠️ {failures}/{count} similar deployments failed for '{service}' "
            f"in the {band.upper()} band. Extended monitoring strongly advised."
        )
    elif failure_rate > 0.25 and count >= 2:
        additional_risk = 2.0
        recommendation = (
            f"⚡ {failures}/{count} similar deployments failed. "
            f"Consider canary rollout for '{service}'."
        )
    elif count == 0:
        recommendation = f"No historical data for '{service}' in {band.upper()} band. Proceeding with caution."
    else:
        recommendation = (
            f"✅ {count} similar deployments for '{service}' in {band.upper()} band, "
            f"failure rate: {failure_rate:.0%}. Risk looks manageable."
        )

    return {
        "similar_count": count,
        "similar_failures": failures,
        "similar_failure_rate": round(failure_rate, 3),
        "risk_band": band,
        "additional_risk": additional_risk,
        "recommendation": recommendation,
    }


def get_service_trend(service: str, limit: int = 10) -> dict:
    """
    Analyse the trend of recent deployments for a service.

    Returns:
        {
          "trend": "improving" | "degrading" | "stable" | "no_data",
          "recent_avg_risk": float,
          "older_avg_risk": float,
          "delta": float
        }
    """
    all_deploys = db.get_recent_deployments(limit=200)
    service_deploys = [
        d for d in all_deploys
        if d.get("service") == service and d.get("risk_score") is not None
    ]

    if len(service_deploys) < 2:
        return {"trend": "no_data", "recent_avg_risk": 0.0, "older_avg_risk": 0.0, "delta": 0.0}

    half = max(1, len(service_deploys) // 2)
    recent = service_deploys[:half]
    older = service_deploys[half:]

    recent_avg = sum(d["risk_score"] for d in recent) / len(recent)
    older_avg = sum(d["risk_score"] for d in older) / len(older)
    delta = round(recent_avg - older_avg, 2)

    if delta < -1.0:
        trend = "improving"
    elif delta > 1.0:
        trend = "degrading"
    else:
        trend = "stable"

    return {
        "trend": trend,
        "recent_avg_risk": round(recent_avg, 2),
        "older_avg_risk": round(older_avg, 2),
        "delta": delta,
    }
