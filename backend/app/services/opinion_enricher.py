"""Service to fetch full case opinions and extract key legal holdings."""

from __future__ import annotations
import asyncio
import json
import logging
from app.models.state import RetrievalItem
from app.services.mcp_client import call_mcp_tool
from app.services.llm import get_flash_model, extract_text_content

logger = logging.getLogger(__name__)

ENRICH_PROMPT = """You are an expert Legal Analyst.
Your task is to read the following full text of a court opinion and extract the core legal principles.

Given the user's legal issue: "{user_query}"

Extract the following from the opinion text:
1. holding: The core legal conclusion or rule established by this case (1-2 clear sentences).
2. principle: The broader legal principle that applies to similar future cases (1 sentence).
3. relevance: A brief note on how this directly impacts the user's specific issue (1 sentence).

OUTPUT FORMAT (STRICT JSON ONLY):
{{
  "holding": "...",
  "principle": "...",
  "relevance": "..."
}}

STRICT RULES:
- If the text is empty or not an opinion, return empty strings for all fields.
- Do NOT hallucinate holdings that aren't in the text.
- Do NOT output anything outside the JSON.
"""

async def _enrich_single_case(item: RetrievalItem, user_query: str) -> RetrievalItem:
    """Fetch case details and extract holding via LLM."""
    if item.get("type") != "case":
        return item
        
    citation = item.get("citation", "")
    if not citation:
        return item

    try:
        # 1. Fetch full case details via CourtListener MCP
        # CourtListener get_case_details expects 'query' to be the case citation or ID
        # Since citation might be a list, we just pass the citation string.
        # Wait, the MCP tool for CourtListener get_case_details expects what?
        # Typically it searches by citation. Let's pass citation as query.
        results = await call_mcp_tool("get_case_details", {"query": citation})
        if not results:
            return item
            
        case_details = results[0]
        
        # Look for full text or opinion fields
        opinion_text = ""
        for field in ["opinion_text", "full_text", "text", "snippet", "summary"]:
            if field in case_details and case_details[field]:
                opinion_text = case_details[field]
                break
                
        if not opinion_text or len(opinion_text) < 200:
            return item  # Not enough text to extract meaningful holding
            
        # Truncate text to stay within LLM context limits (approx 8000 chars)
        opinion_text = opinion_text[:8000]

        # 2. Call LLM to extract holding
        prompt = ENRICH_PROMPT.format(user_query=user_query) + f"\n\n--- OPINION TEXT ---\n{opinion_text}"
        model = get_flash_model(temperature=0.1)
        response = await model.ainvoke(prompt)
        content = extract_text_content(response).strip()
        
        # Parse JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        extracted = json.loads(content)
        
        # 3. Merge into RetrievalItem
        if extracted.get("holding"):
            item["holding"] = extracted["holding"]
            item["principle"] = extracted.get("principle", "")
            item["relevance"] = extracted.get("relevance", "")
            item["opinion_enriched"] = True
            
    except Exception as e:
        logger.error(f"Failed to enrich case opinion '{citation}': {e}")
        
    return item

async def enrich_cases(cases: list[RetrievalItem], user_query: str, max_cases: int = 2) -> list[RetrievalItem]:
    """
    Take a list of ranked cases and enrich the top N with full opinion analysis.
    Returns the updated list.
    """
    to_enrich = []
    others = []
    
    for case in cases:
        if case.get("type") == "case" and len(to_enrich) < max_cases:
            to_enrich.append(case)
        else:
            others.append(case)
            
    if not to_enrich:
        return cases
        
    # Run enrichment in parallel with a hard timeout of 15s
    async def enrich_with_timeout(item):
        try:
            return await asyncio.wait_for(_enrich_single_case(item, user_query), timeout=15.0)
        except asyncio.TimeoutError:
            logger.warning(f"Opinion enrichment timed out for case: {item.get('title')}")
            return item
            
    enriched_results = await asyncio.gather(*[enrich_with_timeout(c) for c in to_enrich])
    
    # Recombine
    return list(enriched_results) + others
