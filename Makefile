.PHONY: install run ui eval langsmith-push langsmith-eval lint

install:
	uv sync

run:
	PYTHONPATH=. uv run python scripts/run_agent.py

ui:
	uv run langgraph dev --port 8123

eval:
	PYTHONPATH=. uv run python -m evals.inspect.runner

langsmith-push:
	PYTHONPATH=. uv run python -m evals.langsmith.datasets

langsmith-eval:
	PYTHONPATH=. uv run python -m evals.langsmith.evaluators

lint:
	uv run ruff check .
	uv run mypy . --ignore-missing-imports
