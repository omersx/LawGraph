"""Node 3: Context Resolver — merges prior case memory with current input for follow-ups."""

from __future__ import annotations
from langgraph.config import get_stream_writer
from app.models.state import GraphState
from app.graph.event_emitter import EventEmitter
from app.services.llm import get_flash_model, extract_text_content


RESOLVER_PROMPT = """You are a Context Resolver for a legal AI system.

Given:
- the user's current message
- previous case facts from the conversation

Your job: produce a single, clear paragraph that combines the prior facts with the new question so the downstream system can understand the full context.

Do NOT perform legal analysis.
Do NOT answer the question.
Just merge the context into one clear statement.

Previous case facts:
{facts}

Current user message:
{message}

Write the resolved context as a single clear paragraph:"""


async def context_resolver_node(state: GraphState) -> dict:
    """Resolve context by merging case memory with current input."""
    writer = get_stream_writer()
    emitter = EventEmitter(writer, state.get("run_id", ""), state.get("conversation_id", ""))

    followup = state.get("followup_context", {})

    # If not a follow-up, pass through
    if not followup.get("is_follow_up", False):
        return {"resolved_input": state.get("user_input", "")}

    emitter.step_started("context_resolver")

    user_input = state.get("user_input", "")
    case_memory = state.get("case_memory", {})

    # Build facts summary
    facts_parts = []
    parties = case_memory.get("parties", {})
    if parties:
        for role, name in parties.items():
            facts_parts.append(f"{role}: {name}")

    stored_facts = case_memory.get("facts", [])
    if stored_facts:
        facts_parts.extend(stored_facts)

    domain = case_memory.get("domain", "")
    if domain:
        facts_parts.append(f"Domain: {domain}")

    issue = case_memory.get("issue", "")
    if issue:
        facts_parts.append(f"Previous issue: {issue}")

    # Also use conversation history
    history = state.get("conversation_history", [])
    for turn in history[-2:]:
        facts_parts.append(f"Previous question: {turn.get('user', '')}")
        facts_parts.append(f"Previous answer summary: {turn.get('assistant_summary', '')}")

    facts_str = "\n".join(facts_parts) if facts_parts else "No prior context available."

    try:
        prompt = RESOLVER_PROMPT.format(facts=facts_str, message=user_input)
        model = get_flash_model(temperature=0.1)
        response = await model.ainvoke(prompt)
        resolved = extract_text_content(response).strip()

        emitter.step_completed("context_resolver")
        return {"resolved_input": resolved}

    except Exception:
        emitter.step_completed("context_resolver")
        return {"resolved_input": user_input}
