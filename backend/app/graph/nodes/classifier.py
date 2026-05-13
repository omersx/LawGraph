"""Node 4: Classifier — detects legal domain and intent."""

from __future__ import annotations
import json
from langgraph.config import get_stream_writer
from app.models.state import GraphState
from app.graph.event_emitter import EventEmitter
from app.services.llm import get_flash_model, extract_text_content


CLASSIFIER_PROMPT = """You are a Legal Intent and Domain Classifier.

Your task is to analyze a user's input and determine:
1. The legal domain
2. The intent of the request
3. Whether external legal data is needed (statutes, case law)

OUTPUT FORMAT (STRICT JSON ONLY):
{
  "domain": "...",
  "intent": "...",
  "needs_statutes": true/false,
  "needs_cases": true/false
}

FIELD DEFINITIONS:

domain — Choose ONE:
- contract_law
- commercial_law
- tort_law
- employment_law
- unknown

intent — Choose ONE:
- legal_analysis (user wants dispute analysis or legal reasoning)
- legal_information (user asks general legal question)
- case_lookup (user asks for similar cases)
- statute_lookup (user asks for laws/regulations)
- company_lookup (user asks about a company)
- unknown

needs_statutes — true if legal rules or laws are needed to answer.
needs_cases — true if precedents or similar cases would improve the answer.

CLASSIFICATION RULES:
- If input describes a dispute → intent = legal_analysis
- If input asks "what does law say" → statute_lookup
- If input asks for examples → case_lookup
- If unclear → choose best approximation

STRICT RULES:
- Do NOT explain your reasoning
- Do NOT output text outside JSON
- Do NOT return multiple domains
- Always return valid JSON

OUTPUT ONLY JSON."""


async def classifier_node(state: GraphState) -> dict:
    """Classify the legal domain and intent of the user's input."""
    writer = get_stream_writer()
    emitter = EventEmitter(writer, state.get("run_id", ""), state.get("conversation_id", ""))

    emitter.step_started("classifier")

    resolved_input = state.get("resolved_input", state.get("user_input", ""))

    prompt = f"""{CLASSIFIER_PROMPT}

User message:
{resolved_input}"""

    try:
        model = get_flash_model(temperature=0.0)
        response = await model.ainvoke(prompt)
        content = extract_text_content(response).strip()

        # Parse JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        result = json.loads(content)

        classification = {
            "domain": result.get("domain", "unknown"),
            "intent": result.get("intent", "legal_analysis"),
            "needs_statutes": result.get("needs_statutes", True),
            "needs_cases": result.get("needs_cases", True),
        }

        emitter.step_output("classifier", {
            "domain": classification["domain"],
            "intent": classification["intent"],
        })
        emitter.step_completed("classifier")

        return {"classification": classification}

    except Exception as e:
        # Default: assume legal analysis with both tools needed
        emitter.step_completed("classifier")
        return {
            "classification": {
                "domain": "contract_law",
                "intent": "legal_analysis",
                "needs_statutes": True,
                "needs_cases": True,
            }
        }
