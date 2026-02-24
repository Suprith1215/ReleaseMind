"""
ReleaseMind — Main Flask API (Full Production Release)
AI-Assisted DevOps Governance Engine
All 11 Phases integrated.
"""

import os
import sys
import json
from datetime import datetime, timezone

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# ── path setup so all sibling modules resolve ──────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from config_loader  import load_config, reload_config
from risk_engine    import calculate_risk, decide_strategy
from dependency_parser import analyze_dependencies
from metrics_collector import get_system_metrics, compute_metric_risk
from github_analyzer   import analyze_repo
import db

# ── new service imports ────────────────────────────────────────────────────
_SERVICES_DIR = os.path.join(os.path.dirname(__file__), "services")
sys.path.insert(0, _SERVICES_DIR)

from learning_engine    import get_similar_failure_rate, get_service_trend
from remediation_engine import generate_recommendations

# ── Flask app ───────────────────────────────────────────────────────────────
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "..", "frontend", "templates"),
    static_folder=os.path.join(os.path.dirname(__file__),   "..", "frontend", "static")
)
CORS(app, resources={r"/*": {"origins": "*"}})

cfg = load_config()


# ===========================================================================
#  HOME
# ===========================================================================
@app.route("/")
def home():
    return render_template("index.html")


# ===========================================================================
#  /analyze-repo  — Full GitHub → Risk → Strategy → DB → Remediation
# ===========================================================================
@app.route("/analyze-repo", methods=["POST"])
def analyze_repo_endpoint():
    """
    Full pipeline:
    1. Fetch GitHub data
    2. Compute dynamic risk
    3. Dependency blast radius
    4. Live metrics
    5. Historical learning
    6. Remediation recommendations
    7. Store in DB
    8. Return structured decision
    """
    payload = request.json or {}
    owner  = payload.get("repo_owner", "")
    repo   = payload.get("repo_name",  "")
    branch = payload.get("branch",     "main")
    token  = payload.get("github_token") or os.environ.get("GITHUB_TOKEN", "")

    config_drift   = payload.get("config_drift",   False)
    resource_drift = payload.get("resource_drift", False)
    peak_hours     = payload.get("peak_hours",     False)
    weekend        = payload.get("weekend",        False)
    owns_service   = payload.get("owns_service",   True)

    if not owner or not repo:
        return jsonify({"error": "repo_owner and repo_name are required"}), 400

    # ── Step 1: GitHub Analysis ────────────────────────────────────────────
    github_data = analyze_repo(owner, repo, branch, github_token=token)

    affected_services = github_data.get("affected_services") or ["unknown"]
    primary_service   = affected_services[0]

    # ── Step 2: Dependency blast radius ───────────────────────────────────
    dep_analysis = analyze_dependencies(affected_services)

    # ── Step 3: Live metrics ───────────────────────────────────────────────
    metrics     = get_system_metrics()
    metric_cfg  = cfg.get("weights", {})
    metric_risk = compute_metric_risk(
        metrics["cpu_percent"],
        metrics["memory_percent"],
        cpu_threshold            = metric_cfg.get("cpu_threshold", 75),
        memory_threshold         = metric_cfg.get("memory_threshold", 80),
        cpu_risk_per_percent     = metric_cfg.get("cpu_risk_per_percent_above", 0.10),
        memory_risk_per_percent  = metric_cfg.get("memory_risk_per_percent_above", 0.08),
    )

    # ── Step 4: Historical failure rate ───────────────────────────────────
    failure_rate = db.get_failure_rate(primary_service)

    # ── Step 5: Dynamic risk calculation ──────────────────────────────────
    risk_breakdown = calculate_risk(
        files_changed              = github_data.get("files_changed", 0),
        lines_added                = github_data.get("lines_added",   0),
        lines_deleted              = github_data.get("lines_deleted", 0),
        commit_type                = github_data.get("commit_type_detected", "unknown"),
        developer_experience_score = github_data.get("developer_experience_score", 0.5),
        owns_service               = owns_service,
        dependency_depth           = dep_analysis["dependency_depth"],
        blast_radius               = len(dep_analysis["impacted_services"]),
        failure_rate               = failure_rate,
        config_drift               = config_drift,
        resource_drift             = resource_drift,
        cpu_percent                = metrics["cpu_percent"],
        memory_percent             = metrics["memory_percent"],
        peak_hours                 = peak_hours,
        weekend                    = weekend,
    )

    risk_score = risk_breakdown["total"]
    strategy   = decide_strategy(risk_score)

    # ── Step 6: Historical learning insight ───────────────────────────────
    learning_insight = get_similar_failure_rate(risk_score, primary_service)
    service_trend    = get_service_trend(primary_service)

    # Apply additional learning risk
    if learning_insight["additional_risk"] > 0:
        risk_breakdown["history"] = round(
            risk_breakdown.get("history", 0) + learning_insight["additional_risk"], 2
        )
        risk_breakdown["total"] = round(sum(
            v for k, v in risk_breakdown.items() if k != "total"
        ), 2)
        risk_score = risk_breakdown["total"]
        strategy   = decide_strategy(risk_score)

    # ── Step 7: Remediation recommendations ───────────────────────────────
    remediation = generate_recommendations(risk_breakdown)

    # ── Step 8: Store in DB ───────────────────────────────────────────────
    dep_id = db.record_deployment({
        "timestamp":     datetime.now(timezone.utc).isoformat(),
        "risk_score":    risk_score,
        "strategy":      strategy,
        "outcome":       "pending",
        "service":       primary_service,
        "developer":     github_data.get("author", "unknown"),
        "repo_owner":    owner,
        "repo_name":     repo,
        "branch":        branch,
        "commit_sha":    github_data.get("commit_sha",  ""),
        "files_changed": github_data.get("files_changed", 0),
        "lines_added":   github_data.get("lines_added",   0),
        "lines_deleted": github_data.get("lines_deleted", 0),
        "commit_type":   github_data.get("commit_type_detected", "unknown"),
        "blast_radius":  len(dep_analysis["impacted_services"]),
        "dep_depth":     dep_analysis["dependency_depth"],
        "cpu_at_deploy": metrics["cpu_percent"],
        "mem_at_deploy": metrics["memory_percent"],
    })

    return jsonify({
        "deployment_id":        dep_id,
        "risk_score":           risk_score,
        "risk_breakdown":       risk_breakdown,
        "deployment_strategy":  strategy,
        "github":               github_data,
        "dependency":           dep_analysis,
        "metrics":              {**metrics, **metric_risk},
        "failure_rate":         failure_rate,
        "learning":             learning_insight,
        "service_trend":        service_trend,
        "remediation":          remediation,
        "explanation": {
            "config_drift":   config_drift,
            "resource_drift": resource_drift,
            "peak_hours":     peak_hours,
            "weekend":        weekend,
        },
        "github_error": github_data.get("error"),
    })


