def decide_strategy(risk_score):
    if risk_score >= 15:
        return "BLOCK"
    elif risk_score >= 10:
        return "CANARY"
    elif risk_score >= 6:
        return "BLUE_GREEN"
    else:
        return "ROLLING"
