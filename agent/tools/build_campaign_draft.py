import json
from pathlib import Path
from langchain_core.tools import tool

_SCENARIOS_PATH = Path(__file__).parent.parent.parent / "data" / "scenarios"


@tool
def build_campaign_draft(scenario_id: str, actions: list[dict]) -> dict:
    """Assemble validated actions into a campaign draft. Refuses unvalidated input."""
    path = _SCENARIOS_PATH / f"{scenario_id}.json"
    if not path.exists():
        raise ValueError(f"UnknownScenario: {scenario_id}")

    for action in actions:
        if not action.get("valid", False):
            violations = action.get("violations", [])
            raise ValueError(f"UnvalidatedAction: cannot build draft with invalid action. Violations: {violations}")

    scenario = json.loads(path.read_text())

    return {
        "scenario_id": scenario_id,
        "version": scenario.get("version", "1.0"),
        "actions": actions,
        "metadata": {
            "objective": scenario.get("objective"),
            "action_count": len(actions),
        },
    }
