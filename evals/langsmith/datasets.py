"""
Push ground truth cases from data/ground_truth/cases/ into a LangSmith dataset.
Usage: uv run python -m evals.langsmith.datasets
"""
from pathlib import Path
import yaml
from langsmith import Client


def push_ground_truth_dataset(dataset_name: str = "ora-eval-ground-truth") -> None:
    client = Client()
    cases_dir = Path(__file__).parent.parent.parent / "data" / "ground_truth" / "cases"

    cases = [yaml.safe_load(f.read_text()) for f in sorted(cases_dir.glob("*.yaml"))]

    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description="ORA campaign planner ground truth eval cases",
    )

    examples = [
        {
            "inputs": {
                "question": c["question"],
                "scenario_id": c["scenario_id"],
                "user_role": c["user_role"],
            },
            "outputs": c["expected_output"],
        }
        for c in cases
    ]

    client.create_examples(
        inputs=[e["inputs"] for e in examples],
        outputs=[e["outputs"] for e in examples],
        dataset_id=dataset.id,
    )

    print(f"Pushed {len(examples)} cases to dataset '{dataset_name}'")


if __name__ == "__main__":
    push_ground_truth_dataset()
