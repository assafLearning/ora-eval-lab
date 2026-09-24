from langchain_core.tools import tool


@tool
def validate_constraints(proposed_action: dict, constraints: list[dict]) -> dict:
    """Check a proposed action against doctrine rules. Does not modify state."""
    violations = []

    action_type = proposed_action.get("action_type", "")
    params = proposed_action.get("parameters", {})

    for rule in constraints:
        constraint_type = rule.get("constraint_type", "")

        if constraint_type == "force_limit":
            limit = rule.get("limit", 0)
            if params.get("unit_count", 0) > limit:
                violations.append(f"Exceeds force limit of {limit}: {rule['id']}")

        elif constraint_type == "restricted_zone":
            if proposed_action.get("location") in rule.get("zones", []):
                violations.append(f"Location in restricted zone: {rule['id']}")

        elif constraint_type == "requires_confirmation" and action_type in rule.get("actions", []):
            violations.append(f"Action '{action_type}' requires commander confirmation: {rule['id']}")

    return {
        "valid": len(violations) == 0,
        "violations": violations,
        "action": proposed_action,
    }
