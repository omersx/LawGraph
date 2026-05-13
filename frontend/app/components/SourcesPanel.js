"use client";
import { useState } from "react";

export default function SourcesPanel({ citations }) {
  const [expanded, setExpanded] = useState(false);

  if (!citations || citations.length === 0) return null;

  return (
    <div className="sources-panel">
      <button className="sources-toggle" onClick={() => setExpanded(!expanded)}>
        <span>{expanded ? "▾" : "▸"}</span>
        <span>Sources used</span>
        <span className="sources-count">{citations.length}</span>
      </button>

      {expanded && (
        <div className="sources-list animate-in">
          {citations.map((cit, i) => (
            <div key={i} className="source-item">
              <span className={`source-type-badge ${cit.type || "statute"}`}>
                {cit.type || "source"}
              </span>
              <div className="source-info">
                <div className="source-title">{cit.title || "Untitled"}</div>
                {cit.citation && (
                  <div className="source-citation">{cit.citation}</div>
                )}
                
                {/* Extracted Holding & Principle */}
                {(cit.holding || cit.principle) && (
                  <div className="citation-extraction">
                    {cit.holding && (
                      <div className="citation-holding">
                        <span className="citation-holding-label">Holding</span>
                        <p>{cit.holding}</p>
                      </div>
                    )}
                    {cit.principle && (
                      <div className="citation-principle">
                        <span>⚖️ {cit.principle}</span>
                      </div>
                    )}
                  </div>
                )}

                {cit.source_url && (
                  <a
                    href={cit.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="source-link"
                  >
                    View source ↗
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
