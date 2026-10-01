# Ops-Agent

**AI Agent for IT Incident Response** — an autonomous agent that responds to
production alerts the way an on-call SRE would: it gathers context (logs,
metrics, runbooks), forms ranked root-cause hypotheses, recommends remediation
steps, and writes up the incident report.

> **Project status: scaffold v0.1 (honest edition).**
> The end-to-end agent loop runs today on **simulated** telemetry and a
> deterministic demo policy. What is real: the ReAct agent loop, the tool
> implementations, hypothesis ranking, and report rendering. What is still
> TODO (clearly marked in code): the LLM reasoning step (currently a
> deterministic policy), real log/metric connectors, and production runbooks.
> Nothing in this repo pretends to be a production incident responder yet.

---

## Problem

When an alert fires at 2 AM, the on-call engineer repeats the same drill:

1. Open the alert: "p99 latency high on payments-api".
2. Grep recent logs for deploys and errors.
3. Pull metrics: latency, error rate, CPU, downstream dependencies.
4. Recall the runbook: what fixed this last time?
5. Decide: rollback? failover? page someone?

That drill is slow, inconsistent, and loses knowledge when people leave.
Ops-Agent encodes it as an **agent loop**: reason → act with tools → observe,
until it has enough evidence to recommend a fix.

## Architecture

```
                    +-------------------+
                    |      Alert        |
                    | (e.g. high p99)   |
                    +--------+----------+
                             |
                    +--------v----------+
                    |  IncidentAgent    |
                    |  ReAct loop       |
                    |  reason -> act -> |
                    |  observe -> ...   |
                    +---+---+---+---+---+
                        |   |   |   |
        +---------------+   |   |   +---------------+
        |                   |   |                   |
+-------v-------+  +--------v---v--------+  +-------v-------+
| log_search    |  | metrics_query       |  | runbook_lookup|
| recent logs,  |  | latency / errors /  |  | known failure |
| deploys, errs |  | cpu / dependencies  |  | modes + fixes |
+---------------+  +---------------------+  +---------------+
   (SIMULATED)            (SIMULATED)            (SIMULATED)
                        |
               +--------v---------+
               | report           |
               | ranked hypotheses|
               | + remediation    |
               | + incident report|
               +------------------+
```

## Ops-Agent vs AI-Node-Sentinel

| | Ops-Agent (this repo) | AI-Node-Sentinel |
|---|---|---|
| Domain | **Generic IT services** (web APIs, databases, infra) | **GPU hardware** (post-silicon, PCIe/XID) |
| Input | Service alerts (latency, errors, saturation) | Node telemetry (dmesg, DCGM/NVML, XID codes) |
| Output | Root-cause hypotheses + remediation steps + incident report | Hardware triage verdicts (drain/reset/reboot/RMA) |
| Skill shown | SRE / AIOps agent design | Hardware diagnostics agent |

Both demonstrate AI-agent engineering; they target different infra roles.

## Quickstart

```bash
pip install -r requirements.txt
python examples/demo.py        # full agent run on a simulated "API latency spike" alert
python -m pytest tests/ -q     # tests
```

The demo prints the complete **thought → action → observation** chain, then the
ranked hypotheses, remediation steps, and the incident report.

## What the demo does

1. A simulated alert fires: p99 latency spike on `payments-api`.
2. The agent searches logs → finds **deploy v2.14.3** completed 25 minutes
   before the alert, followed by timeout errors.
3. The agent queries metrics → p99 jumped 180ms → 2400ms right after the
   deploy; CPU flat; error rate 0.1% → 4.5%.
4. The agent looks up the runbook → matches **deployment-regression**.
5. It outputs hypotheses ranked by confidence:
   - **Bad deploy regression** (0.75) — rollback recommended
   - Downstream dependency slowdown (0.45)
   - Traffic surge (0.30)
6. It writes the incident report (console + `demo/incident_report.json`).

All telemetry is simulated and every result is labeled `SIMULATED`.

## Roadmap

- [ ] Replace the deterministic demo policy with a real LLM reasoning step
      (`agent/llm.py` — `LangChainChatProvider` stub with a TODO)
- [ ] Real connectors: Loki/Elasticsearch logs, Prometheus metrics, PagerDuty alerts
- [ ] Production runbooks contributed by Ezra (TODO marked in
      `tools/runbook_lookup.py`)
- [ ] Multi-alert correlation (cascading failures)
- [ ] Human-in-the-loop approval for remediation actions

## License

MIT — see [LICENSE](LICENSE).
