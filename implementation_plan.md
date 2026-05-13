# Legal AI Agent Platform — Implementation Plan

Build the full Legal AI Agent system: a Python/FastAPI backend with LangGraph orchestration streaming via SSE to a Next.js React frontend. The system analyzes contract/business law disputes using real legal APIs (GovInfo, CourtListener) and provides citation-backed, structured legal reasoning.

---

## User Review Required

> [!IMPORTANT]
> **API Keys Needed**: You will need the following API keys before running the system:
> 1. **Google Gemini API Key** — For the classifier, planner, follow-up detector, and reasoner nodes (Gemini Flash for lightweight nodes, can also serve as stand-in reasoner until your fine-tuned model is ready)
> 2. **GovInfo API Key** — Free from [api.data.gov](https://api.data.gov/signup/). `DEMO_KEY` works for testing.
> 3. **CourtListener API Token** — Free from [courtlistener.com](https://www.courtlistener.com/) (create account → profile → API token)

> [!WARNING]
> **Fine-Tuned Model**: The design calls for a separate fine-tuned model for the Reasoner node. Since it's accessed via "external API", I'll implement the Reasoner node to support **both** Gemini Flash (default/fallback) **and** a configurable external model endpoint. You can swap in your fine-tuned model later by setting `REASONING_MODEL_URL` in `.env`.

## Open Questions

> [!IMPORTANT]
> 1. Do you want me to use **Gemini 2.0 Flash** or **Gemini 2.5 Flash** for the lightweight nodes?
> 2. Do you already have any of the API keys above, or should I set up the system to work with `DEMO_KEY` for GovInfo and mock data for CourtListener initially?

---

## Proposed Changes

### Project Structure

```
legal-agent/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app, SSE endpoint, CORS
│   │   ├── config.py                # Environment config (Pydantic Settings)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── state.py             # LangGraph TypedDict state schema
│   │   │   └── events.py            # SSE event Pydantic models (13 events)
│   │   ├── graph/
│   │   │   ├── __init__.py
│   │   │   ├── workflow.py           # LangGraph StateGraph definition + compilation
│   │   │   ├── event_emitter.py      # Utility to emit SSE events from nodes
│   │   │   └── nodes/
│   │   │       ├── __init__.py
│   │   │       ├── preprocessor.py       # Node 1: Input cleaning
│   │   │       ├── followup_detector.py  # Node 2: Follow-up detection
│   │   │       ├── context_resolver.py   # Node 3: Context resolution
│   │   │       ├── classifier.py         # Node 4: Domain + intent classification
│   │   │       ├── planner.py            # Node 5: Tool selection + query gen
│   │   │       ├── tool_executor.py      # Node 6: MCP tool orchestration
│   │   │       ├── aggregator.py         # Node 7: Dedup, rank, filter, compress
│   │   │       ├── reasoner.py           # Node 8: Legal reasoning (fine-tuned/Gemini)
│   │   │       └── formatter.py          # Node 9: Final JSON assembly
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── statute_tool.py       # GovInfo API integration
│   │   │   └── case_law_tool.py      # CourtListener API integration
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── llm.py                # Model routing (Gemini Flash + external)
│   │       └── memory.py             # In-memory conversation/case memory store
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── ... (Next.js app — created via create-next-app)
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.js
│   │   │   ├── page.js               # Main chat page
│   │   │   └── globals.css           # Design system
│   │   ├── components/
│   │   │   ├── Sidebar.js            # Conversation list + new chat
│   │   │   ├── ChatThread.js         # Message list container
│   │   │   ├── UserMessage.js        # User message bubble
│   │   │   ├── AssistantTurn.js      # Activity card + legal answer
│   │   │   ├── ActivityCard.js       # Progressive workflow steps
│   │   │   ├── LegalAnswer.js        # Streamed structured legal answer
│   │   │   ├── SourcesPanel.js       # Expandable citations
│   │   │   ├── Composer.js           # Input box + submit
│   │   │   └── ConfidenceBadge.js    # Confidence score indicator
│   │   ├── hooks/
│   │   │   └── useSSE.js             # SSE event listener hook
│   │   └── lib/
│   │       └── api.js                # API client
│   └── package.json
├── legal-system.md                   # (existing)
└── app-ui.md                         # (existing)
```

---

### Backend

#### [NEW] `backend/app/config.py`
Pydantic Settings for environment configuration: API keys (Gemini, GovInfo, CourtListener), model names, external reasoning model URL, server port.

#### [NEW] `backend/app/models/state.py`
The **canonical** LangGraph state schema as a TypedDict, matching the refined schema from `app-ui.md` (lines 1730–1743):
- `run_id`, `conversation_id`, `user_input`
- `followup_context`, `classification`, `plan`
- `retrieval`, `aggregation`, `reasoning`, `output`, `meta`

#### [NEW] `backend/app/models/events.py`
Pydantic models for all **13 SSE event types**: `run_started`, `step_started`, `step_completed`, `step_output`, `tool_started`, `tool_result`, `tool_failed`, `sources_aggregated`, `answer_started`, `answer_delta`, `answer_completed`, `followup_requested`, `run_completed`. Each event has the shared envelope (run_id, conversation_id, timestamp, seq).

#### [NEW] `backend/app/graph/event_emitter.py`
Utility that wraps `get_stream_writer()` to emit structured SSE events from inside LangGraph nodes. Provides helper methods: `emit_step_started()`, `emit_step_completed()`, `emit_tool_started()`, etc.

#### [NEW] `backend/app/graph/nodes/` (all 9 nodes)
Each node:
1. **Preprocessor** — Strips whitespace, normalizes text. Pure Python.
2. **Follow-up Detector** — Uses Gemini Flash with the follow-up detector prompt. Returns `{is_follow_up, reason}`.
3. **Context Resolver** — If follow-up, merges case memory with current input. Pure Python + optional Gemini.
4. **Classifier** — Uses Gemini Flash with classifier prompt. Returns `{domain, intent, needs_statutes, needs_cases}`.
5. **Planner** — Uses Gemini Flash with planner prompt. Returns `{tools_to_call, queries}`.
6. **Tool Executor** — Calls MCP tools (statute_tool, case_law_tool) in parallel using `asyncio.gather()`.
7. **Aggregator** — Pure Python: normalize, dedup, score relevance (keyword match + domain match), rank, filter top 5, compress summaries.
8. **Reasoner** — Uses the fine-tuned model (or Gemini Flash fallback) with the full legal reasoning system prompt. Streams `answer_delta` events.
9. **Formatter** — Pure Python: validates JSON, attaches citations from tool data, computes confidence score, builds final output.

#### [NEW] `backend/app/graph/workflow.py`
LangGraph `StateGraph` definition:
- Registers all 9 nodes
- Adds conditional edges (skip tools when `needs_statutes=false AND needs_cases=false`)
- Compiles with `stream_mode=["updates", "custom"]` for SSE events
- Uses `get_stream_writer()` for custom event emission

#### [NEW] `backend/app/tools/statute_tool.py`
GovInfo API integration:
- Endpoint: `POST https://api.govinfo.gov/search?api_key={key}`
- Collection: `USCODE`
- Returns: `{title, section, summary, source, source_url}`
- Max 5 results, structured JSON output

#### [NEW] `backend/app/tools/case_law_tool.py`
CourtListener API integration:
- Endpoint: `GET https://www.courtlistener.com/api/rest/v4/search/?q={query}&type=o`
- Auth: Token header
- Returns: `{case_name, citation, court, year, summary, source_url}`
- Max 5 results, structured JSON output

#### [NEW] `backend/app/services/llm.py`
Model routing service:
- `get_flash_model()` — Returns `ChatGoogleGenerativeAI(model="gemini-2.0-flash")` for lightweight nodes
- `get_reasoning_model()` — Returns either external model client (if `REASONING_MODEL_URL` set) or Gemini Flash fallback
- All models use `.with_structured_output()` where possible for JSON enforcement

#### [NEW] `backend/app/services/memory.py`
In-memory conversation store:
- `ConversationMemory` class with dict-based storage
- Stores `case_memory` (extracted legal facts) and `conversation_history` (last 5 turns)
- Methods: `get_memory()`, `update_memory()`, `create_conversation()`

#### [NEW] `backend/app/main.py`
FastAPI application:
- `POST /api/chat` — SSE streaming endpoint. Accepts `{conversation_id, message}`, runs LangGraph, streams 13 event types.
- `GET /api/conversations` — List conversations
- `POST /api/conversations` — Create new conversation
- `GET /api/conversations/{id}` — Get conversation history
- CORS middleware for frontend

---

### Frontend

#### [NEW] Next.js App (via `create-next-app`)
Initialized with App Router, no Tailwind (vanilla CSS), JavaScript.

#### [NEW] `frontend/src/app/globals.css`
Full design system:
- CSS custom properties for colors, typography, spacing
- Dark theme (legal/professional aesthetic)
- Inter font from Google Fonts
- Glassmorphism effects for cards
- Smooth animations and transitions

#### [NEW] `frontend/src/components/Sidebar.js`
Left sidebar with:
- Conversation list with auto-generated titles
- Active conversation highlighting
- "New Chat" button with icon
- Collapsible on mobile

#### [NEW] `frontend/src/components/ChatThread.js`
Central chat area:
- Scrollable message list
- Auto-scroll on new messages
- Empty state with example prompts

#### [NEW] `frontend/src/components/AssistantTurn.js`
Wraps `ActivityCard` + `LegalAnswer` as two linked UI objects per assistant response.

#### [NEW] `frontend/src/components/ActivityCard.js`
Progressive workflow steps:
- Collapsible (default: "Working…" → expanded: step list)
- Live step updates with checkmarks (✓)
- Active step has animated spinner
- Muted state after completion

#### [NEW] `frontend/src/components/LegalAnswer.js`
Streamed structured legal answer with 5 sections:
- Domain badge
- Legal issue statement
- Analysis (streamed token-by-token)
- Legal basis list
- Sources panel (expandable)

#### [NEW] `frontend/src/components/SourcesPanel.js`
Expandable citations:
- Compact: "Sources used (3)"
- Expanded: statute title, citation, court, source URL link
- Each source has type badge (statute/case)

#### [NEW] `frontend/src/components/Composer.js`
Bottom input area:
- Large textarea with placeholder
- Submit button with keyboard shortcut (Enter)
- Disclaimer text
- Disabled state during active run

#### [NEW] `frontend/src/hooks/useSSE.js`
Custom hook using `@microsoft/fetch-event-source`:
- Connects to `POST /api/chat`
- Handles all 13 event types
- Updates React state progressively
- Reconnection with `seq` tracking

---

## Verification Plan

### Automated Tests
1. Run `pip install -r requirements.txt` and verify backend starts with `uvicorn`
2. Run `npm install && npm run dev` and verify frontend starts
3. Test SSE streaming endpoint with curl: `curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d '{"message":"supplier kept deposit"}'`

### Manual Verification
1. Open frontend in browser
2. Create a new conversation
3. Type a legal question (e.g., "A supplier accepted my deposit and failed to deliver machinery")
4. Verify: activity card shows progressive steps → answer streams section-by-section → citations appear
5. Test follow-up: "What if they refuse to refund?" → verify context continuity
6. Test new issue detection: "I had a traffic accident" → verify new analysis starts
