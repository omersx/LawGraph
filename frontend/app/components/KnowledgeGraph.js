"use client";
import { useRef, useCallback, useState, useEffect, useMemo } from "react";
import dynamic from "next/dynamic";

// Dynamically import react-force-graph-2d with SSR disabled (uses Canvas APIs)
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
  loading: () => (
    <div className="graph-loading">
      <div className="graph-loading-spinner" />
      <span>Initializing graph engine...</span>
    </div>
  ),
});

// ── Entity type configuration ──
const ENTITY_CONFIG = {
  Party:        { color: "#3b82f6", icon: "👤", label: "Parties" },
  Statute:      { color: "#a855f7", icon: "📜", label: "Statutes" },
  Case:         { color: "#f59e0b", icon: "⚖️", label: "Cases" },
  LegalConcept: { color: "#06b6d4", icon: "💡", label: "Concepts" },
  Jurisdiction:  { color: "#22c55e", icon: "🌍", label: "Jurisdictions" },
  Court:        { color: "#f43f5e", icon: "🏛️", label: "Courts" },
  LegalDomain:  { color: "#8b5cf6", icon: "📂", label: "Domains" },
  LegalOutcome: { color: "#10b981", icon: "✅", label: "Outcomes" },
  Evidence:     { color: "#ef4444", icon: "📄", label: "Evidence" },
};

const LINK_COLORS = {
  ALLEGES: "#f59e0b",
  GOVERNED_BY: "#a855f7",
  CITED_IN: "#3b82f6",
  VIOLATED: "#ef4444",
  APPLIES_TO: "#06b6d4",
  DECIDED_BY: "#f43f5e",
  SUPPORTS: "#22c55e",
  CONTRADICTS: "#ef4444",
  PART_OF: "#8b5cf6",
  HAS_JURISDICTION: "#22c55e",
  FILED_AGAINST: "#f59e0b",
  REPRESENTS: "#3b82f6",
  RELATED_TO: "#64748b",
  ESTABLISHES: "#10b981",
  DEFINES: "#06b6d4",
};