# ===========================================================================
#  /decide  — Legacy manual input (backwards compatible)
# ===========================================================================
@app.route("/decide", methods=["POST"])
def decide():
    """Legacy manual-input endpoint — kept for backward compatibility."""
    data        = request.json or {}
    change      = data.get("change",      {})
    human       = data.get("human",       {})
    environment = data.get("environment", {})
    timing      = data.get("timing",      {})

    affected_services = change.get("services", ["unknown"])
    primary_service   = affected_services[0]

    dep_analysis = analyze_dependencies(affected_services)
    metrics      = get_system_metrics()
    failure_rate = db.get_failure_rate(primary_service)

    exp = human.get("experience", "senior")
    exp_score = 0.3 if exp == "new" else 0.85

    risk_breakdown = calculate_risk(
        commit_type                = change.get("intent", "unknown"),
        developer_experience_score = exp_score,
        owns_service               = human.get("owns_service", True),
        dependency_depth           = dep_analysis["dependency_depth"],
        blast_radius               = len(dep_analysis["impacted_services"]),
        failure_rate               = failure_rate,
        config_drift               = environment.get("config_drift", False),
        resource_drift             = environment.get("resource_drift", False),
        cpu_percent                = metrics["cpu_percent"],
        memory_percent             = metrics["memory_percent"],
        peak_hours                 = timing.get("peak_hours", False),
        weekend                    = timing.get("weekend",    False),
    )

    risk_score = risk_breakdown["total"]
    strategy   = decide_strategy(risk_score)
    remediation = generate_recommendations(risk_breakdown)

    dep_id = db.record_deployment({
        "timestamp":    datetime.now(timezone.utc).isoformat(),
        "risk_score":   risk_score,
        "strategy":     strategy,
        "outcome":      "pending",
        "service":      primary_service,
        "developer":    human.get("name", "unknown"),
        "blast_radius": len(dep_analysis["impacted_services"]),
        "dep_depth":    dep_analysis["dependency_depth"],
        "cpu_at_deploy": metrics["cpu_percent"],
        "mem_at_deploy": metrics["memory_percent"],
    })

    return jsonify({
        "deployment_id":       dep_id,
        "risk_score":          risk_score,
        "risk_breakdown":      risk_breakdown,
        "deployment_strategy": strategy,
        "dry_run":             dep_analysis,
        "metrics":             metrics,
        "remediation":         remediation,
        "explanation": {
            "change":       change,
            "human":        human,
            "environment":  environment,
            "timing":       timing,
        },
    })


