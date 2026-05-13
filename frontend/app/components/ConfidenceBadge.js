"use client";

export default function ConfidenceBadge({ confidence }) {
  if (confidence === undefined || confidence === null) return null;

  const pct = Math.round(confidence * 100);
  const level = confidence >= 0.75 ? "high" : confidence >= 0.5 ? "medium" : "low";
  const label = level === "high" ? "High Confidence" : level === "medium" ? "Moderate" : "Low Confidence";

  return (
    <div className={`confidence-badge ${level}`}>
      <div className="confidence-header">
        <div className="confidence-bar">
          <div
            className={`confidence-fill ${level}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <span>{label} ({pct}%)</span>
      </div>
    </div>
  );
}