export default function KnowledgeGraph({
  graphData,
  selectedNode,
  onNodeSelect,
  onBackgroundClick,
  filters,
  onToggleFilter,
  loading,
  error,
  hasData,
  onRefresh,
}) {
  const graphRef = useRef(null);
  const containerRef = useRef(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [searchQuery, setSearchQuery] = useState("");
  const [isPaused, setIsPaused] = useState(false);

  // Track container dimensions
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const updateDimensions = () => {
      const rect = container.getBoundingClientRect();
      setDimensions({ width: rect.width, height: rect.height });
    };

    updateDimensions();
    const observer = new ResizeObserver(updateDimensions);
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  // Compute node sizes based on connections
  const nodeConnections = useMemo(() => {
    const counts = {};
    (graphData.links || []).forEach((link) => {
      const sourceId = typeof link.source === "object" ? link.source.id : link.source;
      const targetId = typeof link.target === "object" ? link.target.id : link.target;
      counts[sourceId] = (counts[sourceId] || 0) + 1;
      counts[targetId] = (counts[targetId] || 0) + 1;
    });
    return counts;
  }, [graphData.links]);

  // Search/highlight
  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) return new Set();
    const q = searchQuery.toLowerCase();
    return new Set(
      (graphData.nodes || [])
        .filter(
          (n) =>
            n.label?.toLowerCase().includes(q) ||
            n.type?.toLowerCase().includes(q)
        )
        .map((n) => n.id)
    );
  }, [searchQuery, graphData.nodes]);

  // Node painting callback
  const paintNode = useCallback(
    (node, ctx, globalScale) => {
      // Guard: skip rendering if position is not yet computed by the simulation
      if (!Number.isFinite(node.x) || !Number.isFinite(node.y)) return;

      const config = ENTITY_CONFIG[node.type] || { color: "#64748b" };
      const connections = nodeConnections[node.id] || 0;
      const baseSize = 6 + Math.min(connections * 2, 10);
      const isSelected = selectedNode?.id === node.id;
      const isHovered = hoveredNode === node.id;
      const isSearchMatch = searchResults.has(node.id);
      const hasDimming = hoveredNode && hoveredNode !== node.id;

      // Determine opacity
      let alpha = 1;
      if (hasDimming) {
        // Check if connected to hovered node
        const isConnected = (graphData.links || []).some((link) => {
          const sourceId = typeof link.source === "object" ? link.source.id : link.source;
          const targetId = typeof link.target === "object" ? link.target.id : link.target;
          return (
            (sourceId === hoveredNode && targetId === node.id) ||
            (targetId === hoveredNode && sourceId === node.id)
          );
        });
        alpha = isConnected ? 1 : 0.15;
      }

      ctx.globalAlpha = alpha;

      // Glow effect for selected/hovered/search-matched
      if (isSelected || isHovered || isSearchMatch) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, baseSize + 6, 0, 2 * Math.PI);
        ctx.fillStyle = isSearchMatch
          ? "rgba(250, 204, 21, 0.25)"
          : `${config.color}30`;
        ctx.fill();

        // Outer glow ring
        ctx.beginPath();
        ctx.arc(node.x, node.y, baseSize + 10, 0, 2 * Math.PI);
        ctx.strokeStyle = isSearchMatch
          ? "rgba(250, 204, 21, 0.15)"
          : `${config.color}15`;
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Node body — gradient fill
      ctx.beginPath();
      ctx.arc(node.x, node.y, baseSize, 0, 2 * Math.PI);
      const gradient = ctx.createRadialGradient(
        node.x - baseSize * 0.3,
        node.y - baseSize * 0.3,
        0,
        node.x,
        node.y,
        baseSize
      );
      gradient.addColorStop(0, config.color + "ff");
      gradient.addColorStop(1, config.color + "aa");
      ctx.fillStyle = gradient;
      ctx.fill();

      // Border
      ctx.strokeStyle = isSelected
        ? "#ffffff"
        : isHovered
        ? config.color
        : `${config.color}80`;
      ctx.lineWidth = isSelected ? 2.5 : isHovered ? 2 : 1;
      ctx.stroke();

      // Label
      const fontSize = Math.max(10 / globalScale, 3);
      ctx.font = `${isSelected || isHovered ? "600" : "500"} ${fontSize}px Inter, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillStyle = alpha < 1 ? `rgba(241, 245, 249, ${alpha})` : "#f1f5f9";
      ctx.fillText(
        node.label?.length > 25 ? node.label.slice(0, 22) + "..." : node.label || "",
        node.x,
        node.y + baseSize + 3
      );

      ctx.globalAlpha = 1;
    },
    [hoveredNode, selectedNode, nodeConnections, searchResults, graphData.links]
  );

  // Link painting callback
  const paintLink = useCallback(
    (link, ctx, globalScale) => {
      // Guard: skip if source/target positions aren't ready
      const source = link.source;
      const target = link.target;
      if (!source || !target) return;
      if (!Number.isFinite(source.x) || !Number.isFinite(target.x)) return;
      const sourceId = typeof link.source === "object" ? link.source.id : link.source;
      const targetId = typeof link.target === "object" ? link.target.id : link.target;
      const isConnectedToHover =
        hoveredNode && (sourceId === hoveredNode || targetId === hoveredNode);
      const isConnectedToSelected =
        selectedNode &&
        (sourceId === selectedNode.id || targetId === selectedNode.id);

      const alpha =
        hoveredNode && !isConnectedToHover
          ? 0.05
          : isConnectedToHover || isConnectedToSelected
          ? 0.9
          : 0.35;

      const color = LINK_COLORS[link.label] || "#64748b";

      ctx.globalAlpha = alpha;
      ctx.strokeStyle = color;
      ctx.lineWidth = isConnectedToHover || isConnectedToSelected ? 2 : 1;

      // Draw line
      ctx.beginPath();
      ctx.moveTo(source.x, source.y);
      ctx.lineTo(target.x, target.y);
      ctx.stroke();

      // Arrow
      const angle = Math.atan2(target.y - source.y, target.x - source.x);
      const arrowLen = 5;
      const midX = (source.x + target.x) / 2;
      const midY = (source.y + target.y) / 2;
      ctx.beginPath();
      ctx.moveTo(midX, midY);
      ctx.lineTo(
        midX - arrowLen * Math.cos(angle - Math.PI / 6),
        midY - arrowLen * Math.sin(angle - Math.PI / 6)
      );
      ctx.lineTo(
        midX - arrowLen * Math.cos(angle + Math.PI / 6),
        midY - arrowLen * Math.sin(angle + Math.PI / 6)
      );
      ctx.closePath();
      ctx.fillStyle = color;
      ctx.fill();

      // Label on hover
      if (isConnectedToHover || isConnectedToSelected) {
        const fontSize = Math.max(9 / globalScale, 2.5);
        ctx.font = `500 ${fontSize}px Inter, sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillStyle = `rgba(148, 163, 184, ${alpha})`;
        ctx.fillText(link.label || "", midX, midY - 6);
      }

      ctx.globalAlpha = 1;
    },
    [hoveredNode, selectedNode]
  );

  const handleNodeClick = useCallback(
    (node) => {
      if (onNodeSelect) onNodeSelect(node);
      // Zoom to node
      if (graphRef.current) {
        graphRef.current.centerAt(node.x, node.y, 500);
        graphRef.current.zoom(3, 500);
      }
    },
    [onNodeSelect]
  );

  const handleFitView = useCallback(() => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400, 60);
    }
  }, []);

  const handleTogglePause = useCallback(() => {
    if (graphRef.current) {
      if (isPaused) {
        graphRef.current.resumeAnimation();
      } else {
        graphRef.current.pauseAnimation();
      }
      setIsPaused((p) => !p);
    }
  }, [isPaused]);

  // Fit view when data loads
  useEffect(() => {
    if (graphData.nodes?.length > 0 && graphRef.current) {
      setTimeout(() => {
        graphRef.current?.zoomToFit(400, 60);
      }, 300);
    }
  }, [graphData.nodes?.length]);

  // ── Render ──

  if (loading) {
    return (
      <div className="graph-empty-state">
        <div className="graph-loading-spinner" />
        <h3>Loading Knowledge Graph...</h3>
        <p>Fetching entity data for this conversation</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="graph-empty-state">
        <div className="graph-empty-icon">⚠️</div>
        <h3>Failed to Load Graph</h3>
        <p>{error}</p>
        <button className="graph-retry-btn" onClick={onRefresh}>
          Retry
        </button>
      </div>
    );
  }

  if (!hasData) {
    return (
      <div className="graph-empty-state">
        <div className="graph-empty-icon">🔗</div>
        <h3>No Knowledge Graph Yet</h3>
        <p>
          Submit a legal query in the Chat view. After the analysis completes,
          the system will automatically extract entities and relationships into
          an interactive knowledge graph.
        </p>
        <div className="graph-empty-hint">
          <span>💡</span>
          <span>
            Try asking about a contract dispute, employment issue, or tort claim
          </span>
        </div>
      </div>
    );
  }

  // Count entity types for filter badges
  const typeCounts = {};
  (graphData.nodes || []).forEach((n) => {
    typeCounts[n.type] = (typeCounts[n.type] || 0) + 1;
  });

  return (
    <div className="graph-container">
      {/* ── Controls Bar ── */}
      <div className="graph-controls">
        <div className="graph-search">
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            placeholder="Search entities..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="graph-search-input"
          />
          {searchQuery && (
            <button
              className="graph-search-clear"
              onClick={() => setSearchQuery("")}
            >
              ✕
            </button>
          )}
        </div>

        <div className="graph-controls-right">
          <button
            className="graph-control-btn"
            onClick={handleFitView}
            title="Fit to view"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
            </svg>
          </button>
          <button
            className={`graph-control-btn ${isPaused ? "active" : ""}`}
            onClick={handleTogglePause}
            title={isPaused ? "Resume physics" : "Pause physics"}
          >
            {isPaused ? "▶" : "⏸"}
          </button>
          <button
            className="graph-control-btn"
            onClick={onRefresh}
            title="Refresh graph"
          >
            ↻
          </button>
        </div>
      </div>

      {/* ── Entity Filters ── */}
      <div className="graph-filters">
        {Object.entries(ENTITY_CONFIG).map(([type, config]) => {
          const count = typeCounts[type] || 0;
          if (count === 0) return null;
          return (
            <button
              key={type}
              className={`graph-filter-chip ${
                filters[type] !== false ? "active" : "inactive"
              }`}
              onClick={() => onToggleFilter(type)}
              style={{
                "--chip-color": config.color,
              }}
            >
              <span className="graph-filter-dot" />
              <span>{config.label}</span>
              <span className="graph-filter-count">{count}</span>
            </button>
          );
        })}
      </div>

      {/* ── Graph Stats ── */}
      <div className="graph-stats">
        <span>{graphData.nodes?.length || 0} entities</span>
        <span className="graph-stats-dot">·</span>
        <span>{graphData.links?.length || 0} relationships</span>
        {searchQuery && searchResults.size > 0 && (
          <>
            <span className="graph-stats-dot">·</span>
            <span className="graph-stats-highlight">
              {searchResults.size} matches
            </span>
          </>
        )}
      </div>

      {/* ── Force Graph ── */}
      <div className="graph-canvas" ref={containerRef}>
        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          width={dimensions.width}
          height={dimensions.height}
          nodeCanvasObject={paintNode}
          linkCanvasObject={paintLink}
          onNodeClick={handleNodeClick}
          onNodeHover={(node) => setHoveredNode(node?.id || null)}
          onBackgroundClick={onBackgroundClick}
          nodeRelSize={6}
          linkDirectionalParticles={2}
          linkDirectionalParticleWidth={1.5}
          linkDirectionalParticleSpeed={0.004}
          linkDirectionalParticleColor={(link) =>
            LINK_COLORS[link.label] || "#64748b"
          }
          cooldownTicks={100}
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.3}
          backgroundColor="transparent"
          enableZoomInteraction={true}
          enablePanInteraction={true}
        />
      </div>
    </div>
  );
}
