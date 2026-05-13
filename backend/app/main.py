"""FastAPI application — SSE streaming endpoint for the Legal AI Agent."""

from __future__ import annotations
import json
import uuid
import time
import asyncio
import logging
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from app.config import settings
from app.graph.workflow import legal_graph
from app.services.memory import memory_store
from app.services.mcp_client import shutdown_mcp, list_mcp_tools
from app.services.graph_store import graph_store
from app.models.state import GraphState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── FastAPI App ──

app = FastAPI(
    title="Legal AI Agent",
    description="Contract & Business Legal Intelligence System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request Models ──

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str


class ConversationCreate(BaseModel):
    title: Optional[str] = None


# ── SSE Streaming Endpoint ──

@app.post("/api/chat")
async def chat_stream(request: ChatRequest):
    """
    Main chat endpoint — streams SSE events from the LangGraph pipeline.

    The frontend consumes these events to render:
    1. Activity card (progressive step updates)
    2. Streamed legal answer
    3. Citations
    """

    # Get or create conversation
    conversation_id = request.conversation_id
    if not conversation_id or not memory_store.get_conversation(conversation_id):
        conversation_id = memory_store.create_conversation(conversation_id)

    run_id = str(uuid.uuid4())

    # Load conversation context
    history = memory_store.get_history(conversation_id)
    case_memory = memory_store.get_case_memory(conversation_id)

    # Load clarification count for multi-turn dialogue
    clarification_count = memory_store.get_clarification_count(conversation_id)

    # Build initial state
    initial_state: GraphState = {
        "run_id": run_id,
        "conversation_id": conversation_id,
        "user_input": request.message,
        "resolved_input": request.message,
        "followup_context": None,
        "needs_clarification": False,
        "clarification_question": None,
        "clarification_count": clarification_count,
        "classification": {},
        "plan": {},
        "retrieval": {},
        "aggregation": {},
        "reasoning": {},
        "output": {},
        "meta": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "running",
        },
        "conversation_history": history,
        "case_memory": case_memory,
    }

    async def event_generator() -> AsyncGenerator[str, None]:
        """Async generator that yields SSE events from LangGraph."""
        seq = 0
        start_time = time.time()

        # Emit run_started
        seq += 1
        yield _sse_event("run_started", {
            "run_id": run_id,
            "conversation_id": conversation_id,
            "timestamp": time.time(),
            "seq": seq,
            "event": "run_started",
            "payload": {
                "user_message_id": f"msg_{uuid.uuid4().hex[:8]}",
                "query": request.message,
            },
        })

        final_output = {}
        clarification_question = None

        try:
            # Stream the graph execution
            async for event in legal_graph.astream(
                initial_state,
                stream_mode=["custom", "updates"],
            ):
                if isinstance(event, tuple) and len(event) == 2:
                    stream_type, data = event

                    if stream_type == "custom":
                        # Custom events from our EventEmitter
                        seq += 1
                        data["seq"] = seq
                        yield _sse_event(data.get("event", "update"), data)

                    elif stream_type == "updates":
                        # State updates from nodes
                        if isinstance(data, dict):
                            for node_name, state_update in data.items():
                                if isinstance(state_update, dict):
                                    if "output" in state_update:
                                        final_output = state_update["output"]
                                    if "clarification_question" in state_update:
                                        clarification_question = state_update["clarification_question"]

                elif isinstance(event, dict):
                    # Handle flat dict events
                    if "event" in event:
                        seq += 1
                        event["seq"] = seq
                        yield _sse_event(event.get("event", "update"), event)
                    else:
                        # State update
                        for node_name, state_update in event.items():
                            if isinstance(state_update, dict):
                                if "output" in state_update:
                                    final_output = state_update["output"]
                                if "clarification_question" in state_update:
                                    clarification_question = state_update["clarification_question"]

        except Exception as e:
            import traceback
            logger.error(f"Graph execution error: {e}\n{traceback.format_exc()}")
            seq += 1
            yield _sse_event("run_completed", {
                "run_id": run_id,
                "conversation_id": conversation_id,
                "timestamp": time.time(),
                "seq": seq,
                "event": "run_completed",
                "payload": {
                    "status": "failed",
                    "duration_ms": int((time.time() - start_time) * 1000),
                    "error": str(e),
                },
            })
            return

        # Emit run_completed
        duration_ms = int((time.time() - start_time) * 1000)
        seq += 1
        yield _sse_event("run_completed", {
            "run_id": run_id,
            "conversation_id": conversation_id,
            "timestamp": time.time(),
            "seq": seq,
            "event": "run_completed",
            "payload": {
                "status": "completed",
                "duration_ms": duration_ms,
            },
        })

        # Update conversation memory
        if clarification_question and not final_output:
            # Pipeline terminated early with a clarification question
            memory_store.update_after_clarification(
                conversation_id=conversation_id,
                user_input=request.message,
                question=clarification_question,
                case_memory={
                    "facts": [request.message],
                },
                title=request.message[:50].strip() + ("..." if len(request.message) > 50 else ""),
            )
        elif final_output:
            # Full analysis completed
            title = None
            issue = final_output.get("issue", "")
            if issue:
                title = issue[:60].replace("Whether ", "").strip()
                if len(issue) > 60:
                    title += "..."

            memory_store.update_after_run(
                conversation_id=conversation_id,
                user_input=request.message,
                output=final_output,
                case_memory={
                    "domain": final_output.get("domain", ""),
                    "issue": final_output.get("issue", ""),
                    "facts": [request.message],
                },
                title=title,
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse_event(event_type: str, data: dict) -> str:
    """Format a dict as an SSE event string."""
    json_str = json.dumps(data, default=str)
    return f"event: {event_type}\ndata: {json_str}\n\n"


# ── REST Endpoints ──

@app.get("/api/conversations")
async def list_conversations():
    """List all conversations."""
    return {"conversations": memory_store.list_conversations()}


@app.post("/api/conversations")
async def create_conversation(body: ConversationCreate = None):
    """Create a new conversation."""
    cid = memory_store.create_conversation()
    convo = memory_store.get_conversation(cid)
    if body and body.title:
        convo["title"] = body.title
    return {"id": cid, "title": convo["title"]}


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation details and messages."""
    convo = memory_store.get_conversation(conversation_id)
    if not convo:
        return {"error": "Not found"}, 404
    return {
        "id": convo["id"],
        "title": convo["title"],
        "messages": convo["messages"],
        "created_at": convo["created_at"],
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        tools = await list_mcp_tools()
    except Exception:
        tools = []
    return {
        "status": "ok",
        "model": settings.gemini_model,
        "mcp_tools": tools,
    }


# ── Graph API Endpoints ──

@app.get("/api/graph/{conversation_id}")
async def get_conversation_graph(conversation_id: str):
    """Get the knowledge graph for a specific conversation."""
    graph = graph_store.get_graph(conversation_id)
    return graph


@app.get("/api/graph")
async def get_global_graph():
    """Get a merged global knowledge graph from all conversations."""
    graph = graph_store.get_all_graphs()
    return graph


@app.on_event("shutdown")
async def on_shutdown():
    """Gracefully shut down MCP server processes."""
    await shutdown_mcp()


# ── Run ──

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
