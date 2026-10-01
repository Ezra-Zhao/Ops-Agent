"""Unit tests for the Ops-Agent scaffold."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent.llm import DeterministicDemoPolicy
from agent.orchestrator import IncidentAgent
from agent.schemas import Alert
from agent.tool_registry import available_tools
from tools.log_search import log_search
from tools.metrics_query import metrics_query
from tools.report import render_json
from tools.runbook_lookup import runbook_lookup


def make_alert() -> Alert:
    return Alert(
        id="ALT-TEST-001",
        service="payments-api",
        alert_type="high_p99_latency",
        severity="critical",
        fired_at="2026-10-01T14:32:00Z",
        description="p99 latency above 2000ms",
    )


def test_registry_has_expected_tools():
    tools = available_tools()
    assert {"log_search", "metrics_query", "runbook_lookup"} <= set(tools)


def test_log_search_finds_deploy():
    result = log_search(service="payments-api", window_minutes=60,
                        patterns=["deploy", "error", "timeout"])
    assert result.simulated is True
    assert len(result.data["deploy_events"]) >= 1
    assert "v2.14.3" in result.data["deploy_events"][-1]["message"]


def test_log_search_filters_by_service():
    result = log_search(service="nonexistent-svc", window_minutes=60,
                        patterns=["deploy"])
    assert result.data["hits"] == []


def test_metrics_query_detects_latency_spike():
    result = metrics_query(
        service="payments-api", window_minutes=60,
        metrics=["p99_latency_ms", "cpu_pct"])
    p99 = result.data["p99_latency_ms"]
    assert p99["pct_change"] > 200
    assert p99["current"] > 2000
    assert "SIGNIFICANT" in result.summary


def test_metrics_query_cpu_flat():
    result = metrics_query(service="payments-api", window_minutes=60,
                           metrics=["cpu_pct"])
    cpu = result.data["cpu_pct"]
    assert abs(cpu["pct_change"]) < 50


def test_runbook_lookup_matches_deployment_regression():
    result = runbook_lookup(query="deployment regression latency spike")
    assert result.data["runbook_id"] == "deployment-regression"
    assert len(result.data["steps"]) >= 3


def test_agent_ranks_bad_deploy_first():
    agent = IncidentAgent(llm=DeterministicDemoPolicy())
    report = agent.run(make_alert(), verbose=False)
    assert len(report.steps) == 3
    assert len(report.hypotheses) == 3
    top = report.hypotheses[0]
    assert "deploy" in top.title.lower()
    confidences = [h.confidence for h in report.hypotheses]
    assert confidences == sorted(confidences, reverse=True)
    assert top.confidence >= 0.7


def test_agent_top_recommendation_is_rollback():
    agent = IncidentAgent(llm=DeterministicDemoPolicy())
    report = agent.run(make_alert(), verbose=False)
    assert "roll back" in report.top_recommendation.lower()


def test_report_json_marks_simulated(tmp_path):
    agent = IncidentAgent(llm=DeterministicDemoPolicy())
    report = agent.run(make_alert(), verbose=False)
    out = str(tmp_path / "report.json")
    payload = render_json(report, out)
    assert payload["data_provenance"].startswith("SIMULATED")
    assert payload["alert"]["service"] == "payments-api"
    assert len(payload["hypotheses"]) == 3
