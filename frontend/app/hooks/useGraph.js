"use client";
import { useCallback, useState, useEffect, useRef } from "react";
import { fetchGraph } from "../lib/api";

/**
 * Custom hook for managing knowledge graph state.
 *
 * Handles fetching, filtering, and node selection for the graph view.
 */
export function useGraph(conversationId) {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    Party: true,
    Statute: true,
    Case: true,
    LegalConcept: true,
    Jurisdiction: true,
    Court: true,
    LegalDomain: true,
    LegalOutcome: true,
    Evidence: true,
  });

  // Track the last fetched ID to prevent stale updates
  const lastFetchId = useRef(null);

  const loadGraph = useCallback(async (convoId) => {
    if (!convoId) {
      setGraphData({ nodes: [], links: [] });
      return;
    }

    setLoading(true);
    setError(null);
    lastFetchId.current = convoId;

    try {
      const data = await fetchGraph(convoId);
      // Only update if this is still the latest fetch
      if (lastFetchId.current === convoId) {
        setGraphData({
          nodes: data.nodes || [],
          links: data.links || [],
        });
      }
    } catch (err) {
      if (lastFetchId.current === convoId) {
        setError("Failed to load graph data");
        console.error("Graph fetch error:", err);
      }
    } finally {
      if (lastFetchId.current === convoId) {
        setLoading(false);
      }
    }
  }, []);

  // Reload when conversation changes
  useEffect(() => {
    loadGraph(conversationId);
  }, [conversationId, loadGraph]);

  // Filtered graph data based on entity type toggles
  const filteredData = (() => {
    const visibleNodes = graphData.nodes.filter(
      (node) => filters[node.type] !== false
    );
    const visibleNodeIds = new Set(visibleNodes.map((n) => n.id));
    const visibleLinks = graphData.links.filter(
      (link) => {
        const sourceId = typeof link.source === "object" ? link.source.id : link.source;
        const targetId = typeof link.target === "object" ? link.target.id : link.target;
        return visibleNodeIds.has(sourceId) && visibleNodeIds.has(targetId);
      }
    );
    return { nodes: visibleNodes, links: visibleLinks };
  })();

  const toggleFilter = useCallback((entityType) => {
    setFilters((prev) => ({ ...prev, [entityType]: !prev[entityType] }));
  }, []);

  const selectNode = useCallback((node) => {
    setSelectedNode(node);
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const refresh = useCallback(() => {
    loadGraph(conversationId);
  }, [conversationId, loadGraph]);

  return {
    graphData: filteredData,
    rawGraphData: graphData,
    selectedNode,
    loading,
    error,
    filters,
    toggleFilter,
    selectNode,
    clearSelection,
    refresh,
    hasData: graphData.nodes.length > 0,
  };
}
