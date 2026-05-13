<p align="center">
  <img src="frontend/public/LawGraph.svg" alt="LawGraph Logo" width="120" />
</p>

<h1 align="center">LawGraph</h1>

<p align="center">
  <strong>AI-powered legal reasoning with real citations, structured analysis, and interactive knowledge graphs.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/LangGraph-10_Node_Pipeline-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/MCP-Stdio_Protocol-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Gemini-Flash-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" />
</p>

---

LawGraph retrieves **real U.S. case law and federal statutes** via the Model Context Protocol (MCP), applies **IRAC legal reasoning**, validates every citation against source material, and visualizes the analysis as an **interactive knowledge graph** — all streamed to the user in real time.

> *This system provides legal information and analysis, not legal representation.*

---

## ✨ Features

- **Grounded Citations** — Every citation is retrieved from CourtListener or GovInfo, never hallucinated  
- **IRAC Reasoning** — Issue → Rule → Application → Conclusion, the gold standard in legal analysis  
- **Knowledge Graph** — Entities (parties, statutes, concepts) and relationships visualized as an interactive force-directed graph  
- **Real-Time Streaming** — Watch each pipeline step execute live via SSE activity cards  
- **Confidence Scoring** — Transparent confidence levels so users know how much to trust the output  
- **Multi-Turn Conversations** — Follow-up questions maintain legal context across turns  
- **PDF Export** — Generate professional legal memo reports  

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────┐
│            Next.js Frontend                  │
│   Composer → ActivityCards → LegalAnswer     │
│              ↕ SSE Events                    │
├──────────────────────────────────────────────┤
│            FastAPI Backend                   │
│                                              │
│   LangGraph 10-Node Pipeline:                │
│   Preprocessor → Followup Detector           │
│   → Context Resolver → Classifier            │
│   → [Planner → Tool Executor → Aggregator]   │
│   → Reasoner → Formatter → Graph Extractor   │
│                                              │
│              ↕ MCP (stdio)                   │
├──────────────────────────────────────────────┤
│   CourtListener MCP    │   GovInfo MCP       │
│   (U.S. Case Law)      │   (Federal Statutes)│
└──────────────────────────────────────────────┘
```

### Pipeline Nodes

| # | Node | Purpose |
|---|------|---------|
| 1 | Preprocessor | Sanitize and normalize input |
| 2 | Followup Detector | Detect multi-turn context |
| 3 | Context Resolver | Resolve pronouns from history |
| 4 | Classifier | Detect legal domain, decide tool use |
| 5 | Planner | Generate tool call strategy |
| 6 | Tool Executor | Execute MCP tool calls |
| 7 | Aggregator | Deduplicate, rank, filter sources |
| 8 | Reasoner | IRAC analysis over sources |
| 9 | Formatter | Validate and structure output |
| 10 | Graph Extractor | Extract entities and relationships |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Google AI Studio API Key](https://aistudio.google.com/) (free)
- [CourtListener API Key](https://www.courtlistener.com/) (free)

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/LawGraph.git
cd LawGraph
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # Edit with your API keys
```

### 3. MCP Servers

```bash
cd legal-mcp/govinfo-mcp && npm install
cd ../courtlistener-mcp && npm install
```

### 4. Frontend Setup

```bash
cd frontend
npm install
```

### 5. Run

```bash
# Terminal 1 — Backend
cd backend && python -m app.main

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Open **http://localhost:3000** and ask your first legal question.

---

## ⚙️ Configuration

### Backend (`backend/.env`)

```env
# Required
GOOGLE_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.0-flash

# MCP Servers
MCP_GOVINFO_SERVER_PATH=../legal-mcp/govinfo-mcp/server.js
MCP_COURTLISTENER_SERVER_PATH=../legal-mcp/courtlistener-mcp/server.js

# Optional: External reasoning model
# REASONING_MODEL_URL=https://your-model-endpoint/v1/chat/completions
# REASONING_MODEL_API_KEY=your_key
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js, React, Vanilla CSS, SSE |
| Backend | FastAPI, Python, Uvicorn |
| Orchestration | LangGraph (StateGraph) |
| LLM | Google Gemini Flash (configurable) |
| Tools | Model Context Protocol (MCP) via stdio |
| Visualization | react-force-graph-2d, D3 |
| Legal Data | CourtListener API, GovInfo API |

---

## 🏛️ Supported Legal Domains

| Domain | Coverage |
|--------|----------|
| 🟠 **Contract Law** | Breach, formation, performance, remedies, UCC |
| 🟣 **Commercial Law** | Trade, IP, business disputes |
| 🔴 **Tort Law** | Negligence, liability, damages |
| 🟢 **Employment Law** | Termination, wages, discrimination |

---

## 📁 Project Structure

```
LawGraph/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI + SSE endpoint
│       ├── config.py            # Environment config
│       ├── graph/
│       │   ├── workflow.py      # LangGraph pipeline
│       │   ├── event_emitter.py # SSE emission
│       │   └── nodes/           # 10 pipeline nodes
│       ├── models/              # State schema + events
│       └── services/            # LLM, MCP, memory, graph store
├── frontend/
│   └── app/
│       ├── page.js              # Main UI
│       ├── globals.css          # Design system
│       ├── components/          # UI components
│       └── hooks/               # SSE + graph hooks
└── legal-mcp/
    ├── courtlistener-mcp/       # Case law MCP server
    └── govinfo-mcp/             # Federal statutes MCP server
```

---

## 🤝 Contributing

Contributions are welcome! Areas where help is especially valuable:

- **New MCP servers** — Additional legal data sources
- **Jurisdiction logic** — State-specific legal rules
- **Accessibility** — Voice input, multi-language support
- **Testing** — Unit and integration test coverage

---

## 📄 License

MIT License — see [LICENSE](./LICENSE) for details.

---

<p align="center">
  <strong>Built with the belief that access to legal knowledge is a fundamental right.</strong>
</p>
