from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from risk_engine import calculate_risk
from decision_engine import decide_strategy
from simulator import simulate_release
from datetime import datetime
import json
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ---------------- HOME / UI ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- DECIDE API ----------------
@app.route("/decide", methods=["POST"])
def decide():
    data = request.json

    change = data["change"]
    human = data["human"]
    environment = data["environment"]
    timing = data["timing"]

    # Risk calculation
    risk = calculate_risk(change, human, environment, timing)
    strategy = decide_strategy(risk)

    # Dependency graph (dry-run simulator)
    dependencies = {
        "auth": ["order", "payment"],
        "order": ["payment"]
    }

    simulation = simulate_release(change["services"], dependencies)

    # Audit log entry
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "risk_score": risk,
        "deployment_strategy": strategy,
        "change": change,
        "human": human,
        "environment": environment,
        "timing": timing,
        "dry_run": simulation
    }

    os.makedirs("logs", exist_ok=True)
    with open("logs/decisions.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return jsonify({
        "risk_score": risk,
        "deployment_strategy": strategy,
        "dry_run": simulation,
        "explanation": {
            "change": change,
            "human": human,
            "environment": environment,
            "timing": timing
        }
    })

# ---------------- DECISION HISTORY ----------------
@app.route("/decisions", methods=["GET"])
def get_decisions():
    logs = []

    if os.path.exists("logs/decisions.log"):
        with open("logs/decisions.log", "r") as f:
            for line in f:
                logs.append(json.loads(line))

    return jsonify(logs[::-1])  # newest first

# ---------------- APP START ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7000)
