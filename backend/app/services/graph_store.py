"""In-memory graph store for legal knowledge graphs, keyed by conversation_id."""

from __future__ import annotations
import logging
from typing import Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class GraphStore:
    """
    In-memory store for conversation knowledge graphs.
    
    Each conversation has its own graph (nodes + links).
    Supports merging across multi-turn conversations (deduplication by node ID).
    
    In production, replace with Neo4j for persistence and advanced graph queries.
    """

    def __init__(self):
        self._graphs: dict[str, dict] = {}

    def add_graph_data(self, conversation_id: str, graph_data: dict) -> None:
        """
        Add or merge graph data for a conversation.
        
        If the conversation already has graph data, new nodes are merged
        (deduplicated by ID) and new links are appended.
        """
        if not graph_data:
            return

        new_nodes = graph_data.get("nodes", [])
        new_links = graph_data.get("links", [])

        if conversation_id not in self._graphs:
            self._graphs[conversation_id] = {
                "conversation_id": conversation_id,
                "nodes": [],
                "links": [],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

        existing = self._graphs[conversation_id]
        existing_node_ids = {n["id"] for n in existing["nodes"]}

        # Merge nodes (deduplicate by ID, update properties if exists)
        for node in new_nodes:
            node_id = node.get("id")
            if not node_id:
                continue
            if node_id in existing_node_ids:
                # Update existing node properties
                for i, existing_node in enumerate(existing["nodes"]):
                    if existing_node["id"] == node_id:
                        # Merge properties
                        existing_props = existing_node.get("properties", {})
                        new_props = node.get("properties", {})
                        existing_node["properties"] = {**existing_props, **new_props}
                        break
            else:
                existing["nodes"].append(node)
                existing_node_ids.add(node_id)

        # Merge links (deduplicate by source+target+label)
        existing_link_keys = {
            (l["source"], l["target"], l.get("label", ""))
            for l in existing["links"]
        }
        for link in new_links:
            key = (link.get("source"), link.get("target"), link.get("label", ""))
            if key not in existing_link_keys:
                # Validate that source and target exist
                if link.get("source") in existing_node_ids and link.get("target") in existing_node_ids:
                    existing["links"].append(link)
                    existing_link_keys.add(key)

        existing["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        logger.info(
            f"Graph for {conversation_id}: "
            f"{len(existing['nodes'])} nodes, {len(existing['links'])} links"
        )

    def get_graph(self, conversation_id: str) -> Optional[dict]:
        """Get the knowledge graph for a specific conversation."""
        graph = self._graphs.get(conversation_id)
        if not graph:
            return {"conversation_id": conversation_id, "nodes": [], "links": []}
        return graph

    def get_all_graphs(self) -> dict:
        """
        Get a merged global graph from all conversations.
        Nodes are deduplicated by ID across conversations.
        """
        all_nodes = {}
        all_links = set()
        link_list = []

        for conv_id, graph in self._graphs.items():
            for node in graph.get("nodes", []):
                node_id = node.get("id")
                if node_id and node_id not in all_nodes:
                    all_nodes[node_id] = {
                        **node,
                        "conversations": [conv_id],
                    }
                elif node_id:
                    # Track which conversations reference this node
                    if conv_id not in all_nodes[node_id].get("conversations", []):
                        all_nodes[node_id]["conversations"].append(conv_id)

            for link in graph.get("links", []):
                key = (link.get("source"), link.get("target"), link.get("label", ""))
                if key not in all_links:
                    all_links.add(key)
                    link_list.append(link)

        return {
            "conversation_id": "global",
            "nodes": list(all_nodes.values()),
            "links": link_list,
        }

    def has_graph(self, conversation_id: str) -> bool:
        """Check if a conversation has any graph data."""
        graph = self._graphs.get(conversation_id)
        return bool(graph and len(graph.get("nodes", [])) > 0)

    def clear_graph(self, conversation_id: str) -> None:
        """Clear graph data for a conversation."""
        if conversation_id in self._graphs:
            del self._graphs[conversation_id]


# Global singleton
graph_store = GraphStore()
