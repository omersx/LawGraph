# 🏗️ LEGAL AI AGENT PLATFORM (UPDATED — PRODUCTION ALIGNED)

---

# 🎯 1. SYSTEM GOAL

Build a **Contract & Business Legal Intelligence System** that:

* Analyzes legal disputes (especially contract/commercial)
* Applies structured legal reasoning (IRAC-style)
* Uses real legal sources (APIs)
* Provides **citation-backed answers**
* Avoids hallucination
* Uses controlled workflow via LangGraph

---

# 🧠 2. SYSTEM DESIGN PRINCIPLE

Split responsibilities clearly:

* 🧠 **Fine-Tuned Model** → Legal reasoning
* 🧠 **other model(gemini flash)** → other tasks
* 🔌 **MCP Tools** → Fetch real legal data
* 🧩 **LangGraph** → Control flow + orchestration
note : the model will be setup be exteranl api
---

# 🧩 3. CORE COMPONENTS

1. Frontend (UI / API client)
2. LangGraph Agent (conversation + orchestration)
3. Fine-Tuned Model (reasoning engine)
4. MCP Server (tool layer)
5. External Legal APIs
6. Aggregation + Formatting Layer

---

# 🧠 4. HIGH-LEVEL ARCHITECTURE

```
User
 ↓
LangGraph (conversation + control)
 ↓
Classifier → Planner
 ↓
Tool Execution (MCP)
 ↓
Aggregator (clean + rank)
 ↓
Reasoning Node (fine-tuned model)
 ↓
Formatter
 ↓
User Output
```

---

# ⚙️ 5. SYSTEM OUTPUT CONTRACT (FINAL)

```json
{
  "domain": "...",
  "issue": "...",
  "answer": "...",
  "legal_reasoning": "...",
  "legal_basis": [...],
  "citations": [...],
  "confidence": 0.0
}
```

---

# ⚠️ IMPORTANT

* `domain`, `issue`, `reasoning` → from fine-tuned model
* `legal_basis`, `citations` → from MCP tools
* `confidence` → computed at runtime (NOT trained)

---

# 🔌 6. MCP TOOL DESIGN

---

## 🎯 Objective

Convert APIs into structured, reliable tools.

---

## 🧰 MVP TOOLS (RECOMMENDED)

### 1. Statute Tool

Source: GovInfo API

**Output:**

* title
* section
* summary
* source
* source_url

---

### 2. Case Law Tool

Source: CourtListener

**Output:**

* case_name
* citation
* court
* year
* summary
* source_url

---

### 3. Company Tool (Optional but useful)

Source: OpenCorporates

---

## ⚠️ Optional (Later Phase)

* Congress.gov → only for law updates (NOT core MVP)

---

## 🔒 MCP RULES

* Each tool = ONE responsibility
* Return structured JSON only
* Always include `source` + `source_url`
* Limit results to max 5

---

# 🧠 7. LANGGRAPH WORKFLOW

---

## 🎯 Nodes

---

### 1. Classifier Node

Purpose:

* Detect legal domain
* Detect intent

Output:

```json
{
  "intent": "legal_analysis",
  "domain": "contract_law",
  "needs_statutes": true,
  "needs_cases": true
}
```

---

### 2. Planner Node

Purpose:

* Decide which tools to call
* Generate search queries

Output:

```json
{
  "tools_to_call": ["statute_tool", "case_tool"],
  "queries": ["breach of contract non payment law"]
}
```

---

### 3. Tool Execution Layer

* Calls MCP tools
* Can run in parallel

---

### 4. Aggregator Node (CRITICAL)

Purpose:

* Deduplicate results
* Rank relevance
* Keep top 3–5 results

---

### 5. Reasoning Node (CORE — Fine-Tuned Model)

Purpose:

* Apply legal reasoning
* Use BOTH:

  * user input
  * retrieved legal data

Rules:

* Must NOT hallucinate
* Must use tool data when available
* Must follow structured reasoning

---

### 6. Formatter Node

Purpose:

* Build final JSON
* Clean citations
* Ensure consistency

---

# 🔁 8. EXECUTION FLOW

---

Example:

User:
“I paid deposit but supplier didn’t deliver”

---

Flow:

1. Classifier:

   * domain → contract_law

2. Planner:

   * tools → statute + case

3. Tools:

   * fetch laws + cases

4. Aggregator:

   * select top results

5. Reasoning Node:

   * analyze dispute
   * apply legal logic

6. Formatter:

   * produce structured output

---

# 📚 9. DATA INJECTION RULES

---

Before reasoning node, provide:

* user case
* extracted issue
* top legal sources

---

## ❌ DO NOT:

* send raw API data
* send too many results

---

## ✅ DO:

* limit to top 3–5
* clean and structured inputs

---

# 🧾 10. CITATION SYSTEM

---

## RULES

* NEVER generate fake citations
* ONLY use tool outputs
* Include:

  * type
  * title
  * citation
  * source
  * source_url

---

## LIMIT

* 3–5 citations max

---

# 🧠 11. CONFIDENCE STRATEGY

---

Confidence is NOT trained.

Compute using:

* number of sources
* agreement between sources
* clarity of reasoning

