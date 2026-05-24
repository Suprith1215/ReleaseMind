"""
ReleaseMind — CI Pipeline Simulator
Replaces pipeline.bat with a pure-Python, testable simulation.

Each stage returns a structured dict so Flask can surface results via JSON.
"""

import time
import random
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Individual pipeline stages
# ---------------------------------------------------------------------------

def stage_checkout(repo: str = "unknown", branch: str = "main") -> dict:
    """Simulate git checkout / source pull."""
    return {
        "stage": "checkout",
        "status": "success",
        "detail": f"Checked out branch '{branch}' from repo '{repo}'",
    }


def stage_lint(files_changed: int = 0) -> dict:
    """Simulate a lint / static-analysis pass."""
    # Introduce a small realistic failure chance on large diffs
    failed = files_changed > 50 and random.random() < 0.15
    return {
        "stage": "lint",
        "status": "failed" if failed else "success",
        "detail": (
            f"Lint failed: {files_changed} files exceed complexity budget"
            if failed
            else f"Lint passed on {files_changed} changed file(s)"
        ),
    }


def stage_unit_tests() -> dict:
    """Simulate unit-test execution."""
    passed = random.randint(80, 120)
    failed = random.randint(0, 2)
    return {
        "stage": "unit_tests",
        "status": "failed" if failed > 0 else "success",
        "detail": f"{passed} passed, {failed} failed",
        "passed": passed,
        "failed": failed,
    }


def stage_build(service: str = "app") -> dict:
    """Simulate Docker image build / artifact creation."""
    tag = f"{service}:{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    return {
        "stage": "build",
        "status": "success",
        "detail": f"Image built: {tag}",
        "artifact": tag,
    }


def stage_security_scan(risk_score: float = 0.0) -> dict:
    """Simulate a basic security / SAST scan."""
    # High-risk deployments are more likely to surface issues
    vuln_count = max(0, int(risk_score / 10))
    status = "warning" if vuln_count > 0 else "success"
    return {
        "stage": "security_scan",
        "status": status,
        "detail": f"{vuln_count} potential vulnerabilities detected",
        "vulnerabilities": vuln_count,
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_pipeline(
    repo: str = "unknown",
    branch: str = "main",
    service: str = "app",
    files_changed: int = 0,
    risk_score: float = 0.0,
) -> dict:
    """
    Run all CI pipeline stages in order.

    Returns a summary dict with:
      - overall status  (success | failed | warning)
      - per-stage results
      - elapsed time
      - timestamp
    """
    start = time.monotonic()

    stages = [
        stage_checkout(repo, branch),
        stage_lint(files_changed),
        stage_unit_tests(),
        stage_build(service),
        stage_security_scan(risk_score),
    ]

    # Overall pipeline status: fail fast on any hard failure
    overall = "success"
    for s in stages:
        if s["status"] == "failed":
            overall = "failed"
            break
        if s["status"] == "warning" and overall == "success":
            overall = "warning"

    elapsed = round(time.monotonic() - start, 3)

    return {
        "pipeline": "ReleaseMind-CI",
        "repo": repo,
        "branch": branch,
        "service": service,
        "status": overall,
        "stages": stages,
        "elapsed_seconds": elapsed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
