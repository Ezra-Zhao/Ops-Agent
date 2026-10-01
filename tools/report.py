"""report: render the incident report to console and JSON."""
import json
import os
from typing import Any, Dict

from agent.schemas import IncidentReport


def render_console(report: IncidentReport) -> str:
    a = report.alert
    lines = [
        "",
        "=" * 64,
        "INCIDENT REPORT",
        "=" * 64,
        f"Alert:      {a.id} [{a.severity}]",
        f"Service:    {a.service}",
        f"Type:       {a.alert_type}",
        f"Fired:      {a.fired_at}",
        f"Steps:      {len(report.steps)} tool calls",
        "",
        "RANKED HYPOTHESES",
        "-" * 64,
    ]
    for i, h in enumerate(report.hypotheses, 1):
        lines.append(f"  {i}. {h.title}  (confidence {h.confidence:.2f})")
        for e in h.evidence:
            lines.append(f"     - {e}")
    lines += [
        "",
        "RECOMMENDED REMEDIATION",
        "-" * 64,
    ]
    for r in report.hypotheses[0].remediation:
        lines.append(f"  * {r}")
    lines += [
        "",
        f"TOP RECOMMENDATION: {report.top_recommendation}",
        "",
        "Data provenance: SIMULATED - demo data, not production telemetry.",
        "=" * 64,
    ]
    return "\n".join(lines)


def render_json(report: IncidentReport, path: str) -> Dict[str, Any]:
    payload = report.to_dict()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return payload