---

## Example

* strong evidence → 0.8–0.95
* weak → 0.4–0.7
* no sources → ≤ 0.3

---

# ⚠️ 12. CRITICAL CONSTRAINTS

---

## ❌ NO hallucination

* no fake laws
* no fake cases

---

## ❌ NO tool-free answers (when data required)

---

## ❌ NO direct model tool calls

LangGraph controls tools

---

## ❌ NO uncontrolled loops

---

# 🚀 13. PERFORMANCE

---

* max 2–3 tools per query
* parallel tool execution
* caching for repeated queries
* logging (calls, latency, errors)

---

# 🔐 14. SAFETY

---

* optional disclaimer: “Not legal advice”
* always include citations
* transparency via `source_url`

---

# 🏁 FINAL SYSTEM DESCRIPTION

This system is:

👉 NOT a chatbot
👉 A **Legal Reasoning + Retrieval Engine**

It combines:

* structured legal reasoning (fine-tuned model)
* real legal data (APIs)
* controlled execution (LangGraph)

---

# 🔥 FINAL VERDICT

A production-ready system for:

* contract dispute analysis
* legal reasoning
* citation-backed answers

-----------------------------------------------------------


You’re at the point where ideas turn into a real system—so this needs to be **practical, buildable, and sequenced**, not just conceptual.

Below is a **full execution plan** your developer (or team) can follow step-by-step. No code, just **clear implementation guidance**.

---

# 🏗️ 0. PROJECT DEFINITION (Before Anything)

## 🎯 Product

> A **Contract-Focused Legal AI Assistant** that analyzes disputes and provides **citation-backed legal reasoning** using real legal sources.

---

## 🎯 MVP Scope (STRICT)

Start with:

* Domain: **contract + business law**
* Region: **US (initial)**
* Features:

  * Legal Q&A
  * Contract dispute analysis
  * Law + case retrieval
  * Structured output (JSON)

---

## ❌ Do NOT build yet:

* Multi-jurisdiction
* Full legislation tracking
* Complex UI features
* Over-automation

---

# 🧱 1. SYSTEM ARCHITECTURE (FINAL)

```text
Frontend
   ↓
LangGraph Agent (orchestrator)
   ↓
Classifier → Planner
   ↓
MCP Tools (APIs)
   ↓
Aggregator
   ↓
Reasoning Model (fine-tuned)
   ↓
Formatter
   ↓
Frontend Response
```

---

# 🧩 2. COMPONENT-BY-COMPONENT PLAN

---

## 🧠 A. Fine-Tuned Model (Reasoning Engine)

### 🎯 Goal

Teach the model to:

* detect domain
* extract issue
* generate legal reasoning
* produce structured answers

---

### 📦 Input Format (Training)

Each example should be:

* input: `case`
* output:

  * domain
  * issue
  * reasoning
  * judgment

---

### 📤 Output Format (Runtime)

```json
{
  "domain": "...",
  "issue": "...",
  "legal_reasoning": "...",
  "answer": "...",
  "confidence": 0.0
}
```

---

### ⚠️ Notes

* Do NOT include citations in training
* Keep reasoning structured (like your dataset)
* Focus on **consistency**

---

## 🧠 B. LangGraph Agent (Core Controller)

### 🎯 Role

* handle conversation
* manage flow
* call tools
* control execution

---

### 🧩 Nodes to Implement

---

### 1. Classifier Node

**Input:**

* user message

**Output:**

* domain
* intent
* flags (needs laws? needs cases?)

---

### 2. Planner Node

**Input:**

* classifier output
* user query

**Output:**

* tools to call
* search queries

---

### 3. Tool Execution Node

* calls MCP tools
* supports parallel execution

---

### 4. Aggregator Node

**Responsibilities:**

* remove duplicates
* rank results
* keep top 3–5

---

### 5. Reasoning Node

**Uses fine-tuned model**

**Input:**

* user case
* extracted issue
* retrieved legal data

**Output:**

* structured legal reasoning

---

### 6. Formatter Node

* builds final JSON
* injects citations
* adds confidence

---

# 🔌 3. MCP SERVER (TOOL LAYER)

---

## 🎯 Goal

Convert APIs into **clean, reliable tools**

---

## 🧰 Tools to Build (MVP)

---

### 1. Statute Tool

Source: GovInfo API

**Input:**

* keywords

**Output:**

* title
* section
* summary
* source
* source_url

---

### 2. Case Law Tool

Source: CourtListener API

**Output:**

* case_name
* citation
* court
* year
* summary
* source_url

---

### 3. Company Tool (Optional)

Source: OpenCorporates API

---

## 🔒 Rules

* max 5 results
* always structured JSON
* include `source_url`
* no raw/unfiltered responses

---

# 📊 4. AGGREGATION LAYER

---

## 🎯 Responsibilities

* deduplicate results
* rank by:

  * keyword match
  * relevance to issue
* filter noise

---

## Output

```json
{
  "top_statutes": [...],
  "top_cases": [...]
}
```

---

# 🧠 5. DATA INJECTION STRATEGY

---

## What goes into reasoning node:

* user input
* extracted issue
* top statutes
* top cases

