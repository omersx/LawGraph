"use client";
import { useState } from "react";

export default function ActivityCard({ steps, isRunning }) {
  const [expanded, setExpanded] = useState(true);

  const allCompleted = steps.length > 0 && steps.every((s) => s.status === "completed");

  return (
    <div className={`activity-card animate-in ${allCompleted && !isRunning ? "completed" : ""}`}>
      <div className="activity-header" onClick={() => setExpanded(!expanded)}>
        <span className="activity-title">
          {isRunning ? (
            <>
              <span className="spinner" />
              Analyzing...
            </>
          ) : allCompleted ? (
            <>✓ Analysis complete</>
          ) : (
            <>Working...</>
          )}
        </span>
        <button className="activity-toggle">
          {expanded ? "▾" : "▸"}
        </button>
      </div>

      {expanded && steps.length > 0 && (
        <div className="activity-steps">
          {steps.map((step) => (
            <div
              key={step.id}
              className={`activity-step ${step.status}`}
            >
              <span className="step-icon">
                {step.status === "completed" ? (
                  "✓"
                ) : step.status === "active" ? (
                  <span className="spinner" />
                ) : step.status === "failed" ? (
                  "✗"
                ) : (
                  "○"
                )}
              </span>
              <span>{step.label}</span>
              {step.durationMs ? (
                <span style={{ fontSize: "10px", color: "var(--text-muted)", marginLeft: "auto" }}>
                  {step.durationMs}ms
                </span>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
