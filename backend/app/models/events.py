"""SSE Event models — the 13-event protocol between backend and frontend."""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime, timezone


class EventEnvelope(BaseModel):
    """Base envelope for all SSE events."""
    run_id: str
    conversation_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    seq: int = 0
    event: str
    payload: dict[str, Any] = {}


# ── 1. Run Lifecycle ──

class RunStartedPayload(BaseModel):
    user_message_id: str
    query: str


class RunCompletedPayload(BaseModel):
    status: str = "completed"     # completed | failed
    duration_ms: int = 0
    error: Optional[str] = None


# ── 2. Step Events ──

class StepStartedPayload(BaseModel):
    step_id: str
    node: str
    label: str


class StepCompletedPayload(BaseModel):
    step_id: str
    node: str
    status: str = "completed"
    duration_ms: int = 0


class StepOutputPayload(BaseModel):
    step_id: str
    node: str
    output: dict[str, Any] = {}


# ── 3. Tool Events ──

class ToolStartedPayload(BaseModel):
    tool_call_id: str
    tool_name: str
    label: str
    input: dict[str, Any] = {}


class ToolResultPayload(BaseModel):
    tool_call_id: str
    tool_name: str
    result_count: int = 0
    results: list[dict[str, Any]] = []


class ToolFailedPayload(BaseModel):
    tool_call_id: str
    tool_name: str
    error: str
    recoverable: bool = True


# ── 4. Aggregation ──

class SourcesAggregatedPayload(BaseModel):
    statutes: int = 0
    cases: int = 0
    deduplicated_total: int = 0


# ── 5. Answer Streaming ──

class AnswerStartedPayload(BaseModel):
    message_id: str


class AnswerDeltaPayload(BaseModel):
    message_id: str
    delta: str


class AnswerCompletedPayload(BaseModel):
    message_id: str
    final: dict[str, Any] = {}


# ── 6. Follow-up ──

class FollowupRequestedPayload(BaseModel):
    question: str
    missing_fields: list[str] = []


# ── Human-readable step labels ──

STEP_LABELS = {
    "preprocessor": "Processing input",
    "followup_detector": "Checking conversation context",
    "context_resolver": "Resolving context",
    "classifier": "Detecting legal domain",
    "intake_analyzer": "Evaluating case details",
    "planner": "Planning legal research",
    "tool_executor": "Executing research tools",
    "aggregator": "Consolidating legal sources",
    "reasoner": "Preparing legal analysis",
    "formatter": "Finalizing response",
    "graph_extractor": "Building knowledge graph",
}

TOOL_LABELS = {
    "statute_search": "Searching statutes",
    "case_law_search": "Searching relevant cases",
    "search_statutes": "Searching statutes",
    "search_cases": "Searching relevant cases",
    "company_search": "Looking up company information",
}
