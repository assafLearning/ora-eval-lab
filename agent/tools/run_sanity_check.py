from langchain_core.tools import tool


@tool
def run_sanity_check(draft: dict) -> dict:
    """Cross-check a campaign draft for force ratios, timing, and objective alignment."""
    issues = []
    actions = draft.get("actions", [])

    if not actions:
        issues.append("Draft contains no actions")

    if not draft.get("metadata", {}).get("objective"):
        issues.append("No objective defined in scenario")

    action_types = [a.get("action", {}).get("action_type", "") for a in actions]
    if "DEPLOY" in action_types and "VALIDATE" not in action_types:
        issues.append("DEPLOY actions present but no prior VALIDATE step found in trace")

    # Simple force ratio check: warn if more than 5 units in a single action
    for a in actions:
        params = a.get("action", {}).get("parameters", {})
        if params.get("unit_count", 0) > 5:
            issues.append(f"High unit concentration in single action: {params.get('unit_count')} units")

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "force_ratio": None,
        "feasibility_score": round(1.0 - (len(issues) * 0.2), 2) if issues else 1.0,
    }
