"""
ReleaseMind — Deployment Simulator
Replaces deploy.bat with a pure-Python, strategy-aware simulation.

Supports all four ReleaseMind strategies:
  ROLLING | BLUE_GREEN | CANARY | BLOCK
"""

import time
import random
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Strategy-specific simulators
# ---------------------------------------------------------------------------

_STRATEGY_DOCS = {
    "ROLLING": (
        "Replace instances one-by-one with zero downtime. "
        "Ideal for low-risk changes."
    ),
    "BLUE_GREEN": (
        "Spin up a parallel 'green' environment, run smoke tests, "
        "then cut traffic over. Rollback = flip the load-balancer."
    ),
    "CANARY": (
        "Route 5% of traffic to new version. Monitor error rate "
        "and latency for 10 minutes before full promotion."
    ),
    "BLOCK": (
        "Deployment BLOCKED by risk policy. "
        "Resolve all high-risk factors before retrying."
    ),
}


def _simulate_rolling(service: str) -> dict:
    replicas = random.randint(2, 6)
    return {
        "method": "ROLLING",
        "replicas_updated": replicas,
        "downtime_seconds": 0,
        "rollback_available": True,
        "detail": f"Updated {replicas} replica(s) of '{service}' one by one.",
    }


def _simulate_blue_green(service: str) -> dict:
    smoke_tests_passed = random.randint(5, 10)
    return {
        "method": "BLUE_GREEN",
        "green_env": f"{service}-green",
        "smoke_tests_passed": smoke_tests_passed,
        "traffic_switched": True,
        "rollback_available": True,
        "detail": (
            f"Green env '{service}-green' promoted after "
            f"{smoke_tests_passed} smoke tests."
        ),
    }


def _simulate_canary(service: str) -> dict:
    canary_pct = 5
    error_rate = round(random.uniform(0.0, 2.5), 2)
    promoted = error_rate < 2.0
    return {
        "method": "CANARY",
        "canary_traffic_pct": canary_pct,
        "observed_error_rate_pct": error_rate,
        "promoted_to_full": promoted,
        "rollback_available": True,
        "detail": (
            f"{canary_pct}% canary observed {error_rate}% error rate → "
            + ("promoted to 100%." if promoted else "held — manual review needed.")
        ),
    }


def _simulate_block(reason: str = "High risk score") -> dict:
    return {
        "method": "BLOCK",
        "blocked": True,
        "reason": reason,
        "detail": (
            "Deployment stopped by ReleaseMind governance policy. "
            "Review risk breakdown and remediation recommendations."
        ),
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def deploy(
    strategy: str,
    service: str = "app",
    deployment_id: int | None = None,
    block_reason: str = "High risk score",
) -> dict:
    """
    Simulate a deployment using the chosen strategy.

    Args:
        strategy:       ROLLING | BLUE_GREEN | CANARY | BLOCK
        service:        Name of the service being deployed
        deployment_id:  DB deployment ID (for traceability)
        block_reason:   Human-readable reason when strategy == BLOCK

    Returns a structured dict describing the simulated outcome.
    """
    strategy = strategy.upper()
    start = time.monotonic()

    sim_map = {
        "ROLLING":    lambda: _simulate_rolling(service),
        "BLUE_GREEN": lambda: _simulate_blue_green(service),
        "CANARY":     lambda: _simulate_canary(service),
        "BLOCK":      lambda: _simulate_block(block_reason),
    }

    if strategy not in sim_map:
        raise ValueError(
            f"Unknown strategy '{strategy}'. "
            f"Valid options: {list(sim_map.keys())}"
        )

    result = sim_map[strategy]()
    elapsed = round(time.monotonic() - start, 3)

    status = "blocked" if strategy == "BLOCK" else "success"

    return {
        "deployment_id":    deployment_id,
        "service":          service,
        "strategy":         strategy,
        "strategy_info":    _STRATEGY_DOCS[strategy],
        "status":           status,
        "simulation":       result,
        "elapsed_seconds":  elapsed,
        "timestamp":        datetime.now(timezone.utc).isoformat(),
    }
