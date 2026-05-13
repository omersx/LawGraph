"use client";
import { useState } from "react";
import ConfidenceBadge from "./ConfidenceBadge";
import SourcesPanel from "./SourcesPanel";

export default function LegalAnswer({ output, streamedText }) {
  // If we have a final structured output, render it
  // Otherwise show the streaming text
  const data = output || {};
  const isStreaming = !output && streamedText;

  if (!output && !streamedText) return null;

  return (
    <div className="legal-answer animate-in">
      {/* Domain */}
      {data.domain && (
        <div className="answer-section">
          <div className="answer-section-label">Detected Domain</div>
          <div className="answer-badges-row">
            <span className={`answer-domain ${data.domain}`}>
              {formatDomain(data.domain)}
            </span>
          </div>
        </div>
      )}

      {/* Jurisdiction */}
      {data.jurisdiction && (
        <div className="answer-section">
          <div className="answer-section-label">Jurisdiction</div>
          <div className="answer-badges-row">
            <span className="answer-jurisdiction">
              {data.jurisdiction}
            </span>
          </div>
        </div>
      )}

      {/* Issue */}
      {data.issue && (
        <div className="answer-section">
          <div className="answer-section-label">Legal Issue</div>
          <div className="answer-issue">{data.issue}</div>
        </div>
      )}

      {/* Analysis / Reasoning */}
      {(data.legal_reasoning || isStreaming) && (
        <div className="answer-section">
          <div className="answer-section-label">Analysis</div>
          <div className="answer-reasoning">
            {data.legal_reasoning || streamedText}
            {isStreaming && <span className="animate-pulse">▊</span>}
          </div>
        </div>
      )}

      {/* Answer / Conclusion */}
      {data.answer && (
        <div className="answer-section">
          <div className="answer-section-label">Likely Outcome</div>
          <div className="answer-conclusion">{data.answer}</div>
        </div>
      )}

      {/* Legal Basis */}
      {data.legal_basis && data.legal_basis.length > 0 && (
        <div className="answer-section">
          <div className="answer-section-label">Legal Basis</div>
          <ul className="legal-basis-list">
            {data.legal_basis.map((item, i) => (
              <li key={i} className="legal-basis-item">
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Confidence */}
      {data.confidence !== undefined && (
        <div className="answer-section">
          <div className="answer-section-label">Confidence Score</div>
          <ConfidenceBadge confidence={data.confidence} reason={data.confidence_reason} />
        </div>
      )}

      {/* Citations */}
      {data.citations && data.citations.length > 0 ? (
        <SourcesPanel citations={data.citations} />
      ) : data.sources_available === false ? (
        <div className="sources-panel">
          <div className="sources-unavailable">
            <span>⚠️</span>
            <span>Legal resources not found — external services may be temporarily unavailable</span>
          </div>
        </div>
      ) : null}

      {/* Download Report Button */}
      {output && data.issue && (
        <ReportButton data={data} />
      )}
    </div>
  );
}

function ReportButton({ data }) {
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    setLoading(true);
    try {
      const { generateLegalReport } = await import("../lib/generatePDF");
      generateLegalReport(data);
    } catch (err) {
      console.error("PDF generation failed:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      className="report-download-btn"
      onClick={handleDownload}
      disabled={loading}
    >
      {loading ? (
        <>
          <span className="report-btn-spinner" />
          Generating...
        </>
      ) : (
        <>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          Download Report
        </>
      )}
    </button>
  );
}

function formatDomain(domain) {
  const map = {
    contract_law: "Contract Law",
    commercial_law: "Commercial Law",
    tort_law: "Tort Law",
    employment_law: "Employment Law",
    unknown: "General",
  };
  return map[domain] || domain;
}
