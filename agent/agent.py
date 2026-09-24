import os
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from langsmith import traceable

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

SYSTEM_PROMPT = """You are a campaign planning assistant. Translate user requests into correct, safe tool calls.

Rules:
- Always search doctrine before validating actions.
- Always fetch the order of battle before referencing units.
- Validate constraints before building a draft — never skip.
- If an action violates constraints, explain why and stop.
- If the user requests access beyond their role ({user_role}), refuse and escalate.
- Always run the sanity check on a completed draft.

Current scenario: {scenario_id}
User role: {user_role}
Available doctrine sets: fm_3_0
"""


@traceable(name="campaign-planner-run")
def run_agent(question: str, scenario_id: str, user_role: str) -> dict:
    # Use ANTHROPIC_MODEL env var; default to haiku for fast/cheap local testing
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    llm = ChatAnthropic(model=model, temperature=0)

    system = SystemMessage(content=SYSTEM_PROMPT.format(
        scenario_id=scenario_id, user_role=user_role
    ))

    agent = create_react_agent(llm, TOOLS, prompt=system)
    result = agent.invoke({"messages": [("human", question)]})

    messages = result.get("messages", [])
    tool_calls = [
        {"tool": m.name, "args": m.content, "result": None}
        for m in messages
        if hasattr(m, "name") and m.name
    ]
    final_output = messages[-1].content if messages else ""

    return {
        "output": final_output,
        "steps": tool_calls,
    }