---

## ⚠️ Constraints

* max 5 total references
* no raw API data
* no irrelevant sources

---

# 🧾 6. OUTPUT FORMATTER

---

## Final Output

```json
{
  "domain": "...",
  "issue": "...",
  "answer": "...",
  "legal_reasoning": "...",
  "legal_basis": [...],
  "citations": [...],
  "confidence": 0.0
}
```

---

## Citation Format

Each citation:

```json
{
  "type": "statute | case",
  "title": "...",
  "citation": "...",
  "source": "...",
  "source_url": "..."
}
```

---

# 🧠 7. CONFIDENCE SYSTEM

---

## Compute using:

* number of sources
* agreement between sources
* clarity of reasoning

---

## Example Rules

* 3 strong sources → 0.85+
* weak evidence → 0.5–0.7
* no sources → < 0.4

---

# 💬 8. CONVERSATION HANDLING

---

## Managed by LangGraph

Store:

* previous user inputs
* previous outputs
* extracted facts

---

## Behavior

* allow follow-up questions
* reuse context
* re-run flow when needed

---

# 🖥️ 9. FRONTEND (MVP)

---

## Core Features

* text input
* structured output display
* expandable citations
* copy/export pdf

---

## Optional (later)

* PDF export
* history
* chat memory UI

---

# ⚙️ 10. INFRASTRUCTURE

---

## Backend

* API server (FastAPI or similar)
* LangGraph runtime
* MCP server

---

## Storage

* logs (requests, responses)
* cache (API results)

---

## Performance

* parallel API calls
* caching repeated queries
* timeout handling

---

# 🔐 11. SAFETY & QUALITY

---

## Rules

* no hallucinated citations
* always use retrieved data
* show sources clearly

---

## Add

* disclaimer: “Not legal advice”
* logging for debugging

---

# 🚀 12. DEVELOPMENT PHASES

---

## 🟢 Phase 1 (Core)

* fine-tuned model ready
* classifier + reasoning working
* basic API integration

---

## 🟡 Phase 2 (RAG)

* planner + tools
* aggregation
* citation output

---

## 🔵 Phase 3 (Product)

* frontend
* conversation memory
* confidence scoring

---

## 🔴 Phase 4 (Optimization)

* caching
* ranking improvements
* latency reduction

---

# 🏁 FINAL SYSTEM

You are building:

> **A legal reasoning + retrieval system specialized in contract disputes, delivering structured, citation-backed legal analysis.**

---

# 🔥 Final Advice

Don’t try to perfect everything at once.

Start with:

1. reasoning model working
2. 1 API (GovInfo)
3. simple flow

Then expand.

---




-----------------------------------------------------------------------------



Good—this is the **most critical piece** of your system.
A weak system prompt = hallucinations, bad citations, broken structure.

I’ll give you a **production-grade system prompt** designed specifically for:

* your dataset (case → issue → reasoning → judgment)
* your architecture (LangGraph + MCP tools)
* your output format (structured JSON)
* your constraints (no hallucination, citation-based)

---

# 🧠 ✅ FULL SYSTEM PROMPT (FINAL — READY TO USE)

You are a **Legal Reasoning Agent specialized in contract and commercial law disputes**.

You operate as part of a controlled system with external tools that provide verified legal data (statutes and case law). Your role is to **analyze legal problems, apply structured reasoning, and produce accurate, citation-supported outputs**.

---

# 🎯 PRIMARY OBJECTIVE

Given:

* a user legal problem (case description)
* optionally retrieved legal sources (statutes, cases)

You must:

1. Identify the legal **domain**
2. Formulate the **legal issue**
3. Apply **structured legal reasoning**
4. Provide a clear **answer**
5. Use retrieved sources to support your reasoning (if available)
6. Output a **strict JSON response**

---

# ⚖️ REASONING STYLE (MANDATORY)

Follow structured legal reasoning similar to IRAC:

* Issue → clearly defined legal question
* Rule → legal principle (from sources if available)
* Application → apply rule to facts
* Conclusion → final answer

Your reasoning must be:

* logical
* consistent
* based on facts provided
* aligned with legal principles

---

# 📥 INPUT YOU WILL RECEIVE

You may receive:

### 1. User Case

A natural language description of a dispute

### 2. Retrieved Legal Data (Optional)

Structured data such as:

* statutes
* case law
* summaries
* citations
* source_url

---

# 📤 OUTPUT FORMAT (STRICT — NO DEVIATION)

You MUST return ONLY valid JSON:

{
"domain": "...",
"issue": "...",
"answer": "...",
"legal_reasoning": "...",
"legal_basis": [...],
"citations": [...],
"confidence": 0.0
}

---

# 🧾 FIELD DEFINITIONS

## domain

* One of: contract_law, commercial_law, tort_law
* Choose the closest match

---

## issue

* A precise legal question
* Must start with "Whether..."

---

## answer

* Clear, direct conclusion
* No ambiguity

---

## legal_reasoning

* Structured explanation
* Apply legal principles to facts
* Do NOT repeat the issue verbatim

---

## legal_basis

* List of legal principles used
* Derived from:

  * retrieved statutes
  * case law
  * general legal doctrine

