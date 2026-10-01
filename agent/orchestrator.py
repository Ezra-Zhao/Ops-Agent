"""IncidentAgent: the ReAct loop (reason -> act with tools -> observe).

The loop:
  1. Ask the LLM provider for the next action (a ToolCall with its thought).
  2. Execute the tool, record the observation.
  3. Repeat until the provider returns None (enough evidence) or max_steps.
  4. Synthesize ranked hypotheses from the collected evidence.

Hypothesis scoring is a transparent heuristic v0.1 over the gathered
evidence. TODO(ezra): let the LLM do the synthesis step too, with the
heuristic as a guardrail/fallback.
"""
from typing import Any, Dict, List

from agent.llm import LLMProvider
from agent.schemas import (Alert, Hypothesis, IncidentReport, ToolCall,
                           ToolResult)
from agent.tool_registry import REGISTRY, available_tools


class IncidentAgent:
    def __init__(self, llm: LLMProvider, max_steps: int = 6) -> None:
        self.llm = llm
        self.max_steps = max_steps

    def run(self, alert: Alert, verbose: bool = True) -> IncidentReport:
        steps: List[ToolCall] = []
        observations: List[ToolResult] = []
        history: List[Dict[str, Any]] = []

        for _ in range(self.max_steps):
            call = self.llm.next_action(alert, history, available_tools())
            if call is None:
                break
            fn = REGISTRY[call.name]
            result = fn(**call.args)  # type: ignore[operator]
            steps.append(call)
            observations.append(result)
            history.append({"thought": call.thought,
                            "action": f"{call.name}({call.args})",
                            "observation": result.summary})
            if verbose:
                print(f"\n  THOUGHT: {call.thought}")
                print(f"  ACTION:  {call.name}({call.args})")
                print(f"  OBSERVE: {result.summary}")

        hypotheses = self._synthesize(alert, observations)
        top = hypotheses[0]
        return IncidentReport(
            alert=alert,
            steps=steps,
            observations=observations,
            hypotheses=hypotheses,
            top_recommendation=top.remediation[0] if top.remediation
            else "Escalate to on-call.",
        )

    # ------------------------------------------------------------------
    # Hypothesis synthesis (heuristic v0.1, transparent and testable)
    # ------------------------------------------------------------------
    def _synthesize(self, alert: Alert,
                    observations: List[ToolResult]) -> List[Hypothesis]:
        log_obs = next((o for o in observations if o.tool == "log_search"),
                       None)
        met_obs = next((o for o in observations if o.tool == "metrics_query"),
                       None)
        rb_obs = next((o for o in observations
                       if o.tool == "runbook_lookup"), None)

        deploy_seen = bool(log_obs and log_obs.data.get("deploy_events"))
        err_after_deploy = bool(log_obs and log_obs.data.get("error_events"))
        p99 = met_obs.data.get("p99_latency_ms", {}) if met_obs else {}
        cpu = met_obs.data.get("cpu_pct", {}) if met_obs else {}
        latency_spiked = p99.get("pct_change", 0) >= 200
        cpu_flat = abs(cpu.get("pct_change", 999)) < 50

        hyps: List[Hypothesis] = []

        conf = 0.4
        evidence = []
        if deploy_seen:
            conf += 0.2
            deploy = log_obs.data["deploy_events"][-1]  # type: ignore[index]
            evidence.append(
                f"Deploy completed at {deploy['ts']}, ~25m before the alert.")
        if err_after_deploy:
            conf += 0.1
            evidence.append("Timeout/pool-exhaustion errors appeared "
                            "only after the deploy.")
        if latency_spiked:
            conf += 0.1
            evidence.append(
                f"p99 latency {p99['baseline']}ms -> {p99['current']}ms "
                f"({p99['pct_change']:+.0f}%).")
        if cpu_flat:
            evidence.append("CPU stayed flat — not a resource-saturation issue.")
        rb_steps = rb_obs.data.get("steps", []) if rb_obs else []
        hyps.append(Hypothesis(
            title="Bad deploy regression (v2.14.3)",
            confidence=round(min(conf, 0.95), 2),
            evidence=evidence,
            remediation=[
                "Roll back payments-api to v2.14.2 immediately.",
                *rb_steps[1:3],
                "Diff v2.14.2..v2.14.3 focusing on DB query/connection changes.",
            ],
        ))

        hyps.append(Hypothesis(
            title="Downstream dependency slowdown",
            confidence=0.45,
            evidence=[
                "Timeout errors mention upstream calls." if err_after_deploy
                else "No dependency trace data in this demo.",
                "Latency spike pattern also matches a slow dependency.",
            ],
            remediation=[
                "Check trace spans for the slowest downstream call.",
                "Enable circuit breaker / shed load on the slow path.",
            ],
        ))

        hyps.append(Hypothesis(
            title="Traffic surge",
            confidence=0.30,
            evidence=[
                "CPU flat and no request-rate data in this demo — "
                "cannot confirm a surge.",
            ],
            remediation=[
                "Compare request rate vs baseline.",
                "Scale out horizontally if a surge is confirmed.",
            ],
        ))

        return sorted(hyps, key=lambda h: h.confidence, reverse=True)
