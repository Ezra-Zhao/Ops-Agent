"""LLM provider interface.

The agent's reasoning step goes through this interface so a real LLM can be
plugged in without touching the agent loop. The demo ships with a
deterministic policy instead of an LLM: it is honest, reproducible, and makes
the scaffold runnable with zero dependencies.
"""
from typing import Any, Dict, List, Protocol

from .schemas import Alert, ToolCall


class LLMProvider(Protocol):
    """Decides the agent's next action given the alert and history."""

    def next_action(
        self,
        alert: Alert,
        history: List[Dict[str, Any]],
        available_tools: List[str],
    ) -> ToolCall | None:
        """Return the next ToolCall, or None when the agent has enough evidence."""
        ...


class DeterministicDemoPolicy:
    """A fixed, transparent investigation playbook used for the demo.

    This is NOT an LLM: it is a hardcoded SRE investigation sequence
    (logs -> metrics -> runbook -> conclude). It exists so the scaffold runs
    end-to-end without an API key. Replace with a real reasoning model for
    production use.
    """

    def __init__(self) -> None:
        self._step = 0

    def next_action(
        self,
        alert: Alert,
        history: List[Dict[str, Any]],
        available_tools: List[str],
    ) -> ToolCall | None:
        self._step += 1
        service = alert.service

        if self._step == 1:
            return ToolCall(
                name="log_search",
                args={"service": service, "window_minutes": 60,
                      "patterns": ["deploy", "error", "timeout", "exception"]},
                thought=(
                    f"Alert is '{alert.alert_type}' on {service}. "
                    "First, check recent logs for deploys and errors — "
                    "a change right before the alert is the most common culprit."
                ),
            )
        if self._step == 2:
            return ToolCall(
                name="metrics_query",
                args={"service": service, "window_minutes": 60,
                      "metrics": ["p99_latency_ms", "error_rate_pct",
                                  "cpu_pct", "db_pool_used_pct"]},
                thought=(
                    "Logs show a deploy completed 25 minutes before the alert, "
                    "followed by timeout errors. Pull metrics to confirm the "
                    "latency/error correlation and rule out resource saturation."
                ),
            )
        if self._step == 3:
            return ToolCall(
                name="runbook_lookup",
                args={"query": "deployment regression latency spike"},
                thought=(
                    "Metrics confirm latency jumped right after the deploy while "
                    "CPU stayed flat. Look up the runbook for deployment "
                    "regressions to ground the recommendation."
                ),
            )
        # Enough evidence gathered.
        return None


# TODO(ezra): implement this against a real model.
class LangChainChatProvider:
    """Stub for a LangChain-backed reasoning provider.

    Intended design:
      - Build a ReAct prompt from the alert + tool history.
      - Expose the four tools (log_search, metrics_query, runbook_lookup,
        report) as LangChain tools with JSON schemas.
      - Parse the model's structured output into ToolCall, or a finish
        signal when the model judges evidence sufficient.
    """

    def __init__(self, model_name: str = "gpt-4o") -> None:
        self.model_name = model_name

    def next_action(self, alert, history, available_tools):  # type: ignore[no-untyped-def]
        raise NotImplementedError(
            "LangChainChatProvider is a stub. Wire up langchain + an API key "
            "or a local model here; see the docstring for the intended design."
        )
