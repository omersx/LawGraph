<p align="center">
  <img src="https://img.shields.io/badge/LangGraph-9_Node_Pipeline-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/MCP-Stdio_Protocol-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Gemini-3.1_Flash-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" />
</p>

# ⚖️ LawGraph

**An autonomous legal reasoning system powered by a 10-node LangGraph pipeline, grounded in real U.S. case law and federal statutes via the Model Context Protocol (MCP).**

> Most legal AI tools are wrappers around a chat model with a prompt. This system retrieves real legal data from CourtListener and GovInfo, applies structured IRAC reasoning, validates citations against retrieved sources, and streams the entire reasoning process to the user in real time.

---

## 🎯 The Problem

Access to legal information is broken:

- **1.2 billion people** worldwide face civil justice problems they can't resolve ([World Justice Project, 2024](https://worldjusticeproject.org/))
- The average cost of a lawyer in the U.S. is **$300–$500/hour**
- Existing AI chatbots **hallucinate case citations** — a [documented risk](https://www.nytimes.com/2023/05/27/nyregion/avianca-lawsuit-chatgpt-lawyers.html) that has led to court sanctions
- People need to understand their legal rights **before** they can afford an attorney

## 💡 The Solution

LawGraph provides **grounded, citation-backed legal analysis** using a multi-stage reasoning pipeline that:

1. **Retrieves real legal data** from authoritative sources (not from the model's training data)
2. **Applies structured IRAC reasoning** (Issue → Rule → Application → Conclusion) — the gold standard in legal analysis
3. **Validates every citation** against the retrieved source material — if the tool didn't return it, the model can't cite it
4. **Builds an Interactive Knowledge Graph** extracting entities (Parties, Statutes, Concepts) and their semantic relationships
5. **Quantifies confidence** so users know how much to trust the output
6. **Streams the reasoning process** in real time so the analysis is fully transparent

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend (Next.js)                │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────────┐│
│  │ Composer  │  │ ActivityCard │  │ LegalAnswer + Graph    ││
│  └────┬─────┘  └──────▲───────┘  └────────────▲───────────┘│
│       │               │                       │             │
│       │          SSE Events (streaming)        │             │
└───────┼───────────────┼───────────────────────┼─────────────┘
        │               │                       │
   POST /chat/stream    │                       │
        │               │                       │
┌───────▼───────────────┴───────────────────────┴─────────────┐
│                  FastAPI Backend (Python)                    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              LangGraph 10-Node Pipeline             │    │
│  │                                                     │    │
│  │  START → Preprocessor → Followup Detector           │    │
│  │         → Context Resolver → Classifier             │    │
│  │         → [Planner → Tool Executor → Aggregator]    │    │
│  │         → Reasoner → Formatter → Graph Extractor → END │    │
│  │                                                     │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                   │
│                    MCP Client                               │
│                   (stdio transport)                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
    ┌─────────▼─────────┐  ┌─────────▼──────────┐
    │  CourtListener MCP │  │   GovInfo MCP      │
    │  (Case Law Search) │  │  (Federal Statutes)│
    │                    │  │                    │
    │  • search_cases    │  │  • search_documents│
    │  • get_case_details│  │  • get_doc_details │
    │                    │  │  • get_doc_text    │
    │                    │  │  • extract_sections│
    └────────────────────┘  └────────────────────┘
```

### The 10-Node Pipeline

Each node has a single responsibility, emits real-time SSE events, and writes only to its designated state slot:

| # | Node | Purpose | Model |
|---|---|---|---|
| 1 | **Preprocessor** | Sanitize and normalize user input | — |
| 2 | **Followup Detector** | Detect if this is a follow-up to a previous query | Gemini Flash |
| 3 | **Context Resolver** | Resolve pronouns and references using conversation history | Gemini Flash |
| 4 | **Classifier** | Detect legal domain + decide if tools are needed | Gemini Flash |
| 5 | **Planner** | Generate tool call plan (which APIs to query) | Gemini Flash |
| 6 | **Tool Executor** | Execute tool calls via MCP protocol | MCP Client |
| 7 | **Aggregator** | Deduplicate, rank, and filter retrieved sources | — |
| 8 | **Reasoner** | Apply IRAC reasoning over sources to produce analysis | Configurable* |
| 9 | **Formatter** | Final validation and formatting | — |
| 10| **Graph Extractor** | Extracts entities and relationships into JSON-LD graph | Gemini Flash |

> \* The Reasoner supports hot-swappable models: primary Gemini, secondary Gemini account, OpenAI-compatible endpoint, or your own fine-tuned model.

### Conditional Routing

The pipeline includes an intelligent routing decision after classification:

```
Classifier ──→ needs_statutes OR needs_cases? ──→ Planner → Tool Executor → Aggregator → Reasoner
                          │
                          └── no tools needed ──→ Reasoner (direct)
```

This means simple legal questions skip the tool retrieval entirely, resulting in faster response times while complex questions get full research backing.

---

## 🔌 MCP Integration (Model Context Protocol)

The system uses **local stdio-based MCP servers** — not cloud APIs — giving you full control over the data pipeline.

### CourtListener MCP Server
- **`search_cases`** — Search U.S. court cases with filters (court, date range, judge)
- **`get_case_details`** — Retrieve full case metadata by cluster ID
- Covers **federal and state courts** across the entire U.S. judicial system
- Data source: [CourtListener.com](https://www.courtlistener.com/) (Free Law Project)

### GovInfo MCP Server
- **`search_documents`** — Browse U.S. government documents by collection (BILLS, CFR, FR, CREC)
- **`get_document_details`** — Retrieve package metadata
- **`get_document_text`** — Get text/HTML/XML source links
- **`extract_bill_sections`** — Parse structured sections from bill XML
- Data source: [GovInfo.gov](https://www.govinfo.gov/) (U.S. Government Publishing Office)

### Stdout Sanitization

A critical engineering challenge: the globally-installed `dotenvx` package on the host system was printing diagnostic messages to `stdout`, corrupting the JSON-RPC stream between the Python backend and Node.js MCP servers. We solved this with a **wrapper script** (`mcp_wrapper.mjs`) that monkey-patches `process.stdout.write` to filter non-JSON output before the MCP SDK attempts to parse it.

---

## 🧠 IRAC Legal Reasoning

The Reasoner node applies the **IRAC methodology** — the standard analytical framework taught in every law school:

```
┌──────────────────────────────────────────────────┐
│                 IRAC Framework                   │
├──────────────────────────────────────────────────┤
│                                                  │
│  I — ISSUE                                       │
│  "Whether the employer's termination without     │
│   notice constitutes a breach of contract"       │
│                                                  │
│  R — RULE                                        │
│  At-will employment doctrine; contractual        │
│  notice period requirements; wrongful            │
│  termination statutes                            │
│                                                  │
│  A — APPLICATION                                 │
│  Apply rules to the specific facts provided      │
│  by the user, citing retrieved case law and      │
│  statutes                                        │
│                                                  │
│  C — CONCLUSION                                  │
│  Clear determination with confidence score       │
│  and actionable next steps                       │
│                                                  │
└──────────────────────────────────────────────────┘
```

### Citation Validation

The system enforces a strict **no-hallucination policy** for citations:

1. The Reasoner receives only sources that were actually retrieved by the MCP tools
2. After generation, every citation is validated against the retrieved source URLs and titles
3. If the model failed to cite retrieved sources, they are injected automatically
4. If no sources were retrieved, the model is instructed to lower its confidence and use only general legal principles

---

## 🕸️ Interactive Knowledge Graph

The system doesn't just return text; it transforms unstructured legal analysis into an interactive, navigable mind map.

- **Entity Extraction:** An LLM-powered node processes the final output to identify key entities (Parties, Statutes, Cases, Legal Concepts, Jurisdictions).
- **Semantic Relationships:** Extracts typed relationships (e.g., `ALLEGES`, `GOVERNED_BY`, `CITED_IN`) connecting the entities.
- **Dynamic Visualization:** Uses a high-performance Canvas-based force-directed graph (`react-force-graph-2d`) on the frontend.
- **Interactive UI:** Includes hover highlighting, node detail slide-out panels, entity filtering, and real-time physics controls.

---

## 🖥️ Frontend Experience

### Real-Time Streaming with Activity Cards

The frontend uses **Server-Sent Events (SSE)** to stream the pipeline's progress in real time:

```
┌─────────────────────────────────────────┐
│  ✅ Processing input                    │
│  ✅ Checking conversation context       │
│  ✅ Classifying legal domain      2ms   │
│  ✅ Planning research strategy    15ms  │
│  ✅ Searching relevant cases            │
│  ✅ Searching relevant cases            │
│  ✅ Consolidating legal sources   9ms   │
│  ✅ Preparing legal analysis    1051ms  │
│  ✅ Finalizing response                 │
└─────────────────────────────────────────┘
```

### Structured Legal Output

The analysis is rendered as a structured card with:

- **Detected Domain** — Color-coded badge (Contract Law 🟠, Tort Law 🔴, Commercial Law 🟣, Employment Law 🟢)
- **Legal Issue** — Precise legal question formulation
- **Analysis** — Full IRAC reasoning with cited sources
- **Likely Outcome** — Clear, direct conclusion
- **Legal Basis** — Pill-styled tags of legal principles applied
- **Confidence Score** — Visual progress bar with percentage
- **Sources Used** — Expandable panel with linked citations

### SSE Event Protocol

The backend emits 12 distinct event types that the frontend handles:

| Event | Purpose |
|---|---|
| `run_started` | Pipeline initialized |
| `step_started` / `step_completed` | Node lifecycle tracking |
| `step_output` | Intermediate node results |
| `tool_started` / `tool_result` / `tool_failed` | MCP tool execution |
| `sources_aggregated` | Deduplication summary |
| `answer_started` / `answer_delta` / `answer_completed` | Streamed reasoning output |
| `followup_requested` | Agent asks for more information |
| `run_completed` | Pipeline finished |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16, React, Vanilla CSS, SSE via `@microsoft/fetch-event-source` |
| **Backend** | FastAPI, Python 3.13, Uvicorn |
| **Orchestration** | LangGraph (StateGraph with conditional edges) |
| **LLM** | Google Gemini 3.1 Flash (configurable — supports secondary accounts and external endpoints) |
| **Tool Protocol** | Model Context Protocol (MCP) via stdio transport |
| **MCP Servers** | Node.js with `@modelcontextprotocol/sdk` |
| **Legal Data** | CourtListener API (case law), GovInfo API (federal statutes) |
| **State** | In-memory conversation store with case memory persistence |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google AI Studio API key ([Get one free](https://aistudio.google.com/))
- CourtListener API key ([Register free](https://www.courtlistener.com/))

### 1. Clone & Setup Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

```env
# Required
GOOGLE_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.1-flash-lite

# MCP Servers (point to your local copies)
MCP_GOVINFO_SERVER_PATH=../legal-mcp/govinfo-mcp/server.js
MCP_COURTLISTENER_SERVER_PATH=../legal-mcp/courtlistener-mcp/server.js
COURTLISTENER_API_KEY=your_courtlistener_api_key

# Optional: Use a separate Gemini account for reasoning
# REASONING_GEMINI_API_KEY=your_second_api_key
# REASONING_GEMINI_MODEL=gemini-2.0-flash
```

### 3. Install MCP Server Dependencies

```bash
cd legal-mcp/govinfo-mcp && npm install
cd ../courtlistener-mcp && npm install
```

### 4. Start Backend

```bash
cd backend
python -m app.main
# → Uvicorn running on http://0.0.0.0:8000
```

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
# → Next.js running on http://localhost:3000
```

### 6. Open the App

Navigate to `http://localhost:3000` and ask your first legal question!

---

## 📊 Example Queries

| Query | What Happens |
|---|---|
| *"My employer terminated my contract without notice"* | Classifies as Employment Law → searches CourtListener for termination cases → applies at-will doctrine analysis |
| *"A supplier failed to deliver machinery after accepting a deposit"* | Classifies as Contract Law → retrieves breach of contract cases → analyzes material breach and restitution rights |
| *"What are the penalties for trademark infringement?"* | Classifies as Commercial Law → searches GovInfo for relevant statutes → provides statutory penalty ranges |
| *"Can I sue my neighbor for water damage from their broken pipe?"* | Classifies as Tort Law → searches for negligence and property damage cases → analyzes duty of care |

---

## 🔮 Roadmap

### Near-Term
- [ ] Multi-turn conversational analysis with follow-up questions
- [ ] Jurisdiction detection (state-specific law variations)
- [ ] PDF report generation for legal memos
- [ ] Full opinion text analysis from CourtListener

### Medium-Term
- [ ] Visual case law citation graph
- [ ] Risk assessment dashboard with factor-by-factor scoring
- [ ] Similar case comparison with outcome predictions
- [ ] Voice input for accessibility

### Long-Term
- [ ] Fine-tuned legal reasoning model (trained on IRAC analyses and bar exam data)
- [ ] User accounts with case history and deadline tracking
- [ ] Attorney handoff with structured briefs
- [ ] Multi-language support for underserved communities

---

## 🏛️ Legal Domains Supported

| Domain | Color | Coverage |
|---|---|---|
| **Contract Law** | 🟠 Orange | Breach, formation, performance, remedies, UCC |
| **Commercial Law** | 🟣 Purple | Trade, merchants, goods, IP, business disputes |
| **Tort Law** | 🔴 Rose | Negligence, liability, damages, duty of care |
| **Employment Law** | 🟢 Green | Termination, wages, discrimination, labor rights |

---

## 🔒 Responsible AI

This system is designed with safety and transparency at its core:

- **No hallucinated citations** — Every citation is validated against retrieved tool data
- **Confidence scoring** — Users see exactly how confident the system is in its analysis
- **Full transparency** — The streaming activity card shows every step of the reasoning process
- **Clear disclaimer** — *"This system provides legal information and analysis, not legal representation."*
- **Source attribution** — All legal data comes from authoritative government and judicial sources

---

## 📁 Project Structure

```
LawGraph/
├── backend/
│   ├── app/
│   │   ├── config.py              # Environment configuration
│   │   ├── main.py                # FastAPI app + SSE streaming endpoint
│   │   ├── graph/
│   │   │   ├── workflow.py        # LangGraph StateGraph definition
│   │   │   ├── event_emitter.py   # SSE event emission utility
│   │   │   └── nodes/
│   │   │       ├── preprocessor.py
│   │   │       ├── followup_detector.py
│   │   │       ├── context_resolver.py
│   │   │       ├── classifier.py
│   │   │       ├── planner.py
│   │   │       ├── tool_executor.py
│   │   │       ├── aggregator.py
│   │   │       ├── reasoner.py
│   │   │       ├── formatter.py
│   │   │       └── graph_extractor_node.py
│   │   ├── models/
│   │   │   ├── state.py           # GraphState TypedDict schema
│   │   │   └── events.py          # SSE event labels
│   │   └── services/
│   │       ├── llm.py             # LLM routing (Gemini / external)
│   │       ├── mcp_client.py      # MCP session pool + tool calling
│   │       ├── memory.py          # Conversation memory store
│   │       ├── graph_extractor.py # LLM entity extraction logic
│   │       └── graph_store.py     # In-memory knowledge graph store
│   └── scripts/
│       └── mcp_wrapper.mjs        # Stdout sanitization wrapper
├── frontend/
│   └── app/
│       ├── page.js                # Main chat page
│       ├── globals.css            # Design system
│       ├── hooks/
│       │   └── useSSE.js          # SSE streaming hook
│       ├── components/
│       │   ├── Sidebar.js         # Conversation list
│       │   ├── Composer.js        # Chat input
│       │   ├── ActivityCard.js    # Pipeline progress
│       │   ├── LegalAnswer.js     # Structured analysis output
│       │   ├── KnowledgeGraph.js  # Interactive node visualization
│       │   ├── GraphDetailPanel.js# Entity details and connections
│       │   ├── ConfidenceBadge.js # Confidence visualization
│       │   └── SourcesPanel.js    # Citation list
│       └── lib/
│           └── api.js             # API endpoint config
└── legal-mcp/
    ├── courtlistener-mcp/
    │   └── server.js              # CourtListener MCP server
    └── govinfo-mcp/
        └── server.js              # GovInfo MCP server
```

---

## 🤝 Contributing

Contributions are welcome! Areas where help is especially valuable:

- **New MCP servers** — Add more legal data sources (state statutes, regulations, legal dictionaries)
- **Jurisdiction logic** — State-specific legal rule databases
- **Fine-tuning data** — Curated IRAC-format legal analyses for model training
- **Accessibility** — Voice input, screen reader support, multi-language

---

## 📄 License

MIT License — see [LICENSE](./LICENSE) for details.

---

<p align="center">
  <strong>Built with the belief that access to legal knowledge is a fundamental right.</strong>
</p>
