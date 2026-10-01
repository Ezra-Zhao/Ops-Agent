"""metrics_query tool: pull time-series metrics for a service.

SIMULATED backend: reads data/simulated_incident.json. A production
implementation would query Prometheus / Datadog / CloudWatch.

TODO(ezra): replace _load_metrics() with a real metrics backend client.
"""
import json
import os
from typing import Any, Dict, List

from agent.schemas import ToolResult

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data",
                          "simulated_incident.json")


def _load_metrics() -> Dict[str, List[List[Any]]]:
    with open(_DATA_PATH) as f:
        return json.load(f)["metrics"]


def _pct_change(series: List[List[Any]]) -> float:
    first, last = series[0][1], series[-1][1]
    if first == 0:
        return float("inf") if last > 0 else 0.0
    return (last - first) / first * 100.0


def metrics_query(service: str, window_minutes: int,
                  metrics: List[str]) -> ToolResult:
    """Query metric series and summarize baseline vs current values.

    Args:
        service: service name (kept for API shape; demo has one service).
        window_minutes: lookback window.
        metrics: metric names to pull.
    """
    store = _load_metrics()
    findings = []
    data: Dict[str, Any] = {}
    for name in metrics:
        series = store.get(name)
        if not series:
            findings.append(f"{name}: no data.")
            continue
        baseline, current = series[0][1], series[-1][1]
        change = _pct_change(series)
        data[name] = {"baseline": baseline, "current": current,
                      "pct_change": round(change, 1), "series": series}
        if abs(change) >= 50:
            direction = "rose" if change > 0 else "fell"
            findings.append(
                f"{name}: {baseline} -> {current} ({direction} "
                f"{abs(change):.0f}%) — SIGNIFICANT.")
        else:
            findings.append(
                f"{name}: {baseline} -> {current} "
                f"({change:+.0f}%) — roughly flat.")

    return ToolResult(
        tool="metrics_query",
        summary=f"Metrics for {service} (window: {window_minutes}m). "
                + " ".join(findings),
        data=data,
        simulated=True,
    )
