"""
Run the agent against a scenario and print the full trace.
Usage: uv run python scripts/run_agent.py
"""
import os
from dotenv import load_dotenv
from agent.agent import run_agent

load_dotenv()


def main():
    result = run_agent(
        question="Add the 1st Mech Infantry Battalion to the northern flank and check feasibility",
        scenario_id="river_crossing_v1",
        user_role="planner",
    )

    print("\n=== Agent Output ===")
    print(result["output"])
    print("\n=== Tool Trace ===")
    for i, step in enumerate(result["steps"], 1):
        print(f"  {i}. {step['tool']}({step['args']})")


if __name__ == "__main__":
    main()
