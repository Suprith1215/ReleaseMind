from risk_engine import calculate_risk
from decision_engine import decide_strategy
import json

# Simulated inputs (later CI/CD sends this)
change = {
    "intent": "refactor",
    "services": ["auth", "order"]
}

human = {
    "experience": "new",
    "owns_service": False
}

environment = {
    "config_drift": True,
    "resource_drift": False
}

timing = {
    "peak_hours": True,
    "weekend": False
}

risk = calculate_risk(change, human, environment, timing)
strategy = decide_strategy(risk)

output = {
    "risk_score": risk,
    "deployment_strategy": strategy,
    "explanation": {
        "intent": change["intent"],
        "services": change["services"],
        "human": human,
        "environment": environment,
        "timing": timing
    }
}

print(json.dumps(output, indent=2))