# ===========================================================================
#  /deployment-outcome  — Outcome Feedback Loop (Phase 6 / Phase 11)
# ===========================================================================
@app.route("/deployment-outcome", methods=["POST"])
@app.route("/deployment-result",  methods=["POST"])   # legacy alias
def deployment_outcome():
    data    = request.json or {}
    dep_id  = data.get("deployment_id")
    outcome = data.get("outcome")

    if dep_id is None or outcome not in ("success", "failure"):
        return jsonify({"error": "deployment_id and outcome (success|failure) are required"}), 400

    try:
        db.update_outcome(int(dep_id), outcome)
        deployment = db.get_deployment_by_id(int(dep_id))
        new_rate   = db.get_failure_rate(deployment["service"])
        return jsonify({
            "status":           "updated",
            "deployment_id":    dep_id,
            "outcome":          outcome,
            "service":          deployment["service"],
            "new_failure_rate": round(new_rate, 3),
            "message":          (
                f"Service '{deployment['service']}' failure rate updated to {new_rate:.1%}"
            ),
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ===========================================================================
#  /history  — Recent deployment history (Phase 11)
# ===========================================================================
@app.route("/history", methods=["GET"])
@app.route("/decisions", methods=["GET"])   # legacy alias
def get_history():
    limit = int(request.args.get("limit", 50))
    return jsonify(db.get_recent_deployments(limit))


# ===========================================================================
#  /service-stats  — Failure rates per service
# ===========================================================================
@app.route("/service-stats", methods=["GET"])
def service_stats():
    return jsonify(db.get_all_service_stats())


# ===========================================================================
#  /system-metrics  — Live system metrics (Phase 11)
# ===========================================================================
@app.route("/system-metrics", methods=["GET"])
@app.route("/metrics",        methods=["GET"])   # legacy alias
def live_metrics():
    m = get_system_metrics()
    k8s = None
    try:
        from metrics_collector import get_k8s_pod_metrics
        k8s = get_k8s_pod_metrics()
    except Exception:
        pass
    return jsonify({"system": m, "kubernetes": k8s})


# ===========================================================================
#  /config/reload  — Hot reload risk_config.yaml
# ===========================================================================
@app.route("/config/reload", methods=["POST"])
def config_reload():
    new_cfg = reload_config()
    return jsonify({"status": "reloaded", "keys": list(new_cfg.keys())})


# ===========================================================================
#  APP START
# ===========================================================================
if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 7000))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    print(f"\n🧠 ReleaseMind AI Governance Engine starting on http://0.0.0.0:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
