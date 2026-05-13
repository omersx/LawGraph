"use client";
import { useState, useRef, useEffect } from "react";

export default function Composer({ onSend, disabled }) {
  const [text, setText] = useState("");
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 200) + "px";
    }
  }, [text]);

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="composer-wrapper">
      <div className="composer">
        <div className="composer-input-row">
          <textarea
            ref={textareaRef}
            className="composer-textarea"
            placeholder="Describe your legal issue. Include relevant facts, dates, and what happened..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            rows={1}
          />
          <button
            className="composer-send-btn"
            onClick={handleSend}
            disabled={disabled || !text.trim()}
            title="Send message"
          >
            ➤
          </button>
        </div>
        <p className="composer-disclaimer">
          This system provides legal information and analysis, not legal representation.
        </p>
      </div>
    </div>
  );
}
