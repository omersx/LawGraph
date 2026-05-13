"""Graph Entity Extractor — Uses LLM to extract entities and relationships from legal analysis."""

from __future__ import annotations
import json
import hashlib
import logging
from typing import Optional

from app.services.llm import get_flash_model, extract_text_content

logger = logging.getLogger(__name__)

# ── Entity Types & Colors (shared with frontend) ──

ENTITY_TYPES = {
    "Party": {"color": "#3b82f6", "icon": "👤"},
    "Statute": {"color": "#a855f7", "icon": "📜"},
    "Case": {"color": "#f59e0b", "icon": "⚖️"},
    "LegalConcept": {"color": "#06b6d4", "icon": "💡"},
    "Jurisdiction": {"color": "#22c55e", "icon": "🌍"},
    "Court": {"color": "#f43f5e", "icon": "🏛️"},
    "LegalDomain": {"color": "#8b5cf6", "icon": "📂"},
    "LegalOutcome": {"color": "#10b981", "icon": "✅"},
    "Evidence": {"color": "#ef4444", "icon": "📄"},
}

RELATIONSHIP_TYPES = [
    "ALLEGES", "GOVERNED_BY", "CITED_IN", "VIOLATED", "APPLIES_TO",
    "DECIDED_BY", "SUPPORTS", "CONTRADICTS", "PART_OF", "HAS_JURISDICTION",
    "FILED_AGAINST", "REPRESENTS", "RELATED_TO", "ESTABLISHES", "DEFINES",
]

# ── Extraction Prompt ──

EXTRACTION_PROMPT = """You are a Legal Knowledge Graph Extractor. Given a legal analysis, extract ALL entities and their relationships into a structured knowledge graph.

ENTITY TYPES (use ONLY these):
- Party: Any person, company, or organization involved (plaintiff, defendant, employer, employee, landlord, tenant, etc.)
- Statute: Any law, regulation, code section, or legislative act referenced
- Case: Any court case or legal precedent cited
- LegalConcept: Legal doctrines, principles, theories (e.g., "breach of contract", "duty of care", "consideration")
- Jurisdiction: Geographic or legal jurisdiction (e.g., "United States", "California", "Federal")
- Court: Any court mentioned (e.g., "Supreme Court", "District Court")
- LegalDomain: Area of law (e.g., "Contract Law", "Employment Law", "Tort Law")
- LegalOutcome: The predicted or actual outcome/remedy (e.g., "Damages Awarded", "Contract Voided")
- Evidence: Key facts or evidence mentioned (e.g., "Written Contract", "Deposit Payment", "Delivery Failure")

RELATIONSHIP TYPES (use ONLY these):
ALLEGES, GOVERNED_BY, CITED_IN, VIOLATED, APPLIES_TO, DECIDED_BY, SUPPORTS, CONTRADICTS, PART_OF, HAS_JURISDICTION, FILED_AGAINST, REPRESENTS, RELATED_TO, ESTABLISHES, DEFINES

RULES:
1. Extract AT LEAST 5 nodes and 5 links (more is better for a rich graph)
2. Every node needs a unique "id" (lowercase, underscored, e.g., "party_supplier", "statute_ucc_2_207")
3. Every node needs a human-readable "label" and a "type" from the list above
4. Links must reference existing node IDs in "source" and "target"
5. Every link needs a "label" from the relationship types above
6. Add a "properties" dict to nodes with any relevant details
7. Return ONLY valid JSON, no markdown, no explanation

OUTPUT FORMAT:
{{
  "nodes": [
    {{ "id": "...", "label": "...", "type": "...", "properties": {{ ... }} }}
  ],
  "links": [
    {{ "source": "...", "target": "...", "label": "..." }}
  ]
}}

LEGAL ANALYSIS TO EXTRACT FROM:
{analysis_text}"""


def _generate_node_id(label: str, node_type: str) -> str:
    """Generate a stable, unique node ID from label and type."""
    raw = f"{node_type}_{label}".lower().strip()
    # Clean and normalize
    clean = raw.replace(" ", "_").replace(".", "_").replace("§", "s")
    clean = "".join(c for c in clean if c.isalnum() or c == "_")
    # Truncate and add hash suffix for uniqueness
    if len(clean) > 40:
        suffix = hashlib.md5(clean.encode()).hexdigest()[:6]
        clean = clean[:34] + "_" + suffix
    return clean


async def extract_graph_from_output(output: dict) -> Optional[dict]:
    """
    Extract entities and relationships from a legal analysis output.
    
    Args:
        output: The OutputState dict from the formatter node
        
    Returns:
        Graph data dict with 'nodes' and 'links', or None on failure
    """
    # Build text representation of the analysis
    parts = []
    
    if output.get("domain"):
        parts.append(f"Legal Domain: {output['domain']}")
    if output.get("jurisdiction"):
        parts.append(f"Jurisdiction: {output['jurisdiction']}")
    if output.get("issue"):
        parts.append(f"Legal Issue: {output['issue']}")
    if output.get("legal_reasoning"):
        parts.append(f"Legal Reasoning: {output['legal_reasoning']}")
    if output.get("answer"):
        parts.append(f"Conclusion: {output['answer']}")
    if output.get("legal_basis"):
        parts.append(f"Legal Basis: {', '.join(output['legal_basis'])}")
    if output.get("citations"):
        citations_text = []
        for cit in output["citations"]:
            if isinstance(cit, dict):
                citations_text.append(f"  - [{cit.get('type', '')}] {cit.get('title', '')} ({cit.get('citation', '')})")
        if citations_text:
            parts.append(f"Citations:\n" + "\n".join(citations_text))
    
    analysis_text = "\n\n".join(parts)
    
    if not analysis_text.strip():
        logger.warning("Empty analysis text, skipping graph extraction")
        return None
    
    prompt = EXTRACTION_PROMPT.format(analysis_text=analysis_text)
    
    try:
        model = get_flash_model(temperature=0.1)
        response = await model.ainvoke(prompt)
        raw = extract_text_content(response)
        
        # Parse JSON
        content = raw.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        graph_data = json.loads(content)
        
        # Validate and clean
        nodes = graph_data.get("nodes", [])
        links = graph_data.get("links", [])
        
        # Validate nodes
        valid_nodes = []
        node_ids = set()
        for node in nodes:
            if not isinstance(node, dict):
                continue
            node_id = node.get("id", "")
            node_type = node.get("type", "")
            label = node.get("label", "")
            
            if not node_id or not label:
                continue
            
            # Ensure valid type
            if node_type not in ENTITY_TYPES:
                node_type = "LegalConcept"  # fallback
            
            node["type"] = node_type
            node.setdefault("properties", {})
            node_ids.add(node_id)
            valid_nodes.append(node)
        
        # Validate links
        valid_links = []
        for link in links:
            if not isinstance(link, dict):
                continue
            source = link.get("source", "")
            target = link.get("target", "")
            if source in node_ids and target in node_ids and source != target:
                link.setdefault("label", "RELATED_TO")
                valid_links.append(link)
        
        if not valid_nodes:
            logger.warning("No valid nodes extracted")
            return None
        
        result = {
            "nodes": valid_nodes,
            "links": valid_links,
        }
        
        logger.info(f"Extracted graph: {len(valid_nodes)} nodes, {len(valid_links)} links")
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse graph extraction JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Graph extraction failed: {e}")
        return None
