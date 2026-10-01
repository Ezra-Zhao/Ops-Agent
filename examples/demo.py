"""Demo: run the agent against a simulated 'API latency spike' alert.

Prints the full thought -> action -> observation chain, then the ranked
hypotheses, remediation steps, and incident report.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent.llm import DeterministicDemoPolicy
from agent.orchestrator import IncidentAgent
from agent.schemas import Alert
from tools.report import render_console, render_json


def main() -> None:
    data_path = os.path.join(os.path.dirname(__file__), "..", "data",
                             "simulated_incident.json")
    with open(data_path) as f:
        alert_data = json.load(f)["alert"]

    alert = Alert(
        id=alert_data["id"],
        service=alert_data["service"],
        alert_type=alert_data["alert_type"],
        severity=alert_data["severity"],
        fired_at=alert_data["fired_at"],
        description=alert_data["description"],
    )

    print("=" * 64)
    print("ALERT RECEIVED")
    print("=" * 64)
    print(f"  [{alert.severity}] {alert.id}: {alert.description}")
    print(f"  Service: {alert.service} | Fired: {alert.fired_at}")

    agent = IncidentAgent(llm=DeterministicDemoPolicy())
    print("\nAGENT INVESTIGATION (thought -> action -> observation)")
    print("-" * 64)
    report = agent.run(alert, verbose=True)

    print(render_console(report))

    out = os.path.join(os.path.dirname(__file__), "incident_report.json")
    render_json(report, out)
    print(f"\nJSON report written to {out}")


if __name__ == "__main__":
    main()
