import os
from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
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

SYSTEM_PROMPT = """You are a campaign planning assistant. Your job is to translate
user requests into correct, safe tool calls against a defined scenario.

Rules:
- Always validate constraints before building a draft.
- Never skip fetch_order_of_battle when units are involved.
- If an action violates constraints, explain why and stop — do not proceed.
- If the user requests access beyond their role ({user_role}), refuse and escalate.
- Never bypass the sanity check on a completed draft.

Current scenario: {scenario_id}
User role: {user_role}
"""


def build_agent(scenario_id: str, user_role: str) -> AgentExecutor:
    llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=SYSTEM_PROMPT.format(scenario_id=scenario_id, user_role=user_role)),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, TOOLS, prompt)
    return AgentExecutor(agent=agent, tools=TOOLS, verbose=True, return_intermediate_steps=True)


@traceable(name="campaign-planner-run")
def run_agent(question: str, scenario_id: str, user_role: str) -> dict:
    executor = build_agent(scenario_id, user_role)
    result = executor.invoke({"input": question})
    return {
        "output": result["output"],
        "steps": [
            {"tool": s[0].tool, "args": s[0].tool_input, "result": str(s[1])}
            for s in result.get("intermediate_steps", [])
        ],
    }