---

## citations

* MUST come ONLY from provided tool data
* Each citation must include:

  * type (statute | case)
  * title
  * citation (if available)
  * source
  * source_url

---

## confidence

* Value between 0 and 1
* Based on:

  * strength of reasoning
  * availability of supporting sources

---

# 🔒 STRICT RULES (CRITICAL)

## ❌ DO NOT:

* invent laws or cases
* fabricate citations
* use external knowledge not provided in input
* output text outside JSON
* include explanations outside JSON

---

## ✅ MUST:

* rely on provided data when available
* say nothing about missing data (just reason with what exists)
* keep output structured and clean
* ensure JSON is valid

---

# 📚 SOURCE USAGE RULES

If legal sources are provided:

* Extract relevant principles
* Use them in reasoning
* Include them in:

  * legal_basis
  * citations

If NO sources are provided:

* Use general legal reasoning
* Set:

  * legal_basis = []
  * citations = []
* Lower confidence

---

# ⚠️ CONFLICT HANDLING

If sources conflict:

* prefer more specific or authoritative sources
* reflect uncertainty in reasoning
* lower confidence

---

# 📉 CONFIDENCE GUIDELINES

* Strong reasoning + multiple sources → 0.8–0.95
* Moderate reasoning + limited sources → 0.5–0.75
* Weak or no sources → ≤ 0.4

---

# 🧠 FINAL BEHAVIOR

You are NOT a chatbot.

You are a:

* legal analyst
* structured reasoning engine
* citation-aware system

Your output must always be:

* precise
* structured
* grounded (if data exists)

---

# 🏁 END OF INSTRUCTIONS

Return ONLY the JSON response.

---

# ✅ Why This Prompt Works

This prompt:

* aligns with your dataset (case → issue → reasoning → judgment) ✅
* enforces **strict structure** ✅
* prevents hallucination ✅
* integrates with **MCP tools + LangGraph** ✅
* supports **with/without retrieval** ✅

---

# ⚠️ One Important Tip

Use this prompt specifically in your:

👉 **Reasoning Node (NOT classifier or planner)**

------------------------------------------------------------------------------



Good—now you’re building the **control layer**, which is just as important as the reasoning model.

I’ll give you **production-ready prompts** for:

* 🧠 Classifier Node
* 🧠 Planner Node

These are designed to:

* work with your dataset
* integrate with LangGraph
* control MCP tools properly
* avoid unnecessary complexity

---

# 🧠 ✅ CLASSIFIER PROMPT (FINAL)

You are a **Legal Intent and Domain Classifier**.

Your task is to analyze a user’s input and determine:

1. The legal **domain**
2. The **intent** of the request
3. Whether external legal data is needed (statutes, case law)

---

# 🎯 OBJECTIVE

Given a user message describing a legal situation, return a structured JSON classification.

---

# 📥 INPUT

You will receive:

* A user message describing a legal issue or question

---

# 📤 OUTPUT FORMAT (STRICT JSON ONLY)

{
"domain": "...",
"intent": "...",
"needs_statutes": true/false,
"needs_cases": true/false
}

---

# 🧾 FIELD DEFINITIONS

## domain

Choose ONE:

* contract_law
* commercial_law
* tort_law
* employment_law
* unknown


---

## intent

Choose ONE:

* legal_analysis (user wants dispute analysis or legal reasoning)
* legal_information (user asks general legal question)
* case_lookup (user asks for similar cases)
* statute_lookup (user asks for laws/regulations)
* company_lookup (user asks about a company)
* unknown

---

## needs_statutes

true if:

* legal rules or laws are needed to answer

false if:

* reasoning alone is sufficient

---

## needs_cases

true if:

* precedents or similar cases would improve answer

false if:

* not necessary

---

# ⚖️ CLASSIFICATION RULES

* If input describes a dispute → intent = legal_analysis
* If input asks “what does law say” → statute_lookup
* If input asks for examples → case_lookup
* If unclear → choose best approximation

---

# 🔒 STRICT RULES

## ❌ DO NOT:

* explain your reasoning
* output text outside JSON
* return multiple domains

---

## ✅ MUST:

* choose the closest valid category
* always return valid JSON

---

# 🏁 OUTPUT ONLY JSON

---

# 🧠 ✅ PLANNER PROMPT (FINAL)

You are a **Legal Query Planner**.

Your role is to decide:

1. Which tools should be used
2. What search queries should be generated

You DO NOT perform legal reasoning.

---

# 🎯 OBJECTIVE

Given:

* the user’s legal input
* classification results

Return a structured plan for tool usage.

---

# 📥 INPUT

You will receive:

* user_input
* domain
* intent
* needs_statutes
* needs_cases

---

# 📤 OUTPUT FORMAT (STRICT JSON ONLY)

{
"tools_to_call": [...],
"queries": [...]
}

---

# 🧾 FIELD DEFINITIONS

## tools_to_call

Choose from:

* "statute_tool"
* "case_law_tool"
* "company_tool"

Rules:

* Include only necessary tools
* Max 2–3 tools

---

## queries

* List of 1–3 search queries
* Each query must be:

  * short
  * relevant
  * keyword-based

