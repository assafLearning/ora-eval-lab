"""
Run all Inspect eval tasks and print a summary report.
Usage: uv run python -m evals.inspect.runner
"""
from inspect_ai import eval as inspect_eval
from evals.inspect.tasks.tool_use import tool_use_eval
from evals.inspect.tasks.adversarial import adversarial_eval


def run_all():
    results = inspect_eval(
        [tool_use_eval(), adversarial_eval()],
        model="anthropic/claude-sonnet-4-5",
        log_dir="logs/inspect",
    )

    print("\n=== Eval Results ===")
    for result in results:
        task_name = result.eval.task
        scores = result.results.scores if result.results else []
        for s in scores:
            for metric_name, metric in s.metrics.items():
                print(f"{task_name} | {s.name} | {metric_name}: {metric.value:.2f}")


if __name__ == "__main__":
    run_all()
