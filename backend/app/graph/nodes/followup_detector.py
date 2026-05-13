"""Node 2: Follow-up Detector — determines if message depends on prior context."""

from __future__ import annotations
import json
from langgraph.config import get_stream_writer
from app.models.state import GraphState
from app.graph.event_emitter import EventEmitter
from app.services.llm import get_flash_model, extract_text_content

FOLLOWUP_PROMPT = """You are a Conversation Follow-Up Detector for a legal AI system.

Your task is to determine whether the current user message depends on prior conversation context.

You do NOT perform legal analysis.
You do NOT classify legal domain.
You only detect whether previous conversation facts are needed to correctly understand the user's message.

Given:
- current user message
- optional recent conversation context

Determine whether the message is:
- a follow-up to earlier conversation, or
- a new standalone legal issue

Output STRICT JSON ONLY:
{
  "is_follow_up": true/false,
  "reason": "pronoun_reference | contextual_reference | short_follow_up | new_issue | standalone"
}

Decision Rules:
- Mark is_follow_up = true if the message contains pronouns (they, he, she, it, that, those), contextual references (in that case, what now, then what, can I sue now), or very short follow-up questions that need prior context.
- Mark is_follow_up = false if the user introduces a new complete legal issue.

Return ONLY JSON. No explanations."""


async def followup_detector_node(state: GraphState) -> dict:
    """Detect whether the current message is a follow-up to prior context."""
    writer = get_stream_writer()
    emitter = EventEmitter(writer, state.get("run_id", ""), state.get("conversation_id", ""))

    emitter.step_started("followup_detector")

    user_input = state.get("user_input", "")
    history = state.get("conversation_history", [])

    # If no history, it's definitely not a follow-up
    if not history:
        emitter.step_completed("followup_detector")
        return {
            "followup_context": {
                "is_follow_up": False,
                "reason": "standalone",
                "resolved_context": "",
                "active_case_memory": {},
            }
        }

    # Build context summary from recent history
    context_summary = ""
    for turn in history[-3:]:
        context_summary += f"User: {turn.get('user', '')}\n"
        context_summary += f"Issue: {turn.get('issue', '')}\n"

    prompt = f"""{FOLLOWUP_PROMPT}

Recent conversation context:
{context_summary}

Current user message:
{user_input}"""

    try:
        model = get_flash_model(temperature=0.0)
        response = await model.ainvoke(prompt)
        content = extract_text_content(response).strip()

        # Parse JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        result = json.loads(content)

        emitter.step_output("followup_detector", result)
        emitter.step_completed("followup_detector")

        return {
            "followup_context": {
                "is_follow_up": result.get("is_follow_up", False),
                "reason": result.get("reason", "standalone"),
                "resolved_context": "",
                "active_case_memory": state.get("case_memory", {}),
            }
        }

    except Exception as e:
        # On failure, treat as standalone
        emitter.step_completed("followup_detector")
        return {
            "followup_context": {
                "is_follow_up": False,
                "reason": "standalone",
                "resolved_context": "",
                "active_case_memory": {},
            }
        }
