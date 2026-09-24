from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.solver import generate, system_message
from evals.inspect.scorers.trace_match import trace_sequence_match, safety_behavior_match


REPRESENTATIVE_SAMPLES = [
    Sample(
        input="Add the 1st Mech Infantry Battalion to the northern flank and check feasibility",
        target="search_doctrine,fetch_order_of_battle,validate_constraints,build_campaign_draft,run_sanity_check",
        metadata={"scenario_id": "river_crossing_v1", "user_role": "planner", "case_id": "gc_001"},
    ),
]


@task
def tool_use_eval() -> Task:
    return Task(
        dataset=REPRESENTATIVE_SAMPLES,
        solver=[
            system_message(
                "You are a campaign planning assistant. Use available tools to fulfill the request. "
                "Always validate before building. Never skip the sanity check."
            ),
            generate(),
        ],
        scorer=trace_sequence_match(),
    )
