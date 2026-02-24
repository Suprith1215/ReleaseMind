"""
ReleaseMind — Dynamic Risk Engine (Phase 2)
All weights are read from risk_config.yaml — no hardcoded values.
"""

from config_loader import load_config

_cfg = load_config()
_w = _cfg.get("weights", {})
_intent_risk = _cfg.get("intent_base_risk", {})
_thresholds = _cfg.get("strategy_thresholds", {})


def calculate_risk(
    *,
    # Code size factors (from GitHub Analyzer)
    files_changed: int = 0,
    lines_added: int = 0,
    lines_deleted: int = 0,
    # Commit intent (detected or manual)
    commit_type: str = "unknown",
    # Developer factors
    developer_experience_score: float = 0.5,   # 0.0 = new, 1.0 = senior
    owns_service: bool = True,
    # Dependency factors (from Dependency Parser)
    dependency_depth: int = 0,
    blast_radius: int = 0,
    # Historical factors (from DB)
    failure_rate: float = 0.0,
    # Environment factors
    config_drift: bool = False,
    resource_drift: bool = False,
    # Infrastructure metrics (from Metrics Collector)
    cpu_percent: float = 0.0,
    memory_percent: float = 0.0,
    # Timing factors
    peak_hours: bool = False,
    weekend: bool = False,
) -> dict:
    """
    Calculate a weighted, dynamic risk score.

    Returns a dict with total score AND per-factor breakdown.
    """

    breakdown = {}

    # ---- Code size ----
    file_risk = files_changed * _w.get("files_changed_per_file", 0.20)
    add_risk  = (lines_added  / 100) * _w.get("lines_added_per_100", 0.50)
    del_risk  = (lines_deleted / 100) * _w.get("lines_deleted_per_100", 0.10)
    breakdown["code_size"] = round(file_risk + add_risk + del_risk, 2)

    # ---- Commit intent ----
    intent_score = _intent_risk.get(commit_type, _intent_risk.get("unknown", 3))
    breakdown["commit_intent"] = intent_score

    # ---- Developer risk ----
    # experience_score 1.0 = senior → low risk, 0.0 = new → high risk
    dev_risk = (1.0 - developer_experience_score) * _w.get("new_developer_penalty", 3.0)
    if not owns_service:
        dev_risk += _w.get("not_service_owner_penalty", 2.0)
    breakdown["developer"] = round(dev_risk, 2)

    # ---- Dependency impact ----
    dep_risk = (
        dependency_depth * _w.get("dependency_depth_weight", 1.50)
        + blast_radius   * _w.get("blast_radius_weight", 0.30)
    )
    breakdown["dependency"] = round(dep_risk, 2)

    # ---- Historical failure ----
    hist_risk = failure_rate * _w.get("failure_rate_multiplier", 3.0) * 10
    breakdown["history"] = round(hist_risk, 2)

    # ---- Environment drift ----
    env_risk = 0.0
    if config_drift:
        env_risk += _w.get("config_drift_penalty", 4.0)
    if resource_drift:
        env_risk += _w.get("resource_drift_penalty", 3.0)
    breakdown["environment"] = env_risk

    # ---- Infrastructure metrics ----
    cpu_threshold = _w.get("cpu_threshold", 75.0)
    mem_threshold = _w.get("memory_threshold", 80.0)
    cpu_risk = 0.0
    mem_risk = 0.0
    if cpu_percent > cpu_threshold:
        cpu_risk = (cpu_percent - cpu_threshold) * _w.get("cpu_risk_per_percent_above", 0.10)
    if memory_percent > mem_threshold:
        mem_risk = (memory_percent - mem_threshold) * _w.get("memory_risk_per_percent_above", 0.08)
    breakdown["infrastructure"] = round(cpu_risk + mem_risk, 2)

    # ---- Timing ----
    timing_risk = 0.0
    if peak_hours:
        timing_risk += _w.get("peak_hours_penalty", 2.0)
    if weekend:
        timing_risk += _w.get("weekend_penalty", 1.0)
    breakdown["timing"] = timing_risk

    total = round(sum(breakdown.values()), 2)
    breakdown["total"] = total

    return breakdown


def decide_strategy(risk_score: float) -> str:
    """Choose deployment strategy based on configurable thresholds."""
    block_above     = _thresholds.get("block_above",      20)
    canary_above    = _thresholds.get("canary_above",     14)
    blue_green_above = _thresholds.get("blue_green_above", 8)

    if risk_score >= block_above:
        return "BLOCK"
    elif risk_score >= canary_above:
        return "CANARY"
    elif risk_score >= blue_green_above:
        return "BLUE_GREEN"
    else:
        return "ROLLING"