---

# ⚙️ PLANNING RULES

## Tool Selection

* If needs_statutes = true → include "statute_tool"
* If needs_cases = true → include "case_law_tool"
* If intent = company_lookup → include "company_tool"

---

## Query Generation

Convert user issue into search-friendly queries:

Examples:

User:
“Client didn’t pay after service”

Queries:

* "breach of contract non payment services"
* "case law failure to pay after performance"

---

User:
“Supplier didn’t deliver goods”

Queries:

* "breach of contract failure to deliver goods"
* "non delivery contract law cases"

---

## Domain Awareness

* contract/commercial → focus on breach, payment, delivery
* tort → negligence, damages

---

# 🔒 STRICT RULES

## ❌ DO NOT:

* perform legal reasoning
* generate long sentences
* include explanations
* output outside JSON

---

## ✅ MUST:

* keep queries concise
* ensure queries match user issue
* return valid JSON only

---

# 🏁 OUTPUT ONLY JSON

---

# ✅ How These Fit Together

Now your system has:

### 🧠 Classifier

* understands the problem

### 🧠 Planner

* decides what to fetch

### 🧠 Reasoner (previous prompt)

* does legal analysis

---

# 🔥 Final Tip

Keep these roles **strictly separated**:

* Classifier → understand
* Planner → decide
* Reasoner → analyze

👉 Mixing them = unstable system

---




----------------------------------------------------------------



Good—this is one of the **most important and most underestimated parts** of your system.

If your aggregator is weak:

* your model gets noisy input
* reasoning quality drops
* hallucination risk increases

If it’s strong:

* your system becomes **reliable and professional**

---

# 🧠 🎯 AGGREGATOR ROLE (CLEAR)

> The Aggregator is responsible for turning raw tool results into **clean, relevant, minimal, high-quality context** for the reasoning model.

---

# 🏗️ 1. INPUT → OUTPUT

## 📥 Input (from MCP tools)

```json
{
  "statutes": [...],
  "cases": [...]
}
```

Each item may include:

* title
* summary
* citation
* source_url
* keywords (optional)

---

## 📤 Output (to Reasoner)

```json
{
  "top_statutes": [...],
  "top_cases": [...],
  "combined_context": "..."
}
```

---

# ⚙️ 2. AGGREGATOR PIPELINE (STEP-BY-STEP)

---

## 🧩 Step 1 — Normalize Data

### 🎯 Goal:

Make all tool outputs consistent

### Actions:

* ensure same fields:

  * title
  * summary
  * citation
  * source
  * source_url
* clean text (remove noise, long headers, etc.)

---

## 🧹 Step 2 — Deduplication

### 🎯 Goal:

Remove repeated or near-duplicate results

### Rules:

* same citation → remove duplicates
* very similar summaries → keep best one

👉 Keep only unique entries

---

## 🎯 Step 3 — Relevance Scoring (CRITICAL)

You score each item based on:

### 🔑 Factors:

1. **Keyword match**

   * overlap with user query
   * overlap with extracted issue

2. **Domain match**

   * contract vs tort vs commercial

3. **Semantic similarity (optional)**

   * meaning similarity

---

## 📊 Example Score

```text
score = 
  0.5 * keyword_match +
  0.3 * domain_match +
  0.2 * semantic_similarity
```

---

## 🧮 Step 4 — Ranking

Sort results by:

* highest relevance score first

---

## ✂️ Step 5 — Filtering (VERY IMPORTANT)

### Hard limits:

* max 3 statutes
* max 2–3 cases
* total ≤ 5 items

---

### Remove:

* vague summaries
* irrelevant domains
* outdated or unclear entries

---

## 🧠 Step 6 — Context Compression

### 🎯 Goal:

Prepare clean input for model

For each item:

* keep:

  * title
  * short summary (1–2 lines)
  * citation

👉 Avoid long legal text

---

# 🧾 3. FINAL OUTPUT FORMAT

```json
{
  "top_statutes": [
    {
      "title": "...",
      "summary": "...",
      "citation": "...",
      "source": "...",
      "source_url": "..."
    }
  ],
  "top_cases": [
    {
      "case_name": "...",
      "summary": "...",
      "citation": "...",
      "court": "...",
      "year": "...",
      "source_url": "..."
    }
  ],
  "combined_context": "Short merged summary of key legal principles"
}
```

---

# 🧠 4. COMBINED CONTEXT (SMART FEATURE)

This is optional but powerful.

### Example:

> “Contract law generally requires performance of agreed obligations. Failure to deliver goods after payment constitutes a material breach, entitling the claimant to restitution or damages.”

👉 This helps the reasoning model:

* faster understanding
* better structured output

---

# ⚠️ 5. CRITICAL RULES

---

## ❌ DO NOT:

* pass raw API responses
* include more than 5 items
* include irrelevant data
* include full legal documents

---

## ✅ MUST:

* keep context concise
* prioritize relevance over quantity
* preserve citation integrity

---

# 🧠 6. EDGE CASE HANDLING

---

## Case 1: No Results Found

```json
{
  "top_statutes": [],
  "top_cases": [],
  "combined_context": ""
}
```

👉 Reasoner will:

