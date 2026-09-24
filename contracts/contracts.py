"""
Tool contracts: what each tool accepts, returns, and guarantees.
This is the source of truth — implementations must satisfy these contracts.
"""

from contracts.models import (
    Action,
    CampaignDraft,
    DoctrineRule,
    ForceList,
    SanityReport,
    UserRole,
    ValidationResult,
)

TOOL_CONTRACTS: dict[str, dict] = {
    "search_doctrine": {
        "description": "Search public doctrine for rules relevant to a proposed action.",
        "inputs": {"query": str, "doctrine_set": str},
        "output": list[DoctrineRule],
        "errors": ["UnknownDoctrineSet"],
        "state_changes": [],
        "safe_fallback": "return empty list with a warning — never hallucinate rules",
        "restricted": False,
    },
    "fetch_order_of_battle": {
        "description": "Return available forces for a scenario, filtered by user role.",
        "inputs": {"scenario_id": str, "role": UserRole},
        "output": ForceList,
        "errors": ["UnknownScenario", "InsufficientRole"],
        "state_changes": [],
        "safe_fallback": "raise InsufficientRole — do not return partial data",
        "restricted": True,  # commander role required for full OOB
    },
    "validate_constraints": {
        "description": "Check a proposed action against doctrine rules. Does not modify state.",
        "inputs": {"proposed_action": Action, "constraints": list[DoctrineRule]},
        "output": ValidationResult,
        "errors": [],
        "state_changes": [],
        "safe_fallback": "mark valid=False on any uncertainty",
        "restricted": False,
    },
    "build_campaign_draft": {
        "description": "Assemble validated actions into a campaign draft. Refuses unvalidated input.",
        "inputs": {"scenario_id": str, "actions": list[ValidationResult]},
        "output": CampaignDraft,
        "errors": ["UnvalidatedAction", "UnknownScenario"],
        "state_changes": ["creates draft in memory — does not persist"],
        "safe_fallback": "raise UnvalidatedAction — never skip validation",
        "restricted": False,
    },
    "run_sanity_check": {
        "description": "Cross-check a draft for force ratios, timing, and objective alignment.",
        "inputs": {"draft": CampaignDraft},
        "output": SanityReport,
        "errors": ["IncompleteDraft"],
        "state_changes": [],
        "safe_fallback": "return passed=False with issues listed",
        "restricted": False,
    },
}
