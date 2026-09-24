import json
from pathlib import Path
from langchain_core.tools import tool
from contracts.models import UserRole

_SCENARIOS_PATH = Path(__file__).parent.parent.parent / "data" / "scenarios"

_ROLE_CLEARANCE = {
    UserRole.analyst: 1,
    UserRole.planner: 2,
    UserRole.commander: 3,
}


@tool
def fetch_order_of_battle(scenario_id: str, role: str) -> dict:
    """Return available forces for a scenario. Some units require elevated role."""
    path = _SCENARIOS_PATH / f"{scenario_id}.json"
    if not path.exists():
        raise ValueError(f"UnknownScenario: {scenario_id}")

    scenario = json.loads(path.read_text())
    user_clearance = _ROLE_CLEARANCE.get(UserRole(role), 0)

    visible_units = [
        u for u in scenario["units"]
        if _ROLE_CLEARANCE.get(UserRole(u.get("min_role", "analyst")), 1) <= user_clearance
    ]

    return {"scenario_id": scenario_id, "role_used": role, "units": visible_units}
