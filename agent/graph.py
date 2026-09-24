"""
Exposes the campaign planner as a compiled LangGraph graph.
LangGraph Studio reads this file via langgraph.json.
"""
import os
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

from agent.tools.search_doctrine import search_doctrine
from agent.tools.fetch_order_of_battle import fetch_order_of_battle
from agent.tools.validate_constraints import validate_constraints
from agent.tools.build_campaign_draft import build_campaign_draft
from agent.tools.run_sanity_check import run_sanity_check

TOOLS = [
    search_doctrine,
    fetch_order_of_battle,
    validate_constraints,
    build_campaign_draft,
    run_sanity_check,
]

# Studio passes state via messages — scenario/role come from the system prompt.
# Change these to explore different scenarios interactively.
SCENARIO_ID = os.getenv("SCENARIO_ID", "river_crossing_v1")
USER_ROLE = os.getenv("USER_ROLE", "planner")

_system = SystemMessage(content=f"""You are a campaign planning assistant.

Rules:
- Always search doctrine before validating actions.
- Always fetch the order of battle before referencing units.
- Validate constraints before building a draft — never skip.
- If an action violates constraints, explain why and stop.
- If the user requests access beyond their role ({USER_ROLE}), refuse and escalate.
- Always run the sanity check on a completed draft.

Current scenario: {SCENARIO_ID}
User role: {USER_ROLE}
Available doctrine sets: fm_3_0
""")

model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
_llm = ChatAnthropic(model=model, temperature=0)

graph = create_react_agent(_llm, TOOLS, prompt=_system)