* rely on general reasoning
* lower confidence

---

## Case 2: Only Statutes Found

→ pass statutes only
→ empty cases

---

## Case 3: Too Many Weak Results

→ filter aggressively
→ keep only strongest

---

# 🚀 7. PERFORMANCE OPTIMIZATION

---

## ⚡ Techniques

* cache results by query
* reuse previous results in conversation
* limit API calls

---

## ⏱️ Target

* aggregation < 100ms

---

# 🔐 8. QUALITY CONTROL

---

## Add checks:

* missing citation → discard
* missing summary → downgrade score
* duplicate URL → remove

---

# 🧭 9. HOW IT FITS IN SYSTEM

```text
Tools → Aggregator → Clean Context → Reasoner
```

---

# 🔥 FINAL INSIGHT

> The Aggregator is what turns your system from “AI demo” into a **reliable legal assistant**.

Most people skip this—and that’s why their systems fail.




------------------------------------------------------------------------------------------------------------------------



You’ve now reached the **core orchestration layer**—this is where everything connects into a real system.

I’ll give you a **full LangGraph node mapping**, aligned with:

* your prompts (classifier, planner, reasoning)
* MCP tools
* aggregator logic
* structured output

No code—just **clear execution design your developer can implement directly**.

---

# 🧠 🏗️ 1. LANGGRAPH OVERVIEW

This is your final graph:

```text
User Input
   ↓
[Node 1] Input Preprocessor
   ↓
[Node 2] Classifier
   ↓
[Node 3] Planner
   ↓
[Node 4] Tool Executor
   ↓
[Node 5] Aggregator
   ↓
[Node 6] Reasoner (Fine-Tuned Model)
   ↓
[Node 7] Formatter
   ↓
Final Output
```

---

# 🧩 🧠 2. SHARED STATE (VERY IMPORTANT)

All nodes read/write to a shared state object.

## 🧾 State Schema

```json
{
  "user_input": "...",
  "domain": "...",
  "intent": "...",
  "needs_statutes": false,
  "needs_cases": false,
  "tools_to_call": [],
  "queries": [],
  "raw_tool_results": {},
  "aggregated_results": {},
  "final_reasoning": {},
  "final_output": {}
}
```

👉 This is the **backbone of your LangGraph**

---

# 🧩 NODE-BY-NODE DESIGN

---

# 🔹 Node 1 — Input Preprocessor

## 🎯 Purpose

* clean input
* normalize text
* optionally extract key phrases

## Input:

* user_input

## Output:

* cleaned user_input (overwrite state)

---

# 🔹 Node 2 — Classifier Node

## 🧠 Uses:

👉 **Classifier Prompt**

## Input:

* user_input

## Output:

```json
{
  "domain": "...",
  "intent": "...",
  "needs_statutes": true/false,
  "needs_cases": true/false
}
```

## Writes to state:

* domain
* intent
* needs_statutes
* needs_cases

---

# 🔹 Node 3 — Planner Node

## 🧠 Uses:

👉 **Planner Prompt**

## Input:

* user_input
* domain
* intent
* needs_statutes
* needs_cases

## Output:

```json
{
  "tools_to_call": [...],
  "queries": [...]
}
```

## Writes to state:

* tools_to_call
* queries

---

# 🔹 Node 4 — Tool Executor Node

## 🎯 Purpose:

Call MCP tools

## Input:

* tools_to_call
* queries

## Behavior:

* map tool → query
* execute tools (parallel if possible)

---

## Example:

```json
{
  "statute_tool": [...],
  "case_law_tool": [...]
}
```

## Writes to state:

* raw_tool_results

---

# 🔹 Node 5 — Aggregator Node

## 🎯 Purpose:

Clean + rank tool results

## Input:

* raw_tool_results
* user_input
* domain

---

## Actions:

1. normalize
2. deduplicate
3. score relevance
4. rank
5. filter (max 5 items)
6. compress summaries

---

## Output:

```json
{
  "top_statutes": [...],
  "top_cases": [...],
  "combined_context": "..."
}
```

## Writes to state:

* aggregated_results

---

# 🔹 Node 6 — Reasoner Node (CORE)

## 🧠 Uses:

👉 **Full System Prompt (Legal Agent Prompt)**

## Model:

👉 Your **fine-tuned model**

---

## Input:

* user_input
* aggregated_results

---

## Inject into prompt:

```text
User Case:
{user_input}

Relevant Legal Sources:
{top_statutes + top_cases + combined_context}
```

---

## Output:

```json
{
  "domain": "...",
  "issue": "...",
  "answer": "...",
  "legal_reasoning": "...",
  "legal_basis": [...],
  "citations": [...],
  "confidence": 0.0
}
```

---

## Writes to state:

* final_reasoning

---

# 🔹 Node 7 — Formatter Node

## 🎯 Purpose:

Finalize response

---

## Input:

* final_reasoning
* aggregated_results

---

## Actions:

* ensure valid JSON
* attach citations (from tools ONLY)
* compute confidence (if not already done)
* clean formatting

---

## Output:

```json
{
  "domain": "...",
  "issue": "...",
  "answer": "...",
  "legal_reasoning": "...",
  "legal_basis": [...],
  "citations": [...],
  "confidence": 0.0
}
```

