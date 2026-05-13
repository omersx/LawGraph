"""Node 10: Graph Extractor — extracts knowledge graph entities from the final legal output."""

from __future__ import annotations
import logging
from langgraph.config import get_stream_writer
from app.models.state import GraphState
from app.graph.event_emitter import EventEmitter
from app.services.graph_extractor import extract_graph_from_output
from app.services.graph_store import graph_store

logger = logging.getLogger(__name__)


async def graph_extractor_node(state: GraphState) -> dict:
    """
    Extract knowledge graph entities and relationships from the final output.
    
    Runs AFTER the formatter node. Does not modify the output — only reads it
    and stores the extracted graph data in the graph_store.
    """
    writer = get_stream_writer()
    emitter = EventEmitter(writer, state.get("run_id", ""), state.get("conversation_id", ""))

    emitter.step_started("graph_extractor")

    output = state.get("output", {})
    conversation_id = state.get("conversation_id", "")

    if not output or not output.get("issue"):
        # No meaningful output to extract from
        emitter.step_completed("graph_extractor")
        return {}

    try:
        graph_data = await extract_graph_from_output(output)

        if graph_data and graph_data.get("nodes"):
            # Store in the graph store
            graph_store.add_graph_data(conversation_id, graph_data)

            # Emit SSE event so frontend knows graph data is ready
            writer({
                "event": "graph_ready",
                "run_id": state.get("run_id", ""),
                "conversation_id": conversation_id,
                "payload": {
                    "node_count": len(graph_data.get("nodes", [])),
                    "link_count": len(graph_data.get("links", [])),
                },
            })

            logger.info(
                f"Graph extracted for {conversation_id}: "
                f"{len(graph_data['nodes'])} nodes, {len(graph_data['links'])} links"
            )
        else:
            logger.warning(f"No graph data extracted for {conversation_id}")

    except Exception as e:
        logger.error(f"Graph extraction node error: {e}")
        # Non-fatal — don't break the pipeline

    emitter.step_completed("graph_extractor")
    return {}
