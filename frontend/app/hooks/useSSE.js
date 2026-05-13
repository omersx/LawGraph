"use client";
import { useCallback, useRef, useState } from "react";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import { getChatStreamUrl } from "../lib/api";

/**
 * Custom hook for SSE streaming from the Legal AI backend.
 *
 * Returns state and controls for the chat streaming pipeline.
 */
export function useSSE() {
  const [steps, setSteps] = useState([]);
  const [toolResults, setToolResults] = useState([]);
  const [streamedAnswer, setStreamedAnswer] = useState("");
  const [finalOutput, setFinalOutput] = useState(null);
  const [followup, setFollowup] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState(null);
  const [runMeta, setRunMeta] = useState(null);
  const [graphReady, setGraphReady] = useState(false);
  const controllerRef = useRef(null);

  const reset = useCallback(() => {
    setSteps([]);
    setToolResults([]);
    setStreamedAnswer("");
    setFinalOutput(null);
    setFollowup(null);
    setError(null);
    setRunMeta(null);
    setGraphReady(false);
  }, []);

  const startStream = useCallback(async (message, conversationId) => {
    reset();
    setIsRunning(true);

    const ctrl = new AbortController();
    controllerRef.current = ctrl;

    try {
      await fetchEventSource(getChatStreamUrl(), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          conversation_id: conversationId || null,
        }),
        signal: ctrl.signal,

        onopen(response) {
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
          }
        },

        onmessage(ev) {
          if (!ev.data) return;

          try {
            const data = JSON.parse(ev.data);
            const eventType = data.event || ev.event;
            const payload = data.payload || {};

            switch (eventType) {
              case "run_started":
                setRunMeta({
                  runId: data.run_id,
                  conversationId: data.conversation_id,
                });
                break;

              case "step_started":
                setSteps((prev) => [
                  ...prev,
                  {
                    id: payload.step_id,
                    node: payload.node,
                    label: payload.label,
                    status: "active",
                  },
                ]);
                break;

              case "step_completed":
                setSteps((prev) =>
                  prev.map((s) =>
                    s.id === payload.step_id
                      ? { ...s, status: "completed", durationMs: payload.duration_ms }
                      : s
                  )
                );
                break;

              case "step_output":
                // Optional: store for debugging
                break;

              case "tool_started":
                setSteps((prev) => [
                  ...prev,
                  {
                    id: payload.tool_call_id,
                    node: "tool",
                    label: payload.label,
                    status: "active",
                  },
                ]);
                break;

              case "tool_result":
                setSteps((prev) =>
                  prev.map((s) =>
                    s.id === payload.tool_call_id
                      ? { ...s, status: "completed" }
                      : s
                  )
                );
                setToolResults((prev) => [
                  ...prev,
                  ...payload.results.map((r) => ({
                    ...r,
                    toolName: payload.tool_name,
                  })),
                ]);
                break;

              case "tool_failed":
                setSteps((prev) =>
                  prev.map((s) =>
                    s.id === payload.tool_call_id
                      ? { ...s, status: "failed", error: payload.error }
                      : s
                  )
                );
                break;

              case "sources_aggregated":
                // Aggregation stats — could display
                break;

              case "answer_started":
                setStreamedAnswer("");
                break;

              case "answer_delta":
                setStreamedAnswer((prev) => prev + payload.delta);
                break;

              case "answer_completed":
                setFinalOutput(payload.final || {});
                break;

              case "followup_requested":
                // Mark all active steps as completed since the pipeline paused for user input
                setSteps((prev) =>
                  prev.map((s) =>
                    s.status === "active" ? { ...s, status: "completed" } : s
                  )
                );
                setFollowup({
                  question: payload.question,
                  missingFields: payload.missing_fields,
                });
                break;

              case "run_completed":
                setIsRunning(false);
                if (payload.status === "failed") {
                  setError(payload.error || "Analysis failed");
                }
                break;

              case "graph_ready":
                setGraphReady(true);
                break;

              default:
                break;
            }
          } catch (parseErr) {
            console.warn("Failed to parse SSE event:", parseErr);
          }
        },

        onerror(err) {
          console.error("SSE error:", err);
          setIsRunning(false);
          setError("Connection lost. Please try again.");
          throw err; // Stop retrying
        },

        onclose() {
          setIsRunning(false);
        },
      });
    } catch (err) {
      if (err.name !== "AbortError") {
        setError(err.message || "Failed to connect");
      }
      setIsRunning(false);
    }
  }, [reset]);

  const stop = useCallback(() => {
    if (controllerRef.current) {
      controllerRef.current.abort();
      controllerRef.current = null;
    }
    setIsRunning(false);
  }, []);

  return {
    steps,
    toolResults,
    streamedAnswer,
    finalOutput,
    followup,
    isRunning,
    error,
    runMeta,
    graphReady,
    startStream,
    stop,
    reset,
  };
}
