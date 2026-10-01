"""Tool registry: maps tool names to their implementations."""
from typing import Callable, Dict, List

from tools.log_search import log_search
from tools.metrics_query import metrics_query
from tools.runbook_lookup import runbook_lookup

ToolFn = Callable[..., "object"]

REGISTRY: Dict[str, ToolFn] = {
    "log_search": log_search,
    "metrics_query": metrics_query,
    "runbook_lookup": runbook_lookup,
}


def available_tools() -> List[str]:
    return sorted(REGISTRY.keys())
