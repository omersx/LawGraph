"""Node 9: Formatter — validates, cleans, and finalizes the output."""

from __future__ import annotations
from langgraph.config import get_stream_writer
from app.models.state import GraphState
from app.graph.event_emitter import EventEmitter


def formatter_node(state: GraphState) -> dict:
    """Finalize the response — validate JSON, clean citations, compute confidence."""
    writer = get_stream_writer()
    emitter = EventEmitter(writer, state.get("run_id", ""), state.get("conversation_id", ""))

    emitter.step_started("formatter")

    output = state.get("output", {})
    aggregation = state.get("aggregation", {})
    legal_sources = aggregation.get("legal_sources", [])

    # ── Validate required fields ──
    output.setdefault("domain", state.get("classification", {}).get("domain", "unknown"))
    output.setdefault("jurisdiction", "United States")
    output.setdefault("issue", "")
    output.setdefault("answer", "")
    output.setdefault("legal_reasoning", "")
    output.setdefault("legal_basis", [])
    output.setdefault("citations", [])

    # ── Recompute confidence if needed ──
    confidence = output.get("confidence", 0.0)
    if not confidence or confidence == 0.0:
        num_sources = len(legal_sources)
        has_reasoning = bool(output.get("legal_reasoning"))
        has_citations = len(output.get("citations", [])) > 0

        if num_sources >= 3 and has_reasoning and has_citations:
            confidence = 0.85
        elif num_sources >= 1 and has_reasoning:
            confidence = 0.7
        elif has_reasoning:
            confidence = 0.5
        else:
            confidence = 0.3

    output["confidence"] = round(confidence, 2)

    # ── Clean citations ──
    clean_citations = []
    for cit in output.get("citations", []):
        # Handle dict or string citations
        if isinstance(cit, dict):
            clean_cit = {
                "type": cit.get("type", "statute"),
                "title": cit.get("title", "Unknown"),
                "citation": cit.get("citation", ""),
                "source": cit.get("source", ""),
                "source_url": cit.get("source_url", ""),
            }
            # Search original legal sources for enrichment data
            for src in legal_sources:
                if src.get("citation") == clean_cit["citation"] or src.get("title") == clean_cit["title"]:
                    if src.get("holding"):
                        clean_cit["holding"] = src["holding"]
                    if src.get("principle"):
                        clean_cit["principle"] = src["principle"]
                    break
                    
            invalid_titles = {"unknown", "untitled", "n/a", "none"}
            if clean_cit["title"] and str(clean_cit["title"]).strip().lower() not in invalid_titles:
                # Also ensure the citation has either a title or a citation string
                if clean_cit["title"] or clean_cit["citation"]:
                    clean_citations.append(clean_cit)

    output["citations"] = clean_citations[:5]  # Max 5 citations

    # ── Build case memory update ──
    case_memory = {
        "domain": output.get("domain", ""),
        "issue": output.get("issue", ""),
        "facts": [],
    }

    # Extract simple facts from the issue
    issue = output.get("issue", "")
    if issue:
        case_memory["facts"].append(issue)

    emitter.step_completed("formatter")

    return {
        "output": output,
        "case_memory": case_memory,
        "meta": {
            **state.get("meta", {}),
            "status": "completed",
        },
    }
