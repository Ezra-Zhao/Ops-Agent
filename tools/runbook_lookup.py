"""runbook_lookup tool: match a symptom query to known runbooks.

SIMULATED backend: reads data/simulated_incident.json. Production runbooks
should be contributed from Ezra's real on-call experience.

TODO(ezra): replace the bundled runbooks with the team's real ones
(e.g. from Confluence / Notion / an internal runbook repo).
"""
import json
import os
from typing import Any, Dict

from agent.schemas import ToolResult

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data",
                          "simulated_incident.json")


def _load_runbooks() -> Dict[str, Dict[str, Any]]:
    with open(_DATA_PATH) as f:
        return json.load(f)["runbooks"]


def _score(query: str, runbook: Dict[str, Any]) -> int:
    text = " ".join([runbook["title"]] + runbook["triggers"]).lower()
    return sum(1 for word in query.lower().split() if word in text)


def runbook_lookup(query: str) -> ToolResult:
    """Return the best-matching runbook for a symptom query."""
    runbooks = _load_runbooks()
    best_key = max(runbooks, key=lambda k: _score(query, runbooks[k]))
    best = runbooks[best_key]
    steps = "\n".join(best["steps"])
    return ToolResult(
        tool="runbook_lookup",
        summary=f"Matched runbook '{best['title']}' for query '{query}'. "
                f"Triggers: {'; '.join(best['triggers'])}.",
        data={"runbook_id": best_key, "title": best["title"],
              "triggers": best["triggers"], "steps": best["steps"],
              "steps_text": steps},
        simulated=True,
    )
