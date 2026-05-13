"""Node 6: Tool Executor — calls MCP tools via the external server."""

from __future__ import annotations
import asyncio
import uuid
from langgraph.config import get_stream_writer
from app.models.state import GraphState
from app.graph.event_emitter import EventEmitter
from app.services.mcp_client import call_mcp_tool


async def tool_executor_node(state: GraphState) -> dict:
    """Execute MCP tools based on the planner's output."""
    writer = get_stream_writer()
    emitter = EventEmitter(writer, state.get("run_id", ""), state.get("conversation_id", ""))

    emitter.step_started("tool_executor")

    plan = state.get("plan", {})
    tool_calls = plan.get("tool_calls", [])
    parallel = plan.get("parallel", True)

    retrieval: dict[str, list] = {}

    if not tool_calls:
        emitter.step_completed("tool_executor")
        return {"retrieval": retrieval}

    async def execute_single_tool(tc: dict):
        """Execute a single tool call and emit events."""
        tool_name = tc["tool_name"]
        query = tc["query"]
        tool_call_id = f"tool_{uuid.uuid4().hex[:8]}"

        emitter.tool_started(tool_name, query, tool_call_id)

        try:
            results = await call_mcp_tool(tool_name, {"query": query})

            # Normalize results
            normalized = []
            for item in (results or [])[:5]:  # Max 5 results per tool
                normalized.append({
                    "type": "statute" if "statute" in tool_name.lower() else "case",
                    "title": item.get("title", item.get("case_name", "")),
                    "citation": item.get("citation", ""),
                    "court": item.get("court", ""),
                    "year": str(item.get("year", "")),
                    "summary": item.get("summary", item.get("snippet", "")),
                    "source": item.get("source", tool_name),
                    "source_url": item.get("source_url", item.get("url", "")),
                })

            emitter.tool_result(tool_call_id, tool_name, normalized)

            # Accumulate results by tool name
            if tool_name not in retrieval:
                retrieval[tool_name] = []
            retrieval[tool_name].extend(normalized)

        except Exception as e:
            emitter.tool_failed(tool_call_id, tool_name, str(e))

    if parallel and len(tool_calls) > 1:
        await asyncio.gather(*[execute_single_tool(tc) for tc in tool_calls])
    else:
        for tc in tool_calls:
            await execute_single_tool(tc)

    emitter.step_completed("tool_executor")

    return {"retrieval": retrieval}
