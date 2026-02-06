def calculate_risk(change, human, environment, timing):
    risk = 0

    # ---------------- Change Intent ----------------
    intent_weights = {
        "hotfix": 2,
        "feature": 4,
        "refactor": 6
    }
    risk += intent_weights.get(change["intent"], 3)

    # ---------------- Human Risk ----------------
    if human["experience"] == "new":
        risk += 3

    if not human.get("owns_service", False):
        risk += 2

    # ---------------- Environment Drift ----------------
    if environment.get("config_drift"):
        risk += 4

    if environment.get("resource_drift"):
        risk += 3

    # ---------------- Timing Risk ----------------
    if timing.get("peak_hours"):
        risk += 2

    if timing.get("weekend"):
        risk += 1

    # ---------------- Dependency Impact ----------------
    risk += len(change.get("services", [])) * 2

    return risk
