"""log_search tool: search recent logs for patterns.

SIMULATED backend: reads data/simulated_incident.json. A production
implementation would query Loki / Elasticsearch / CloudWatch Logs.

TODO(ezra): replace _load_logs() with a real log backend client.
"""
import json
import os
from typing import Any, Dict, List

from agent.schemas import ToolResult

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data",
                          "simulated_incident.json")


def _load_logs() -> List[Dict[str, Any]]:
    with open(_DATA_PATH) as f:
        return json.load(f)["logs"]


def log_search(service: str, window_minutes: int,
               patterns: List[str]) -> ToolResult:
    """Search logs for the service, returning entries matching any pattern.

    Args:
        service: service name to filter on.
        window_minutes: lookback window (demo data is fixed; kept for API shape).
        patterns: case-insensitive substrings to match in log messages.
    """
    hits = []
    for entry in _load_logs():
        if entry["service"] != service:
            continue
        msg = entry["message"].lower()
        if any(p.lower() in msg for p in patterns):
            hits.append(entry)

    deploy_events = [h for h in hits if "deploy" in h["message"].lower()]
    error_events = [h for h in hits
                    if h["level"] in ("ERROR", "CRITICAL", "WARN")]

    summary_lines = [
        f"Found {len(hits)} matching log lines for {service} "
        f"(window: {window_minutes}m).",
    ]
    if deploy_events:
        latest = deploy_events[-1]
        summary_lines.append(
            f"DEPLOY EVENT: '{latest['message']}' at {latest['ts']}.")
    if error_events:
        summary_lines.append(
            f"{len(error_events)} error/warn lines after the deploy window, "
            f"first at {error_events[0]['ts']}: "
            f"'{error_events[0]['message'][:80]}'.")

    return ToolResult(
        tool="log_search",
        summary=" ".join(summary_lines),
        data={"hits": hits, "deploy_events": deploy_events,
              "error_events": error_events},
        simulated=True,
    )
