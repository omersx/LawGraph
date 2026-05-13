"""Node 4.5: Intake Analyzer — decides if enough case details exist for full analysis.

Sits between classifier and planner. Uses the LLM to evaluate whether the
user has provided sufficient facts (jurisdiction, timeline, parties, key
events) to perform a complete IRAC analysis.  When critical details are
missing, it generates a natural follow-up question and terminates the
pipeline early so the user can respond.
"""

from __future__ import annotations
import json
from langgraph.config import get_stream_writer
from app.models.state import GraphState
from app.graph.event_emitter import EventEmitter
from app.services.llm import get_flash_model, extract_text_content


INTAKE_PROMPT = """You are a Legal Intake Analyst for an AI legal consultation system.

Your job is to evaluate whether the user's legal question has enough detail for a thorough legal analysis.

Given:
- The user's message (possibly enriched with prior conversation context)
- The detected legal domain
- Any existing case memory from prior turns

Evaluate whether you have ENOUGH information to perform a complete IRAC legal analysis.

CHECK FOR THESE CRITICAL DETAILS:
1. Timeline (when did events occur? how long ago?)
2. Parties involved (who is the user dealing with?)
3. Key facts of the dispute (what happened specifically?)
4. Specific legal question (what does the user want to know?)

IMPORTANT: This system is for U.S. law ONLY. Do NOT ask about jurisdiction, state, or country — assume United States.

DECISION RULES:
- If 2+ of the 4 items above are clearly present → has_enough_info = true
- If the query is very specific and self-contained → has_enough_info = true
- If critical context is missing (especially what happened) → has_enough_info = false
- If the user is asking a general legal information question (not a specific dispute) → has_enough_info = true
- NEVER ask more than 2-3 things at once

OUTPUT FORMAT (STRICT JSON ONLY):
{{
  "has_enough_info": true/false,
  "missing_fields": ["timeline", "parties", ...],
  "question": "Natural, conversational follow-up question (only if has_enough_info is false)"
}}

QUESTION STYLE:
- Be warm and professional — like a helpful attorney in an initial consultation
- Ask about 1-3 missing items in ONE natural sentence
- Do NOT create a numbered checklist
- Do NOT be robotic
- Example: "I'd be happy to help with your deposit situation. Could you tell me roughly when you paid the deposit and if you have a written agreement?"

Return ONLY JSON. No explanations."""


async def intake_analyzer_node(state: GraphState) -> dict:
    """Evaluate if enough case details exist; ask clarifying questions if not."""
    writer = get_stream_writer()
    emitter = EventEmitter(writer, state.get("run_id", ""), state.get("conversation_id", ""))

    emitter.step_started("intake_analyzer")

    resolved_input = state.get("resolved_input", state.get("user_input", ""))
    classification = state.get("classification", {})
    case_memory = state.get("case_memory", {})
    history = state.get("conversation_history", [])
    clarification_count = state.get("clarification_count", 0)

    # If we've already asked 2 times, proceed with what we have
    if clarification_count >= 2:
        emitter.step_output("intake_analyzer", {"decision": "max_rounds_reached", "proceeding": True})
        emitter.step_completed("intake_analyzer")
        return {"needs_clarification": False}

    # Build context for the LLM
    memory_summary = ""
    if case_memory:
        facts = case_memory.get("facts", [])
        if facts:
            memory_summary = f"\nKnown case facts from prior turns:\n" + "\n".join(f"- {f}" for f in facts)
        domain = case_memory.get("domain", "")
        if domain:
            memory_summary += f"\nPreviously detected domain: {domain}"
        issue = case_memory.get("issue", "")
        if issue:
            memory_summary += f"\nPrevious issue: {issue}"

    history_summary = ""
    if history:
        for turn in history[-3:]:
            history_summary += f"\nUser previously said: {turn.get('user', '')}"
            summary = turn.get('assistant_summary', '')
            if summary and len(summary) > 100:
                summary = summary[:100] + "..."
            if summary:
                history_summary += f"\nAgent responded: {summary}"

    prompt = f"""{INTAKE_PROMPT}

User message: {resolved_input}
Detected domain: {classification.get('domain', 'unknown')}
Detected intent: {classification.get('intent', 'unknown')}
Clarification rounds so far: {clarification_count}
{memory_summary}
{history_summary}"""

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

        has_enough = result.get("has_enough_info", True)
        question = result.get("question", "")
        missing = result.get("missing_fields", [])

        if not has_enough and question:
            # Emit the clarification question via SSE
            emitter.followup_requested(question, missing)
            emitter.step_output("intake_analyzer", {
                "decision": "needs_clarification",
                "missing_fields": missing,
            })
            emitter.step_completed("intake_analyzer")

            return {
                "needs_clarification": True,
                "clarification_question": question,
                "clarification_count": clarification_count + 1,
            }
        else:
            emitter.step_output("intake_analyzer", {"decision": "sufficient_info"})
            emitter.step_completed("intake_analyzer")
            return {"needs_clarification": False}

    except Exception:
        # On failure, proceed with analysis (don't block the user)
        emitter.step_completed("intake_analyzer")
        return {"needs_clarification": False}
