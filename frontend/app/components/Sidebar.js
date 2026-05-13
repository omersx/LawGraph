"use client";
import { useState } from "react";

export default function Sidebar({
  conversations,
  activeId,
  onSelect,
  onNewChat,
}) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <aside className={`sidebar ${isOpen ? "" : "collapsed"}`}>
      <button 
        className="sidebar-toggle-btn"
        onClick={() => setIsOpen(!isOpen)}
        title={isOpen ? "Close Sidebar" : "Open Sidebar"}
      >
        {isOpen ? "◂" : "▸"}
      </button>

      <div className="sidebar-content">
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <img src="/LawGraph.svg" alt="LawGraph Logo" style={{ width: 40, height: 40, borderRadius: 8 }} />
            <span className="sidebar-logo-text">LawGraph</span>
          </div>
          <button className="new-chat-btn" onClick={onNewChat} title="New Consultation">
            <span>＋</span> <span className="new-chat-text">New Consultation</span>
          </button>
        </div>

        <div className="sidebar-conversations">
          {conversations.length === 0 && (
            <p style={{ padding: "12px", fontSize: "12px", color: "var(--text-muted)" }}>
              No conversations yet
            </p>
          )}
          {conversations.map((convo) => (
            <div
              key={convo.id}
              className={`conversation-item ${convo.id === activeId ? "active" : ""}`}
              onClick={() => onSelect(convo.id)}
              title={convo.title}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="convo-icon" style={{ flexShrink: 0 }}>
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
              <div className="conversation-item-content">
                <div className="conversation-item-title">{convo.title}</div>
                <div className="conversation-item-meta">
                  {convo.message_count || 0} messages
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
