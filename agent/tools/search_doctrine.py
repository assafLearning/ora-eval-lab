import json
from pathlib import Path
from langchain_core.tools import tool
from contracts.models import DoctrineRule

_DOCTRINE_PATH = Path(__file__).parent.parent.parent / "data" / "doctrine"


@tool
def search_doctrine(query: str, doctrine_set: str) -> list[dict]:
    """Search public doctrine for rules relevant to a proposed action."""
    path = _DOCTRINE_PATH / f"{doctrine_set}.json"
    if not path.exists():
        available = [p.stem for p in _DOCTRINE_PATH.glob("*.json")]
        return [{"warning": f"Unknown doctrine set '{doctrine_set}'. Available: {available}"}]

    rules: list[dict] = json.loads(path.read_text())
    query_lower = query.lower()
    matches = [r for r in rules if any(w in r["text"].lower() for w in query_lower.split())]
    return matches[:5]