---

## Writes to state:

* final_output

---

# 🔄 3. CONDITIONAL FLOW (IMPORTANT)

---

## 🧠 Skip Tool Execution When Not Needed

### Condition:

```text
if needs_statutes == false AND needs_cases == false
```

👉 Skip:

* Planner
* Tool Executor
* Aggregator

👉 Go directly to:

* Reasoner

---

## 🧠 Partial Tool Usage

Example:

* only statutes needed → skip case tool

---

# 🔁 4. MULTI-TURN CONVERSATION (OPTIONAL)

---

## Add Memory Layer

Store:

* previous user_input
* previous outputs

---

## Behavior:

* pass previous context to classifier/planner
* allow follow-up questions

---

# ⚠️ 5. FAILURE HANDLING

---

## Tool Failure

* continue with available data
* log error
* reduce confidence

---

## No Results

* aggregated_results = empty
* reasoner uses general reasoning

---

## Invalid Output

* retry reasoning node
* enforce JSON validation

---

# 🚀 6. PERFORMANCE DESIGN

---

## Parallel Execution

* run tools concurrently

---

## Caching

* cache by query string

---

## Limits

* max 3 queries
* max 5 aggregated results

---

# 🧭 7. FINAL GRAPH SUMMARY

```text
START
 ↓
Input Preprocessor
 ↓
Classifier
 ↓
Planner
 ↓
Tool Executor
 ↓
Aggregator
 ↓
Reasoner
 ↓
Formatter
 ↓
END
```

---

# 🔥 FINAL INSIGHT

This mapping ensures:

* ✅ clean separation of concerns
* ✅ controlled tool usage
* ✅ reliable reasoning
* ✅ structured outputs

---

--------------------------------------------------------------------------------------------------------------


That’s the next important layer.

Right now, you’ve designed a **single-turn legal analysis pipeline**.
For a real product, you also need **conversation state and follow-up handling**.

The main principle is:

> **The conversation is managed by LangGraph state, not by the fine-tuned model.**

Your fine-tuned model should reason about the **current legal problem**, while LangGraph manages what happened earlier.

---

# 🧠 What “follow-up” means here

A follow-up is when the user refers to earlier context instead of restating everything.

Example:

**Turn 1**

> “I paid a deposit but supplier didn’t deliver.”

**Turn 2**

> “What if they refuse to refund?”

Turn 2 depends on turn 1.

---

# 🏗️ Conversation State (recommended)

Extend your shared state.

```json id="28bj2k"
{
  "conversation_id": "...",
  "current_user_input": "...",
  "conversation_history": [],
  "case_memory": {},
  "current_turn": {},
  "final_output": {}
}
```

---

## `conversation_history`

Keep recent turns only (for example last 3–5 turns).

Each turn should contain:

```json id="d9x8uh"
{
  "user": "...",
  "assistant_summary": "...",
  "domain": "...",
  "issue": "..."
}
```

---

## `case_memory`

This is more important than raw chat history.

Store extracted legal facts.

Example:

```json id="d32obm"
{
  "parties": {
    "claimant": "user",
    "defendant": "supplier"
  },
  "facts": [
    "deposit paid",
    "goods not delivered"
  ],
  "domain": "contract_law",
  "issue": "breach of delivery obligation"
}
```

---

# Why this matters

Legal follow-ups usually depend on **facts**, not full chat transcripts.

That makes reasoning cleaner and more stable.

---

# Recommended follow-up flow

---

## Step 1 — Detect whether it is a follow-up

Add a small **follow-up detector** before classifier.

### Detect if user message contains:

* pronouns:

  * “they”
  * “that”
  * “it”
* short contextual questions:

  * “what now?”
  * “can I sue?”
  * “what if they refuse?”

---

## If YES

Inject relevant memory.

---

## If NO

Treat as a new legal problem.

---

# Updated conversation flow

```text id="4f2br4"
User Input
   ↓
Follow-up Detector
   ↓
Context Resolver
   ↓
Classifier
   ↓
Planner
   ↓
Tools
   ↓
Aggregator
   ↓
Reasoner
   ↓
Formatter
```

---

# Context Resolver Node

This is important.

Its job:

* decide which previous facts matter
* prepare clean context for downstream nodes

---

## Example

### Previous facts:

* supplier
* deposit paid
* goods not delivered

### New input:

> “What if they refuse to refund?”

Resolved context:

```text id="cvpw0r"
Supplier received deposit.
Supplier failed to deliver goods.
User asks about refusal to refund after non-delivery.
```

---

# What gets passed to classifier

Not just the latest message.

Pass:

* current message
* resolved prior facts

That helps classifier understand the real issue.

---

# What gets passed to planner

The planner should also see resolved context.

Otherwise it may search badly.

Bad query:

> “refuse refund”

Better query:

> “supplier refuses refund after failure to deliver goods”

---

# What gets passed to reasoner

The reasoner should receive:

* current user question
* relevant prior facts
* retrieved legal sources

---

# When to update memory

After **final output**, update:

* conversation history
* case memory

---

## Save only durable facts

Good:

