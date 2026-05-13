"use client";

// ── Entity type configuration (mirrors KnowledgeGraph.js) ──
const ENTITY_CONFIG = {
  Party:        { color: "#3b82f6", icon: "👤", label: "Party" },
  Statute:      { color: "#a855f7", icon: "📜", label: "Statute" },
  Case:         { color: "#f59e0b", icon: "⚖️", label: "Case" },
  LegalConcept: { color: "#06b6d4", icon: "💡", label: "Legal Concept" },
  Jurisdiction:  { color: "#22c55e", icon: "🌍", label: "Jurisdiction" },
  Court:        { color: "#f43f5e", icon: "🏛️", label: "Court" },
  LegalDomain:  { color: "#8b5cf6", icon: "📂", label: "Legal Domain" },
  LegalOutcome: { color: "#10b981", icon: "✅", label: "Legal Outcome" },
  Evidence:     { color: "#ef4444", icon: "📄", label: "Evidence" },
};

export default function GraphDetailPanel({
  node,
  graphData,
  onClose,
}) {
  if (!node) return null;

  const config = ENTITY_CONFIG[node.type] || { color: "#64748b", icon: "🔹", label: node.type };

  // Find connected nodes
  const connections = [];
  (graphData?.links || []).forEach((link) => {
    const sourceId = typeof link.source === "object" ? link.source.id : link.source;
    const targetId = typeof link.target === "object" ? link.target.id : link.target;

    if (sourceId === node.id) {
      const targetNode = (graphData?.nodes || []).find((n) => n.id === targetId);
      if (targetNode) {
        connections.push({
          direction: "outgoing",
          label: link.label,
          node: targetNode,
        });
      }
    } else if (targetId === node.id) {
      const sourceNode = (graphData?.nodes || []).find((n) => n.id === sourceId);
      if (sourceNode) {
        connections.push({
          direction: "incoming",
          label: link.label,
          node: sourceNode,
        });
      }
    }
  });

  return (
    <div className="graph-detail-panel animate-in">
      {/* Header */}
      <div className="graph-detail-header">
        <div className="graph-detail-title-row">
          <div
            className="graph-detail-icon"
            style={{ background: `${config.color}20`, color: config.color }}
          >
            {config.icon}
          </div>
          <div className="graph-detail-title-info">
            <h3 className="graph-detail-name">{node.label}</h3>
            <span
              className="graph-detail-type-badge"
              style={{
                background: `${config.color}15`,
                color: config.color,
                border: `1px solid ${config.color}30`,
              }}
            >
              {config.label}
            </span>
          </div>
        </div>
        <button className="graph-detail-close" onClick={onClose}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      {/* Properties */}
      {node.properties && Object.keys(node.properties).length > 0 && (
        <div className="graph-detail-section">
          <div className="graph-detail-section-label">Properties</div>
          <div className="graph-detail-properties">
            {Object.entries(node.properties).map(([key, value]) => (
              <div key={key} className="graph-detail-property">
                <span className="graph-detail-property-key">
                  {key.replace(/_/g, " ")}
                </span>
                <span className="graph-detail-property-value">
                  {typeof value === "object" ? JSON.stringify(value) : String(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Connections */}
      {connections.length > 0 && (
        <div className="graph-detail-section">
          <div className="graph-detail-section-label">
            Connections ({connections.length})
          </div>
          <div className="graph-detail-connections">
            {connections.map((conn, i) => {
              const connConfig = ENTITY_CONFIG[conn.node.type] || {
                color: "#64748b",
                icon: "🔹",
              };
              return (
                <div key={i} className="graph-detail-connection">
                  <div className="graph-detail-conn-direction">
                    {conn.direction === "outgoing" ? (
                      <span className="conn-arrow-out">→</span>
                    ) : (
                      <span className="conn-arrow-in">←</span>
                    )}
                  </div>
                  <div className="graph-detail-conn-label">{conn.label}</div>
                  <div className="graph-detail-conn-target">
                    <span
                      className="graph-detail-conn-dot"
                      style={{ background: connConfig.color }}
                    />
                    <span>{conn.node.label}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Node ID (footer) */}
      <div className="graph-detail-footer">
        <span className="graph-detail-id">ID: {node.id}</span>
      </div>
    </div>
  );
}
