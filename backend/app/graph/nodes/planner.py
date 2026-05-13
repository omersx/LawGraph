"""Node 5: Planner — decides which tools to call and generates search queries."""

from __future__ import annotations
import json
from langgraph.config import get_stream_writer
from app.models.state import GraphState
from app.graph.event_emitter import EventEmitter
from app.services.llm import get_flash_model, extract_text_content


PLANNER_PROMPT = """You are a Legal Query Planner.

Your role is to decide:
1. Which tools should be used
2. What search queries should be generated

You DO NOT perform legal reasoning.

Given:
- the user's legal input
- classification results

Return a structured plan for tool usage.

OUTPUT FORMAT (STRICT JSON ONLY):
{
  "tools_to_call": [...],
  "queries": [...]
}

FIELD DEFINITIONS:

tools_to_call — Choose from:
- "search_statutes"
- "search_cases"

Rules:
- Include only necessary tools
- Max 2-3 tools

queries — List of 1-3 search queries:
- Each query must be short, relevant, keyword-based
- Convert user issue into search-friendly queries

PLANNING RULES:
- If needs_statutes = true → include "search_statutes"
- If needs_cases = true → include "search_cases"

Query Generation Examples:
User: "Client didn't pay after service"
Queries: ["breach of contract non payment services", "case law failure to pay after performance"]

User: "Supplier didn't deliver goods"
Queries: ["breach of contract failure to deliver goods", "non delivery contract law"]

STRICT RULES:
- Do NOT perform legal reasoning
- Do NOT generate long sentences
- Do NOT include explanations
- Do NOT output outside JSON
- Return valid JSON only

OUTPUT ONLY JSON."""


async def planner_node(state: GraphState) -> dict:
    """Plan which tools to call and generate search queries."""
    writer = get_stream_writer()
    emitter = EventEmitter(writer, state.get("run_id", ""), state.get("conversation_id", ""))

    emitter.step_started("planner")

    resolved_input = state.get("resolved_input", state.get("user_input", ""))
    classification = state.get("classification", {})

    prompt = f"""{PLANNER_PROMPT}

User input: {resolved_input}
Domain: {classification.get('domain', 'unknown')}
Intent: {classification.get('intent', 'legal_analysis')}
Needs statutes: {classification.get('needs_statutes', True)}
Needs cases: {classification.get('needs_cases', True)}"""

    try:
        model = get_flash_model(temperature=0.1)
        response = await model.ainvoke(prompt)
        content = extract_text_content(response).strip()

        # Parse JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        result = json.loads(content)

        tools = result.get("tools_to_call", [])
        queries = result.get("queries", [])

        # Build tool_calls list
        tool_calls = []
        for tool in tools:
            for query in queries[:2]:  # Max 2 queries per tool
                tool_calls.append({"tool_name": tool, "query": query})

        plan = {
            "tool_calls": tool_calls,
            "parallel": True,
        }

        emitter.step_output("planner", {"tools": tools, "queries": queries})
        emitter.step_completed("planner")

        return {"plan": plan}

    except Exception as e:
        # Default plan: search both with user input as query
        emitter.step_completed("planner")
        default_calls = []
        if classification.get("needs_statutes", True):
            default_calls.append({"tool_name": "search_statutes", "query": resolved_input})
        if classification.get("needs_cases", True):
            default_calls.append({"tool_name": "search_cases", "query": resolved_input})

        return {"plan": {"tool_calls": default_calls, "parallel": True}}
