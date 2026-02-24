"""
ReleaseMind — Remediation Engine
Translates risk breakdown into structured, actionable recommendations.
"""


# Severity thresholds for each risk dimension
_THRESHOLDS = {
    "code_size":      {"high": 4.0, "medium": 2.0},
    "commit_intent":  {"high": 6.0, "medium": 3.0},
    "developer":      {"high": 3.0, "medium": 1.5},
    "dependency":     {"high": 4.0, "medium": 2.0},
    "history":        {"high": 4.0, "medium": 2.0},
    "environment":    {"high": 4.0, "medium": 2.0},
    "infrastructure": {"high": 3.0, "medium": 1.5},
    "timing":         {"high": 3.0, "medium": 1.0},
}

_RECOMMENDATIONS = {
    "code_size": {
        "high": {
            "title": "🔪 Split into smaller PRs",
            "detail": "This commit is very large. Break it into 2-3 focused PRs to reduce cognitive load and blast radius.",
            "priority": "HIGH",
            "action": "split_pr",
        },
        "medium": {
            "title": "📋 Request additional code review",
            "detail": "The code change size is moderate. Ensure at least 2 reviewers have approved before merging.",
            "priority": "MEDIUM",
            "action": "extra_review",
        },
    },
    "commit_intent": {
        "high": {
            "title": "🧪 Run full regression suite",
            "detail": "Refactors and breaking changes carry high implicit risk. Run a full regression test before deploying.",
            "priority": "HIGH",
            "action": "full_regression",
        },
        "medium": {
            "title": "✅ Run targeted integration tests",
            "detail": "Feature commits should pass integration tests covering affected modules.",
            "priority": "MEDIUM",
            "action": "integration_tests",
        },
    },
    "developer": {
        "high": {
            "title": "👥 Assign senior reviewer",
            "detail": "Contributor has limited experience or does not own this service. Assign a senior engineer as co-reviewer.",
            "priority": "HIGH",
            "action": "senior_review",
        },
        "medium": {
            "title": "🔍 Pair deployment recommended",
            "detail": "Consider pairing this deployment with the service owner for guidance.",
            "priority": "MEDIUM",
            "action": "pair_deploy",
        },
    },
    "dependency": {
        "high": {
            "title": "🐤 Use Canary or Staged Rollout",
            "detail": "High dependency depth means failures can cascade. Deploy to 5% of traffic first and monitor for 30 minutes.",
            "priority": "HIGH",
            "action": "canary_rollout",
        },
        "medium": {
            "title": "🔵 Prefer Blue-Green deployment",
            "detail": "Moderate dependency impact. Use blue-green strategy to allow instant rollback if downstream issues occur.",
            "priority": "MEDIUM",
            "action": "blue_green",
        },
    },
    "history": {
        "high": {
            "title": "🔔 Enable extended monitoring",
            "detail": "Similar commits have failed before. Enable alerts and set a 2-hour observation window post-deployment.",
            "priority": "HIGH",
            "action": "extended_monitoring",
        },
        "medium": {
            "title": "📊 Increase observability",
            "detail": "Historical failure rate is above baseline. Ensure dashboards and error budgets are under watch.",
            "priority": "MEDIUM",
            "action": "increase_observability",
        },
    },
    "environment": {
        "high": {
            "title": "⚙️ Resolve config drift first",
            "detail": "Configuration drift detected. Reconcile environment configs before deploying to prevent unexpected behavior.",
            "priority": "HIGH",
            "action": "resolve_config_drift",
        },
        "medium": {
            "title": "🔎 Validate environment parity",
            "detail": "Some drift detected between environments. Verify staging closely mirrors production.",
            "priority": "MEDIUM",
            "action": "validate_env_parity",
        },
    },
    "infrastructure": {
        "high": {
            "title": "⏳ Delay deployment — system under load",
            "detail": "CPU or Memory is above safe threshold. Schedule deployment during low-traffic window.",
            "priority": "HIGH",
            "action": "delay_deployment",
        },
        "medium": {
            "title": "📉 Monitor resource headroom",
            "detail": "System resources are elevated. Ensure auto-scaling is active before deploying.",
            "priority": "MEDIUM",
            "action": "monitor_resources",
        },
    },
    "timing": {
        "high": {
            "title": "🕐 Reschedule to off-peak hours",
            "detail": "Deploying during peak traffic or on weekends increases blast radius. Reschedule to a maintenance window.",
            "priority": "HIGH",
            "action": "reschedule",
        },
        "medium": {
            "title": "🗓️ Consider off-hours deployment",
            "detail": "Timing is non-ideal. Consider scheduling for a lower-traffic period.",
            "priority": "MEDIUM",
            "action": "consider_rescheduling",
        },
    },
}


def generate_recommendations(risk_breakdown: dict) -> dict:
    """
    Generate ordered, structured recommendations based on risk breakdown.

    Args:
        risk_breakdown: dict returned by calculate_risk()

    Returns:
        {
          "recommendations": [
            {
              "title": str,
              "detail": str,
              "priority": "HIGH" | "MEDIUM",
              "dimension": str,
              "action": str,
              "score": float
            }
          ],
          "critical_count": int,
          "medium_count": int,
          "overall_posture": str
        }
    """
    recommendations = []

    for dimension, advice_levels in _RECOMMENDATIONS.items():
        score = risk_breakdown.get(dimension, 0.0)
        hi = _THRESHOLDS[dimension]["high"]
        med = _THRESHOLDS[dimension]["medium"]

        if score >= hi:
            rec = advice_levels["high"].copy()
            rec["dimension"] = dimension
            rec["score"] = round(score, 2)
            recommendations.append(rec)
        elif score >= med:
            rec = advice_levels["medium"].copy()
            rec["dimension"] = dimension
            rec["score"] = round(score, 2)
            recommendations.append(rec)

    # Sort: HIGH first, then by score descending
    recommendations.sort(key=lambda r: (r["priority"] != "HIGH", -r["score"]))

    high_count = sum(1 for r in recommendations if r["priority"] == "HIGH")
    medium_count = sum(1 for r in recommendations if r["priority"] == "MEDIUM")

    total_risk = risk_breakdown.get("total", 0)
    if total_risk >= 20:
        posture = "CRITICAL — Block recommended"
    elif total_risk >= 14:
        posture = "HIGH RISK — Canary rollout required"
    elif total_risk >= 8:
        posture = "MODERATE — Blue-Green preferred"
    else:
        posture = "ACCEPTABLE — Rolling deployment safe"

    return {
        "recommendations": recommendations,
        "critical_count": high_count,
        "medium_count": medium_count,
        "overall_posture": posture,
    }
