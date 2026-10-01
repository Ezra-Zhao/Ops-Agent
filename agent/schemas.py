"""Data models for the incident response agent."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Alert:
    """An incoming production alert."""
    id: str
    service: str
    alert_type: str          # e.g. "high_p99_latency"
    severity: str            # info | warning | critical
    fired_at: str            # ISO timestamp
    description: str


@dataclass
class ToolCall:
    """One agent action: invoke a named tool with arguments."""
    name: str
    args: Dict[str, Any]
    thought: str             # why the agent chose this action


@dataclass
class ToolResult:
    """What the tool returned (always labeled with its data source)."""
    tool: str
    summary: str
    data: Dict[str, Any] = field(default_factory=dict)
    simulated: bool = True


@dataclass
class Hypothesis:
    """A ranked root-cause hypothesis."""
    title: str
    confidence: float        # 0.0 - 1.0
    evidence: List[str]
    remediation: List[str]


@dataclass
class IncidentReport:
    """Final output of an agent run."""
    alert: Alert
    steps: List[ToolCall]
    observations: List[ToolResult]
    hypotheses: List[Hypothesis]
    top_recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert": {
                "id": self.alert.id,
                "service": self.alert.service,
                "type": self.alert.alert_type,
                "severity": self.alert.severity,
                "fired_at": self.alert.fired_at,
                "description": self.alert.description,
            },
            "steps_taken": len(self.steps),
            "hypotheses": [
                {
                    "title": h.title,
                    "confidence": h.confidence,
                    "evidence": h.evidence,
                    "remediation": h.remediation,
                }
                for h in self.hypotheses
            ],
            "top_recommendation": self.top_recommendation,
            "data_provenance": "SIMULATED - demo data, not production telemetry",
        }
