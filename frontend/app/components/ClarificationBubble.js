"use client";

export default function ClarificationBubble({ question, missingFields }) {
  if (!question) return null;

  return (
    <div className="clarification-bubble animate-in">
      <div className="clarification-icon-row">
        <span className="clarification-icon">🔍</span>
        <span className="clarification-label">Follow-up Question</span>
      </div>
      <div className="clarification-text">{question}</div>
      {missingFields && missingFields.length > 0 && (
        <div className="clarification-tags">
          {missingFields.map((field, i) => (
            <span key={i} className="clarification-tag">
              {formatField(field)}
            </span>
          ))}
        </div>
      )}
      <div className="clarification-hint">
        Reply below to continue your consultation
      </div>
    </div>
  );
}

function formatField(field) {
  const map = {
    jurisdiction: "📍 Jurisdiction",
    timeline: "📅 Timeline",
    parties: "👥 Parties",
    key_facts: "📋 Key Facts",
    legal_question: "⚖️ Legal Question",
    amount: "💰 Amount",
    contract_terms: "📄 Contract Terms",
  };
  return map[field] || field.replace(/_/g, " ");
}
