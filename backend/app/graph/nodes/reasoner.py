"""Node 8: Reasoner — applies legal reasoning using IRAC-style structured analysis."""

from __future__ import annotations
import json
import uuid
from langgraph.config import get_stream_writer
from app.models.state import GraphState
from app.graph.event_emitter import EventEmitter
from app.services.llm import get_reasoning_model, call_external_reasoning_model, extract_text_content
from app.config import settings


REASONING_PROMPT = """You are a Legal Reasoning Agent specialized in contract and commercial law disputes.

You operate as part of a controlled system with external tools that provide verified legal data (statutes and case law). Your role is to analyze legal problems, apply structured reasoning, and produce accurate, citation-supported outputs.

PRIMARY OBJECTIVE:
Given:
- a user legal problem (case description)
- optionally retrieved legal sources (statutes, cases)

You must:
1. Identify the legal domain
2. Formulate the legal issue
3. Apply structured legal reasoning (IRAC: Issue → Rule → Application → Conclusion)
4. Provide a clear answer
5. Use retrieved sources to support your reasoning (if available)
6. Output a strict JSON response

OUTPUT FORMAT (STRICT — NO DEVIATION):
{{
  "domain": "...",
  "issue": "...",
  "answer": "...",
  "legal_reasoning": "...",
  "legal_basis": [...],
  "citations": [...],
  "confidence": 0.0,
  "confidence_reason": "..."
}}

FIELD DEFINITIONS:
- domain: One of contract_law, commercial_law, tort_law, employment_law
- issue: A precise legal question starting with "Whether..."
- answer: Clear, direct conclusion
- legal_reasoning: Structured IRAC explanation applying legal principles to facts
- legal_basis: List of legal principles used (strings)
- citations: MUST come ONLY from provided tool data. Each: {{"type": "statute|case", "title": "...", "citation": "...", "source": "...", "source_url": "..."}}
- confidence: 0-1 based on strength of reasoning and sources
- confidence_reason: A brief 1-sentence explanation of why this confidence level was chosen (e.g., "Lack of explicit jurisdictional details limits certainty.")

SOURCE USAGE RULES:
- If legal sources are provided: extract principles, use in reasoning, include in legal_basis and citations
- If a source has a [HOLDING] or [PRINCIPLE] tag, prioritize using that exact legal rule in your analysis.
- If NO sources are provided: use general legal reasoning, set legal_basis=[], citations=[], lower confidence

STRICT RULES:
- Do NOT invent laws or cases
- Do NOT fabricate citations
- Do NOT output text outside JSON
- Ensure JSON is valid
- If sources conflict, prefer more specific/authoritative sources, reflect uncertainty, lower confidence

CONFIDENCE GUIDELINES:
- Strong reasoning + multiple sources → 0.8-0.95
- Moderate reasoning + limited sources → 0.5-0.75
- Weak or no sources → ≤ 0.4

Return ONLY the JSON response."""


async def reasoner_node(state: GraphState) -> dict:
    """Apply legal reasoning to produce structured analysis."""
    writer = get_stream_writer()
    emitter = EventEmitter(writer, state.get("run_id", ""), state.get("conversation_id", ""))

    emitter.step_started("reasoner")

    user_input = state.get("resolved_input", state.get("user_input", ""))
    aggregation = state.get("aggregation", {})
    legal_sources = aggregation.get("legal_sources", [])
    retrieval_summary = aggregation.get("retrieval_summary", "")

    # Build sources context
    sources_text = ""
    if legal_sources:
        sources_parts = []
        for i, src in enumerate(legal_sources, 1):
            part = f"{i}. [{src.get('type', 'unknown')}] {src.get('title', 'N/A')}"
            if src.get("citation"):
                part += f" — {src['citation']}"
            
            if src.get("opinion_enriched") and src.get("holding"):
                part += f"\n   [HOLDING] {src['holding']}"
                if src.get("principle"):
                    part += f"\n   [PRINCIPLE] {src['principle']}"
                if src.get("relevance"):
                    part += f"\n   [RELEVANCE] {src['relevance']}"
            elif src.get("summary"):
                part += f"\n   Summary: {src['summary']}"
                
            if src.get("source_url"):
                part += f"\n   Source: {src['source_url']}"
            sources_parts.append(part)
        sources_text = "\n".join(sources_parts)
    else:
        sources_text = "No external legal sources were retrieved. Use general legal reasoning only."

    full_prompt = f"""{REASONING_PROMPT}

User Case:
{user_input}

Relevant Legal Sources:
{sources_text}

{retrieval_summary}"""

    message_id = emitter.answer_started()

    try:
        # Use external model if configured, otherwise Gemini
        if settings.reasoning_model_url:
            raw_response = await call_external_reasoning_model(full_prompt)
        else:
            model = get_reasoning_model(temperature=0.2)
            response = await model.ainvoke(full_prompt)
            raw_response = extract_text_content(response)

        # Stream the response content as deltas
        chunk_size = 50
        for i in range(0, len(raw_response), chunk_size):
            chunk = raw_response[i : i + chunk_size]
            emitter.answer_delta(message_id, chunk)

        # Parse the JSON output
        content = raw_response.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        output = json.loads(content)

        # Validate citations — ONLY keep those verified from tool data
        valid_citations = []
        tool_urls = {src.get("source_url", "") for src in legal_sources if src.get("source_url")}
        tool_titles = {src.get("title", "").lower() for src in legal_sources if src.get("title")}

        for cit in output.get("citations", []):
            if not isinstance(cit, dict):
                continue
            cit_url = cit.get("source_url", "")
            cit_title = cit.get("title", "").lower()
            if cit_url in tool_urls or cit_title in tool_titles:
                valid_citations.append(cit)

        # If model didn't produce citations but we have valid sources, inject them
        if not valid_citations and legal_sources:
            for src in legal_sources[:5]:
                if src.get("title"):
                    valid_citations.append({
                        "type": src.get("type", "statute"),
                        "title": src.get("title", ""),
                        "citation": src.get("citation", ""),
                        "source": src.get("source", ""),
                        "source_url": src.get("source_url", ""),
                        "holding": src.get("holding", ""),
                        "principle": src.get("principle", ""),
                    })

        output["citations"] = valid_citations
        output["sources_available"] = len(valid_citations) > 0
        output.setdefault("jurisdiction", "United States")

        emitter.answer_completed(message_id, output)
        emitter.step_completed("reasoner")

        return {
            "reasoning": {
                "case_facts": user_input,
                "legal_issue": output.get("issue", ""),
                "reasoning_context": output.get("legal_basis", []),
            },
            "output": output,
        }

    except Exception as e:
        # Fallback output on failure
        fallback = {
            "domain": state.get("classification", {}).get("domain", "unknown"),
            "issue": "Unable to complete legal analysis",
            "answer": f"An error occurred during analysis: {str(e)}",
            "legal_reasoning": "",
            "legal_basis": [],
            "citations": [],
            "confidence": 0.0,
            "confidence_reason": "Analysis failed due to an internal error."
        }
        emitter.answer_completed(message_id, fallback)
        emitter.step_completed("reasoner")
        return {"output": fallback}
