"""LangGraph state schema — the canonical shared state for all nodes."""

from __future__ import annotations
from typing import TypedDict, Optional, Any
from dataclasses import dataclass, field


# ── Classification Output ──

class ClassificationState(TypedDict, total=False):
    domain: str            # contract_law | commercial_law | tort_law | employment_law | unknown
    intent: str            # legal_analysis | legal_information | case_lookup | statute_lookup | company_lookup | unknown
    needs_statutes: bool
    needs_cases: bool


# ── Plan Output ──

class ToolCall(TypedDict):
    tool_name: str
    query: str


class PlanState(TypedDict, total=False):
    tool_calls: list[ToolCall]
    parallel: bool


# ── Follow-up Context ──

class FollowupContext(TypedDict, total=False):
    is_follow_up: bool
    reason: str            # pronoun_reference | contextual_reference | short_follow_up | new_issue | standalone
    resolved_context: str
    active_case_memory: dict[str, Any]


# ── Retrieval Result ──

class RetrievalItem(TypedDict, total=False):
    type: str              # statute | case
    title: str
    citation: str
    court: str
    year: str
    summary: str
    source: str
    source_url: str
    holding: str           # Extracted core holding from opinion text
    principle: str         # Key legal principle
    relevance: str         # Why this case is relevant
    opinion_enriched: bool # Whether full opinion was analyzed


# ── Aggregation Output ──

class AggregationState(TypedDict, total=False):
    legal_sources: list[RetrievalItem]
    retrieval_summary: str


# ── Reasoning Internal ──

class ReasoningState(TypedDict, total=False):
    case_facts: str
    legal_issue: str
    reasoning_context: list[str]


# ── Citation ──

class Citation(TypedDict, total=False):
    type: str              # statute | case
    title: str
    citation: str
    source: str
    source_url: str


# ── Final Output ──

class OutputState(TypedDict, total=False):
    domain: str
    jurisdiction: str          # e.g. "United States"
    issue: str
    answer: str
    legal_reasoning: str
    legal_basis: list[str]
    citations: list[Citation]
    confidence: float


# ── Execution Metadata ──

class MetaState(TypedDict, total=False):
    created_at: str
    started_at: str
    completed_at: str
    status: str            # running | completed | failed | paused


# ── Case Memory (persistent across turns) ──

class CaseMemory(TypedDict, total=False):
    parties: dict[str, str]
    facts: list[str]
    domain: str
    issue: str


class ConversationTurn(TypedDict, total=False):
    user: str
    assistant_summary: str
    domain: str
    issue: str


# ══════════════════════════════════════════════
#  MAIN GRAPH STATE — all nodes read/write here
# ══════════════════════════════════════════════

class GraphState(TypedDict, total=False):
    # Identity
    run_id: str
    conversation_id: str

    # Input
    user_input: str
    resolved_input: str             # After context resolution

    # Follow-up detection
    followup_context: Optional[FollowupContext]

    # Clarification (multi-turn dialogue)
    needs_clarification: bool                    # Flag for conditional edge
    clarification_question: Optional[str]        # Question to ask the user
    clarification_count: int                     # Rounds so far (max 2)

    # Pipeline outputs (each node writes ONLY its slot)
    classification: ClassificationState
    plan: PlanState
    retrieval: dict[str, list[RetrievalItem]]   # tool_name → results
    aggregation: AggregationState
    reasoning: ReasoningState
    output: OutputState
    meta: MetaState

    # Conversation memory (carried between runs)
    conversation_history: list[ConversationTurn]
    case_memory: CaseMemory