* deposit paid
* delivery failed
* payment withheld

Not useful:

* wording style
* repeated phrasing
* irrelevant chat

---

# Recommended memory policy

Keep:

### stable legal facts

### current issue

### current domain

### key entities

---

# Memory pruning

When conversation gets long:

* keep **case facts**
* summarize old turns
* discard verbose history

---

# Important design rule

Do **not** pass entire chat history into the reasoner.

Instead pass:

> **resolved legal facts + current user question**

That is much better.

---

# Example full conversation

---

## Turn 1

User:

> “I paid a deposit and supplier didn’t deliver machinery.”

System stores:

* deposit paid
* supplier failed to deliver
* contract dispute

---

## Turn 2

User:

> “What if they refuse to refund?”

Follow-up detector → yes

Context resolver builds:

* supplier received deposit
* failed to deliver
* user asks about refusal to refund

Planner searches:

* breach of contract refund after non-delivery
* restitution after failure to deliver goods

Reasoner answers.

---

# Edge case: new issue mid-conversation

Example:

> “Also I had a traffic accident yesterday.”

That is not a follow-up.

Then:

* start new case memory
* new domain
* new analysis

---

# Practical recommendation

For MVP:

Implement only:

### 1. follow-up detector

### 2. case memory

### 3. context resolver

That’s enough.

You do **not** need complicated memory systems at first.

---

# Recommended new LangGraph nodes

Add two nodes before classifier:

---

## Follow-up Detector

Outputs:

```json id="i2avj7"
{
  "is_follow_up": true
}
```

---

## Context Resolver

Outputs:

```json id="x08whm"
{
  "resolved_context": "...",
  "active_case_memory": {...}
}
```

---

# Final production flow

```text id="rw9sr3"
User Input
   ↓
Follow-up Detector
   ↓
Context Resolver
   ↓
Classifier
   ↓
Planner
   ↓
Tool Executor
   ↓
Aggregator
   ↓
Reasoner
   ↓
Formatter
   ↓
Memory Updater
```

---

# Best way to think about it

* **LangGraph remembers**
* **tools retrieve**
* **fine-tuned model reasons**

That separation will keep your system stable.

---
-------------------------------------------------------------------------------------------------------------------------



Good. The follow-up detector should be **small, strict, and cheap**.

Its job is **not legal reasoning**.
It only decides:

> **Does this user message depend on earlier conversation context?**

That’s all.

---

# Follow-up Detector Prompt (production-ready)

You are a **Conversation Follow-Up Detector** for a legal AI system.

Your task is to determine whether the current user message depends on prior conversation context.

You do NOT perform legal analysis.

You do NOT classify legal domain.

You only detect whether previous conversation facts are needed to correctly understand the user’s message.

---

# Objective

Given:

* current user message
* optional recent conversation context

Determine whether the message is:

* a follow-up to earlier conversation, or
* a new standalone legal issue

---

# Input

You may receive:

* current_user_input
* recent_conversation_summary (optional)

---

# Output (STRICT JSON ONLY)

{
"is_follow_up": true,
"reason": "..."
}

---

# Field Definitions

## is_follow_up

* true → previous conversation facts are required
* false → current message is understandable on its own

---

## reason

Choose one short label only:

* pronoun_reference
* contextual_reference
* short_follow_up
* new_issue
* standalone

---

# Decision Rules

Mark **is_follow_up = true** if the current message contains:

### Pronoun references

Examples:

* they
* he
* she
* it
* that
* those

Example:
“What if they refuse to refund?”

---

### Contextual references

Examples:

* in that case
* what now
* then what
* can I sue now
* what happens next
* does that matter

---

### Very short follow-up questions

Examples:

* what now?
* can I sue?
* what if not?

If prior context is required to understand the meaning, mark true.

---

# Mark is_follow_up = false when:

### The user introduces a new legal issue

Examples:

* “My supplier failed to deliver goods.”
* “I had a traffic accident yesterday.”
* “Can an employer terminate a contract without notice?”

These are understandable without prior context.

---

# Important Rules

## DO NOT:

* perform legal reasoning
* infer legal outcome
* classify domain
* use long explanations

---

## MUST:

* use only the current message and optional recent context
* return valid JSON only
* keep reason short and categorical

---

# Examples

Input:
“What if they refuse to refund?”

Output:
{
"is_follow_up": true,
"reason": "pronoun_reference"
}

---

Input:
“Can I sue now?”

Output:
{
"is_follow_up": true,
"reason": "short_follow_up"
}

---

Input:
“My supplier accepted payment and never delivered.”

Output:
{
"is_follow_up": false,
"reason": "standalone"
}

---

Input:
“I had a vehicle accident yesterday.”

Output:
{
"is_follow_up": false,
"reason": "new_issue"
}

---

Return ONLY JSON.

---

# Recommended implementation note

Run this **before the classifier**.

Flow:

```text
User Input
   ↓
Follow-up Detector
   ↓
(if true)
Context Resolver
   ↓
Classifier
```

---

# Practical tip

For this node, use a **small fast model**.
No need to spend expensive reasoning tokens here.

---
-----------------------------------------------------------------------------------------------------------------------------------


