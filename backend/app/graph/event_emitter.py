"""Event emitter — utility to emit SSE events from inside LangGraph nodes."""

from __future__ import annotations
import json
import time
import uuid
from typing import Any, Callable
from app.models.events import STEP_LABELS, TOOL_LABELS


class EventEmitter:
    """
    Wraps the LangGraph stream writer to emit structured SSE events.

    Usage inside a node:
        emitter = EventEmitter(writer, run_id, conversation_id)
        emitter.step_started("classifier")
        ... do work ...
        emitter.step_completed("classifier")
    """

    def __init__(self, writer: Callable, run_id: str, conversation_id: str):
        self._writer = writer
        self._run_id = run_id
        self._conversation_id = conversation_id
        self._seq = 0
        self._step_timers: dict[str, float] = {}

    def _emit(self, event_type: str, payload: dict[str, Any]):
        """Emit a single SSE event."""
        self._seq += 1
        envelope = {
            "run_id": self._run_id,
            "conversation_id": self._conversation_id,
            "timestamp": time.time(),
            "seq": self._seq,
            "event": event_type,
            "payload": payload,
        }
        self._writer(envelope)

    # ── Run Lifecycle ──

    def run_started(self, query: str, message_id: str = ""):
        msg_id = message_id or f"msg_{uuid.uuid4().hex[:8]}"
        self._emit("run_started", {
            "user_message_id": msg_id,
            "query": query,
        })

    def run_completed(self, status: str = "completed", error: str = None):
        payload = {"status": status, "duration_ms": 0}
        if error:
            payload["error"] = error
        self._emit("run_completed", payload)

    # ── Step Events ──

    def step_started(self, node: str, step_id: str = ""):
        sid = step_id or f"step_{node}"
        label = STEP_LABELS.get(node, f"Processing {node}")
        self._step_timers[node] = time.time()
        self._emit("step_started", {
            "step_id": sid,
            "node": node,
            "label": label,
        })

    def step_completed(self, node: str, step_id: str = ""):
        sid = step_id or f"step_{node}"
        start = self._step_timers.pop(node, time.time())
        duration_ms = int((time.time() - start) * 1000)
        self._emit("step_completed", {
            "step_id": sid,
            "node": node,
            "status": "completed",
            "duration_ms": duration_ms,
        })

    def step_output(self, node: str, output: dict, step_id: str = ""):
        sid = step_id or f"step_{node}"
        self._emit("step_output", {
            "step_id": sid,
            "node": node,
            "output": output,
        })

    # ── Tool Events ──

    def tool_started(self, tool_name: str, query: str, tool_call_id: str = ""):
        tcid = tool_call_id or f"tool_{uuid.uuid4().hex[:8]}"
        label = TOOL_LABELS.get(tool_name, f"Using {tool_name}")
        self._emit("tool_started", {
            "tool_call_id": tcid,
            "tool_name": tool_name,
            "label": label,
            "input": {"query": query},
        })
        return tcid

    def tool_result(self, tool_call_id: str, tool_name: str, results: list[dict]):
        self._emit("tool_result", {
            "tool_call_id": tool_call_id,
            "tool_name": tool_name,
            "result_count": len(results),
            "results": results,
        })

    def tool_failed(self, tool_call_id: str, tool_name: str, error: str, recoverable: bool = True):
        self._emit("tool_failed", {
            "tool_call_id": tool_call_id,
            "tool_name": tool_name,
            "error": error,
            "recoverable": recoverable,
        })

    # ── Aggregation ──

    def sources_aggregated(self, statutes: int, cases: int, total: int):
        self._emit("sources_aggregated", {
            "statutes": statutes,
            "cases": cases,
            "deduplicated_total": total,
        })

    # ── Answer Streaming ──

    def answer_started(self, message_id: str = ""):
        mid = message_id or f"ans_{uuid.uuid4().hex[:8]}"
        self._emit("answer_started", {"message_id": mid})
        return mid

    def answer_delta(self, message_id: str, delta: str):
        self._emit("answer_delta", {
            "message_id": message_id,
            "delta": delta,
        })

    def answer_completed(self, message_id: str, final_output: dict):
        self._emit("answer_completed", {
            "message_id": message_id,
            "final": final_output,
        })

    # ── Follow-up ──

    def followup_requested(self, question: str, missing_fields: list[str] = None):
        self._emit("followup_requested", {
            "question": question,
            "missing_fields": missing_fields or [],
        })
