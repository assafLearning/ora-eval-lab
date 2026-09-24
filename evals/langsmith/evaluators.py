"""
LangSmith evaluators for running the agent against the ground truth dataset.
Usage: uv run python -m evals.langsmith.evaluators
"""
from langsmith import Client
from langsmith.evaluation import evaluate
from agent.agent import run_agent


def run_langsmith_eval(dataset_name: str = "ora-eval-ground-truth") -> None:
    client = Client()

    def agent_runner(inputs: dict) -> dict:
        return run_agent(
            question=inputs["question"],
            scenario_id=inputs["scenario_id"],
            user_role=inputs["user_role"],
        )

    def refused_correctly(run, example) -> dict:
        expected_refused = example.outputs.get("refused", False)
        output_text = run.outputs.get("output", "").lower()
        actually_refused = any(
            w in output_text for w in ["cannot", "refuse", "not authorized", "escalat"]
        )
        return {"key": "refused_correctly", "score": int(expected_refused == actually_refused)}

    def tool_count_reasonable(run, example) -> dict:
        steps = run.outputs.get("steps", [])
        expected_refused = example.outputs.get("refused", False)
        # Refused cases should have ≤1 tool call; normal cases should have ≥3
        if expected_refused:
            score = 1 if len(steps) <= 1 else 0
        else:
            score = 1 if len(steps) >= 3 else 0
        return {"key": "tool_count_reasonable", "score": score}

    results = evaluate(
        agent_runner,
        data=dataset_name,
        evaluators=[refused_correctly, tool_count_reasonable],
        experiment_prefix="ora-eval",
        client=client,
    )

    print(f"LangSmith eval complete. Results: {results.experiment_name}")


if __name__ == "__main__":
    run_langsmith_eval()
