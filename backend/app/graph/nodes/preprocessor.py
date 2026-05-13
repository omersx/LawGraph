"""Node 1: Input Preprocessor — cleans and normalizes user input."""

from __future__ import annotations
import re
from langgraph.config import get_stream_writer
from app.models.state import GraphState
from app.graph.event_emitter import EventEmitter


def preprocessor_node(state: GraphState) -> dict:
    """Clean and normalize the user input."""
    writer = get_stream_writer()
    emitter = EventEmitter(writer, state.get("run_id", ""), state.get("conversation_id", ""))

    emitter.step_started("preprocessor")

    raw_input = state.get("user_input", "")

    # Basic text normalization
    cleaned = raw_input.strip()
    cleaned = re.sub(r"\s+", " ", cleaned)     # collapse whitespace
    cleaned = re.sub(r"\n+", " ", cleaned)     # collapse newlines

    emitter.step_completed("preprocessor")

    return {"user_input": cleaned, "resolved_input": cleaned}
