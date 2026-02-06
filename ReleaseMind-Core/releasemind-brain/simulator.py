def simulate_release(services, dependencies):
    impact = set()

    for service in services:
        impact.add(service)

        if service in dependencies:
            for dependent in dependencies[service]:
                impact.add(dependent)

    return {
        "impacted_services": list(impact),
        "impact_level": "HIGH" if len(impact) >= 3 else "MEDIUM"
    }
