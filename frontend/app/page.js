"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import Sidebar from "./components/Sidebar";
import Composer from "./components/Composer";
import ActivityCard from "./components/ActivityCard";
import LegalAnswer from "./components/LegalAnswer";
import ClarificationBubble from "./components/ClarificationBubble";
import KnowledgeGraph from "./components/KnowledgeGraph";
import GraphDetailPanel from "./components/GraphDetailPanel";
import { useSSE } from "./hooks/useSSE";
import { useGraph } from "./hooks/useGraph";
import { fetchConversations, createConversation, fetchConversation } from "./lib/api";

const EXAMPLE_PROMPTS = [
  "A supplier accepted a deposit and failed to deliver machinery",
  "My employer terminated my contract without notice",
  "Can a landlord keep my security deposit without justification?",
  "Client didn't pay after receiving the completed service",
];

export default function Home() {
  // ── Conversations ──
  const [conversations, setConversations] = useState([]);
  const [activeConvoId, setActiveConvoId] = useState(null);
  const [messages, setMessages] = useState([]);

  // ── View Toggle ──
  const [activeView, setActiveView] = useState("chat"); // "chat" | "graph"

  // ── SSE Streaming ──
  const {
    steps,
    streamedAnswer,
    finalOutput,
    followup,
    isRunning,
    error,
    runMeta,
    graphReady,
    startStream,
  } = useSSE();

  // ── Graph ──
  const {
    graphData,
    rawGraphData,
    selectedNode,
    loading: graphLoading,
    error: graphError,
    filters,
    toggleFilter,
    selectNode,
    clearSelection,
    refresh: refreshGraph,
    hasData: hasGraphData,
  } = useGraph(activeConvoId);

  const chatEndRef = useRef(null);

  // ── Load conversations ──
  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const convos = await fetchConversations();
      setConversations(convos);
    } catch {
      // Backend not running yet — that's OK
    }
  };

  // ── Auto-scroll ──
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, steps, streamedAnswer, finalOutput, followup]);

  // ── When final output arrives, add to messages ──
  useEffect(() => {
    if (finalOutput) {
      setMessages((prev) => {
        const last = prev[prev.length - 1];
        if (last && last.role === "assistant" && !last.output) {
          // Update the placeholder assistant message
          return prev.map((m, i) =>
            i === prev.length - 1 ? { ...m, output: finalOutput, steps: [...steps] } : m
          );
        }
        return prev;
      });
      // Refresh conversation list
      loadConversations();
    }
  }, [finalOutput]);

  // ── When graph is ready, refresh graph data ──
  useEffect(() => {
    if (graphReady) {
      refreshGraph();
    }
  }, [graphReady, refreshGraph]);

  // ── When a follow-up / clarification arrives ──
  useEffect(() => {
    if (followup) {
      setMessages((prev) => {
        // Replace the placeholder assistant message with a clarification
        const last = prev[prev.length - 1];
        if (last && last.role === "assistant" && !last.output) {
          return prev.map((m, i) =>
            i === prev.length - 1
              ? {
                  ...m,
                  role: "clarification",
                  question: followup.question,
                  missingFields: followup.missingFields,
                  steps: [...steps],
                }
              : m
          );
        }
        // Otherwise append as new clarification
        return [
          ...prev,
          {
            role: "clarification",
            question: followup.question,
            missingFields: followup.missingFields,
            steps: [...steps],
          },
        ];
      });
      // Refresh conversation list
      loadConversations();
    }
  }, [followup]);

  // ── Select conversation ──
  const handleSelectConvo = useCallback(async (id) => {
    setActiveConvoId(id);
    try {
      const data = await fetchConversation(id);
      const loadedMessages = (data.messages || []).map((m) => {
        if (m.role === "assistant" && typeof m.content === "object") {
          // Check if it's a clarification message
          if (m.content.type === "clarification") {
            return {
              role: "clarification",
              question: m.content.question,
              missingFields: [],
              steps: [],
            };
          }
          return { role: "assistant", output: m.content, steps: [] };
        }
        return m;
      });
      setMessages(loadedMessages);
    } catch {
      setMessages([]);
    }
  }, []);

  // ── New chat ──
  const handleNewChat = useCallback(async () => {
    try {
      const data = await createConversation();
      setActiveConvoId(data.id);
      setMessages([]);
      loadConversations();
    } catch {
      // Generate a local ID if backend isn't running
      const localId = "local_" + Date.now();
      setActiveConvoId(localId);
      setMessages([]);
    }
  }, []);

  // ── Send message ──
  const handleSend = useCallback(
    async (text) => {
      let convoId = activeConvoId;

      // Create conversation if none active
      if (!convoId) {
        try {
          const data = await createConversation();
          convoId = data.id;
          setActiveConvoId(convoId);
          loadConversations();
        } catch {
          convoId = "local_" + Date.now();
          setActiveConvoId(convoId);
        }
      }

      // Switch to chat view when sending
      setActiveView("chat");

      // Add user message + placeholder assistant
      setMessages((prev) => [
        ...prev,
        { role: "user", content: text },
        { role: "assistant", output: null, steps: [] },
      ]);

      // Start SSE stream
      startStream(text, convoId);
    },
    [activeConvoId, startStream]
  );

  // ── Handle example prompt click ──
  const handleExampleClick = (prompt) => {
    handleSend(prompt);
  };

  const hasMessages = messages.length > 0;

  return (
    <div className="app-layout">
      <Sidebar
        conversations={conversations}
        activeId={activeConvoId}
        onSelect={handleSelectConvo}
        onNewChat={handleNewChat}
      />

      <main className="main-panel">
        {/* ── Header with View Toggle ── */}
        <div className="view-header">
          <div className="view-toggle">
            <button
              className={`view-toggle-btn ${activeView === "chat" ? "active" : ""}`}
              onClick={() => setActiveView("chat")}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              <span>Chat</span>
            </button>
            <button
              className={`view-toggle-btn ${activeView === "graph" ? "active" : ""}`}
              onClick={() => setActiveView("graph")}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="6" cy="6" r="3" />
                <circle cx="18" cy="6" r="3" />
                <circle cx="12" cy="18" r="3" />
                <line x1="8.5" y1="7.5" x2="10.5" y2="16" />
                <line x1="15.5" y1="7.5" x2="13.5" y2="16" />
                <line x1="9" y1="6" x2="15" y2="6" />
              </svg>
              <span>Graph</span>
              {hasGraphData && activeView !== "graph" && (
                <span className="graph-badge-dot" />
              )}
            </button>
            {/* Animated indicator pill */}
            <div
              className="view-toggle-indicator"
              style={{
                transform: activeView === "graph" ? "translateX(100%)" : "translateX(0)",
              }}
            />
          </div>
        </div>

        {/* ── Chat View ── */}
        {activeView === "chat" && (
          <>
            <div className="chat-thread">
              {!hasMessages && !isRunning ? (
                /* ── Empty State ── */
                <div className="empty-state">
                  <img src="/LawGraph.svg" alt="LawGraph Logo" style={{ width: 80, height: 80, marginBottom: 20, borderRadius: 16 }} />
                  <h2>LawGraph</h2>
                  <p>
                    Describe your legal issue to receive structured, citation-backed
                    analysis of contract and business law disputes.
                  </p>
                  <div className="example-prompts">
                    {EXAMPLE_PROMPTS.map((prompt, i) => (
                      <button
                        key={i}
                        className="example-prompt"
                        onClick={() => handleExampleClick(prompt)}
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                /* ── Messages ── */
                <div className="chat-messages">
                  {messages.map((msg, i) => {
                    if (msg.role === "user") {
                      return (
                        <div key={i} className="user-message animate-in">
                          <div className="user-message-bubble">{msg.content}</div>
                        </div>
                      );
                    }

                    if (msg.role === "clarification") {
                      const isLast = i === messages.length - 1;
                      const showLiveActivity = isLast && isRunning;

                      return (
                        <div key={i} className="assistant-turn animate-in">
                          {/* Activity Card */}
                          {(showLiveActivity || (msg.steps && msg.steps.length > 0)) && (
                            <ActivityCard
                              steps={showLiveActivity ? steps : msg.steps || []}
                              isRunning={showLiveActivity}
                            />
                          )}

                          {/* Clarification Bubble */}
                          <ClarificationBubble
                            question={msg.question}
                            missingFields={msg.missingFields}
                          />
                        </div>
                      );
                    }

                    if (msg.role === "assistant") {
                      const isLastAssistant = i === messages.length - 1;
                      const showLiveActivity = isLastAssistant && isRunning;
                      const showLiveAnswer = isLastAssistant && (streamedAnswer || finalOutput);

                      return (
                        <div key={i} className="assistant-turn animate-in">
                          {/* Activity Card */}
                          {(showLiveActivity || (msg.steps && msg.steps.length > 0)) && (
                            <ActivityCard
                              steps={showLiveActivity ? steps : msg.steps || []}
                              isRunning={showLiveActivity}
                            />
                          )}

                          {/* Legal Answer */}
                          {showLiveAnswer ? (
                            <LegalAnswer
                              output={finalOutput}
                              streamedText={finalOutput ? null : streamedAnswer}
                            />
                          ) : msg.output ? (
                            <LegalAnswer output={msg.output} />
                          ) : isRunning && isLastAssistant ? null : null}

                          {/* Error */}
                          {isLastAssistant && error && (
                            <div
                              className="answer-section"
                              style={{
                                background: "rgba(239, 68, 68, 0.05)",
                                border: "1px solid rgba(239, 68, 68, 0.2)",
                                borderRadius: "var(--radius-md)",
                                padding: "12px 16px",
                                color: "var(--error)",
                                fontSize: "13px",
                              }}
                            >
                              ⚠ {error}
                            </div>
                          )}
                        </div>
                      );
                    }

                    return null;
                  })}
                  <div ref={chatEndRef} />
                </div>
              )}
            </div>

            <Composer onSend={handleSend} disabled={isRunning} />
          </>
        )}

        {/* ── Graph View ── */}
        {activeView === "graph" && (
          <div className="graph-view">
            <KnowledgeGraph
              graphData={graphData}
              selectedNode={selectedNode}
              onNodeSelect={selectNode}
              onBackgroundClick={clearSelection}
              filters={filters}
              onToggleFilter={toggleFilter}
              loading={graphLoading}
              error={graphError}
              hasData={hasGraphData}
              onRefresh={refreshGraph}
            />
            <GraphDetailPanel
              node={selectedNode}
              graphData={rawGraphData}
              onClose={clearSelection}
            />
          </div>
        )}
      </main>
    </div>
  );
}
