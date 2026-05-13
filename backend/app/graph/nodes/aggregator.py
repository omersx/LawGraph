"""Node 7: Aggregator — deduplicates, ranks, filters, and compresses tool results."""

from __future__ import annotations
import re
from langgraph.config import get_stream_writer
from app.models.state import GraphState, RetrievalItem
from app.graph.event_emitter import EventEmitter
from app.services.opinion_enricher import enrich_cases


def _keyword_overlap(text: str, query: str) -> float:
    """Compute keyword overlap ratio between text and query."""
    if not text or not query:
        return 0.0
    text_words = set(re.findall(r"\w+", text.lower()))
    query_words = set(re.findall(r"\w+", query.lower()))
    if not query_words:
        return 0.0
    overlap = len(text_words & query_words)
    return overlap / len(query_words)


def _domain_match(item: dict, domain: str) -> float:
    """Check if item is relevant to the detected domain."""
    if not domain:
        return 0.5
    domain_keywords = {
        "contract_law": ["contract", "breach", "agreement", "obligation", "delivery", "payment", "performance"],
        "commercial_law": ["commercial", "trade", "ucc", "merchant", "goods", "sale"],
        "tort_law": ["negligence", "tort", "damages", "liability", "injury", "duty"],
        "employment_law": ["employment", "employee", "employer", "termination", "wage", "labor"],
    }
    keywords = domain_keywords.get(domain, [])
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    matches = sum(1 for kw in keywords if kw in text)
    return min(1.0, matches / max(len(keywords), 1))


def _score_item(item: dict, query: str, domain: str) -> float:
    """Compute relevance score for a retrieval item."""
    text = f"{item.get('title', '')} {item.get('summary', '')}"
    keyword = _keyword_overlap(text, query)
    domain_score = _domain_match(item, domain)
    # Weighted score: 60% keyword, 40% domain
    return 0.6 * keyword + 0.4 * domain_score


def _deduplicate(items: list[dict]) -> list[dict]:
    """Remove duplicate items based on citation or title."""
    seen = set()
    unique = []
    for item in items:
        key = item.get("citation", "") or item.get("title", "")
        # Handle cases where citation is a list (e.g., CourtListener API)
        if isinstance(key, list):
            key = key[0] if key else ""
        
        # Ensure key is a string
        key = str(key).strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
        elif not key:
            unique.append(item)
    return unique


async def aggregator_node(state: GraphState) -> dict:
    """Aggregate, deduplicate, rank, filter, and enrich retrieval results."""
    writer = get_stream_writer()
    emitter = EventEmitter(writer, state.get("run_id", ""), state.get("conversation_id", ""))

    emitter.step_started("aggregator")

    retrieval = state.get("retrieval", {})
    query = state.get("resolved_input", state.get("user_input", ""))
    domain = state.get("classification", {}).get("domain", "")

    # Step 1: Flatten all results
    all_items = []
    statute_count = 0
    case_count = 0

    for tool_name, results in retrieval.items():
        for item in results:
            # Drop MCP error messages disguised as results
            if not item.get("title") and "API Error" in str(item.get("summary", "")):
                continue
                
            all_items.append(item)
            if item.get("type") == "statute":
                statute_count += 1
            else:
                case_count += 1

    # Step 2: Deduplicate
    unique_items = _deduplicate(all_items)

    # Step 3: Score and rank
    scored = []
    for item in unique_items:
        score = _score_item(item, query, domain)
        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)

    # Step 4: Filter — max 5 total (3 statutes + 2 cases)
    top_statutes = []
    top_cases = []
    for score, item in scored:
        if item.get("type") == "statute" and len(top_statutes) < 3:
            top_statutes.append(item)
        elif item.get("type") != "statute" and len(top_cases) < 3:
            top_cases.append(item)
        if len(top_statutes) + len(top_cases) >= 5:
            break

    legal_sources = top_statutes + top_cases

    # Step 5: Compress summaries (truncate long ones)
    for item in legal_sources:
        summary = item.get("summary", "")
        if len(summary) > 200:
            item["summary"] = summary[:197] + "..."

    # Step 6: Build retrieval summary
    parts = []
    if top_statutes:
        parts.append(f"{len(top_statutes)} relevant statute(s)")
    if top_cases:
        parts.append(f"{len(top_cases)} relevant case(s)")
    retrieval_summary = " and ".join(parts) + " found." if parts else "No relevant sources found."

    total = len(legal_sources)
    emitter.sources_aggregated(len(top_statutes), len(top_cases), total)
    
    # Step 7: Enrich the top cases with full opinion text analysis
    if top_cases:
        emitter.step_output("aggregator", {"enriching": True, "case_count": len(top_cases)})
        legal_sources = await enrich_cases(legal_sources, query, max_cases=2)
        
    emitter.step_completed("aggregator")

    return {
        "aggregation": {
            "legal_sources": legal_sources,
            "retrieval_summary": retrieval_summary,
        }
    }
