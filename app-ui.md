Yes. Here’s a **practical ChatGPT-like UI design** for your legal agent that fits the system you described.

# Product goal

A user should be able to:

* describe a legal situation naturally
* answer follow-up questions when facts are missing
* receive a structured legal analysis
* inspect statutes, cases, and sources

The UI should feel simple, but support legal trust and traceability.

---

# Main layout

## Left sidebar

### Conversations

Recent chats, for example:

* Supplier deposit dispute
* Employment termination question
* Vehicle lease payment dispute

### New chat button

Starts a new legal consultation.

---

## Center panel

This is the main chat thread.

It should behave like a normal chat app.

---

## Bottom composer

Large input box.

Placeholder example:

> Describe your legal issue. Include the relevant facts, dates, and what happened.

Optional helper text:

> This system provides legal information and analysis, not legal representation.

---

# Message flow

## User message

Natural language.

Example:

> A supplier accepted a deposit and failed to deliver machinery. They have not refunded the money.

---

## Assistant follow-up (only when needed)

The system should ask **only missing facts that materially affect analysis**.

Example:

> Was there a written contract?
>
> Was a delivery date specified?
>
> Did the supplier provide any reason for non-delivery?

Keep follow-up short and targeted.

---

## Final legal answer

Each assistant answer should stay chat-like but structured.

Recommended message structure:

### Detected domain

`contract_law`

### Legal issue

Short issue statement.

### Analysis

Clear legal reasoning in normal language.

### Likely outcome

Concise practical answer.

### Legal basis

Relevant statutes, principles, and cases.

### Sources

Expandable citations.

---

# Sources UI

This is important.

At the bottom of each legal answer:

**Sources used (3)**

When expanded, show:

* statute title
* section citation
* case citation
* source URL

Example:

* 29 U.S.C. § 201
* *Smith v. Jones*, 2023
* govinfo source

Keep this compact.

---

# Conversation behavior

## Follow-up awareness

The system should remember conversation context.

Example:

User:

> It was a written agreement.

Then later:

> The delivery date was June 1.

The backend should treat this as continuation of the same matter.

No need to restate everything.

---

# Suggested message types

## 1. Clarification message

Short factual question.

---

## 2. Retrieval notice (optional)

Small subtle status:

> Searching relevant statutes and cases…

Good for perceived transparency.

---

## 3. Final legal analysis

Main structured answer.

---

# Recommended left sidebar behavior

Each conversation title should be auto-generated.

Examples:

* Late delivery dispute
* Lease-to-own default
* Final salary withholding

That makes the product feel polished.

---

# Minimal first-version UI

For first release, I would build only this:

## Required

* sidebar
* chat thread
* input
* follow-up messages
* legal answer sections
* citations

## Not needed yet

* document upload
* multi-agent controls
* workflow panels
* dashboards
* analytics
* legal workspace management

---

# Recommended UX rules

## Keep answers readable

Avoid giant blocks of legal prose.

Use short sections.

---

## Ask fewer follow-ups

Only when missing facts materially change the legal analysis.

---

## Show sources only after answer

Don’t overwhelm users first.

---

# Best user journey

```text
New chat
   ↓
User describes dispute
   ↓
Follow-up if needed
   ↓
Retrieve laws + cases
   ↓
Legal reasoning
   ↓
Structured answer + citations
```

That fits your LangGraph architecture cleanly.

---

# My practical product recommendation

For your current stage, I would ship:

> **ChatGPT-style legal research assistant for business disputes**


-----------------------------------------------------------------------------------------------




For legal workflows, showing **process visibility** helps users understand *why* the answer is trustworthy.

A good design is **progress visibility**, not raw internal chain-of-thought.

# What I recommend showing

Show **workflow events**.

Good examples:

* analyzing legal issue
* detecting domain
* planning research
* searching statutes
* retrieving case law
* aggregating sources
* preparing legal analysis

That gives transparency without exposing hidden internal reasoning.

---

# Recommended chat behavior

When the user submits a message:

## Step 1 — temporary status card appears

Inside the chat thread, show a small live activity block.

Example:

```text id="z0dd8n"
Analyzing legal issue...
```

Then update it as work progresses.

---

# Good UX pattern

Instead of a long “thinking…” spinner, use **progressive steps**.

Example:

```text id="o7snto"
✓ Domain detected: contract_law
✓ Planning legal research
✓ Searching statutes
✓ Searching case law
✓ Aggregating sources
… Preparing final analysis
```

That feels much better.

---

# What tool names to show

You can show friendly names.

Examples:

* statute search
* case law search
* legislation search
* company lookup

That is better than exposing raw internal implementation details.

---

# Better than raw tool names

Instead of:

> `govinfo_tool()`

Show:

> Searching federal statutes

Instead of:

> `courtlistener_search()`

Show:

> Retrieving relevant cases

That is more user-friendly.

---

# My recommended event model

For your architecture:

## Classifier node

Show:

> Detecting legal domain

---

## Planner node

Show:

> Planning legal research

---

## GovInfo retrieval

Show:

> Searching statutes

---

## CourtListener retrieval

Show:

> Searching relevant cases

---

## Aggregator

Show:

> Consolidating legal sources

---

## Reasoner

Show:

> Preparing legal analysis

---

# How it should appear in chat

### User message

> supplier kept my deposit and failed to deliver

---

### Assistant activity card

```text id="1l4nrt"
Detecting legal domain...
Searching statutes...
Searching cases...
Preparing legal analysis...
```

---

### Final assistant response

Structured legal answer.

That is a very good experience.

---

# Small UI recommendation

Make the activity card **collapsible**.

Default:

> Working…

Expanded:

* detected domain
* sources used
* steps completed

That keeps chat clean.

---

# Important design recommendation

Do **not** expose:

* hidden chain-of-thought
* raw prompt text
* internal reasoning tokens
* internal deliberation

Expose **process steps**, not private reasoning traces.

That is the best design.

---

# My practical recommendation

For your legal product, I would absolutely include this.

It makes the system feel:

* active
* trustworthy
* tool-driven
* transparent

Especially for legal use.

---

# My favorite simple version

Minimal but very good:

```text id="8s8drp"
Analyzing issue
Searching statutes
Searching cases
Preparing answer
```

-----------------------------------------------------------------------------------------------------------------

Yes — here’s a **concrete streaming chat UX** that fits your legal agent.

The goal is:

> **make the user see the system working in real time** while keeping the interface clean and trustworthy.

---

# Core interaction model

The chat should have **three live phases**:

```text id="v1xg5a"
user message
   ↓
live workflow activity
   ↓
streamed final legal answer
```

That is the simplest strong version.

---

# 1. User sends a legal question

Example:

> A supplier accepted a deposit and failed to deliver machinery. They are refusing to refund the money.

The user message appears immediately.

---

# 2. Live workflow card appears

Directly below the user message.

This is not the final answer yet.

It is a temporary assistant activity card.

---

## Recommended collapsed state

```text id="dpr76i"
Working…
```

---

## Expanded state

Show live steps as they happen.

Example:

```text id="9b59qp"
✓ Detecting legal domain
✓ Planning legal research
✓ Searching statutes
✓ Searching relevant cases
✓ Consolidating sources
… Preparing legal analysis
```

Only one current step should be active.

Completed steps get a check.

---

# 3. Timing behavior

## Fast nodes

Classifier / planner usually complete quickly.

Those can update almost immediately.

---

## Retrieval nodes

These should remain visible longer.

Users should be able to see:

* searching
* fetching
* consolidating

That gives trust.

---

# 4. Optional source preview during retrieval

Very useful.

As tools finish, show compact source pills.

Example:

```text id="vuk6yn"
Sources found:
29 U.S.C. § 201
Smith v. Jones (2023)
```

These can appear progressively.

Not full citations yet.

---

# 5. Transition to final answer

When reasoning starts:

The activity card stays above.

Then the final assistant message begins streaming underneath.

---

# Recommended pattern

```text id="f0b5u0"
✓ Detecting legal domain
✓ Planning legal research
✓ Searching statutes
✓ Searching relevant cases
✓ Consolidating sources
✓ Preparing legal analysis
```

Then the answer starts.

---

# 6. Stream the final answer in sections

Do **not** dump one large block.

Stream structured sections progressively.

---

## First

### Detected domain

`contract_law`

---

## Then

### Legal issue

One short sentence.

---

## Then

### Analysis

Main reasoning body.

This can stream token-by-token.

---

## Then

### Legal basis

List of statutes / principles / cases.

---

## Then

### Sources

Expandable source block.

---

# Why section streaming is better

It gives users useful information early.

They don’t have to wait for the entire response.

---

# 7. Source rendering

At the bottom of the final answer:

## Compact default

```text id="fquf2g"
Sources used (3)
```

---

## Expanded

Show:

* statute title
* citation
* court
* source link

Example:

* 29 U.S.C. § 201
* *Smith v. Jones*, 2023
* GovInfo source

---

# 8. Follow-up handling

If facts are insufficient:

The reasoning phase should **not** start.

Instead:

---

## Workflow card

```text id="9tswz2"
✓ Detecting legal domain
✓ Evaluating available facts
```

---

## Assistant asks follow-up

> Was there a written contract?
>
> Was a delivery date specified?

Then wait.

---

# 9. Follow-up continuation

When the user answers:

The system should continue from prior context.

Do **not** restart the conversation.

New live card appears:

```text id="up4g9f"
✓ Updating case facts
✓ Searching statutes
✓ Searching relevant cases
… Preparing legal analysis
```

That feels natural.

---

# 10. Recommended UI behavior for tool visibility

I recommend **human-readable tool labels**, not raw backend names.

Use:

* Detecting legal domain
* Searching statutes
* Searching relevant cases
* Consolidating sources

Avoid raw internal identifiers.

---

# 11. Suggested micro-interactions

## While waiting

Subtle animated dots.

---

## Step completion

Instant checkmark.

---

## Final transition

Activity card remains visible but becomes muted.

That gives process traceability.

---

# 12. Full example

## User

> A supplier took a deposit and failed to deliver machinery.

---

## Activity

```text id="yyof96"
✓ Detecting legal domain
✓ Planning legal research
✓ Searching statutes
✓ Searching relevant cases
✓ Consolidating sources
… Preparing legal analysis
```

---

## Streamed answer

### Detected domain

`contract_law`

### Legal issue

Whether the supplier’s failure to deliver after accepting a deposit constitutes breach of contract requiring restitution.

### Analysis

(streaming...)

### Legal basis

* contract performance obligations
* restitution after non-performance
* damages principles

### Sources

Sources used (3)

---

# My strongest recommendation

For your product:

> **stream workflow events first, then stream structured legal answer**

That is probably the best UX.

It feels modern, clear, and trustworthy.

---------------------------------------------------------------------------------------------------------

Yes — here’s a **practical frontend event architecture** that fits your legal agent.

The goal is simple:

> **LangGraph emits structured events → frontend renders live chat updates**

That gives you streaming progress, tool visibility, and final answers without making the UI messy.

---

# Core idea

Think of the backend as emitting **event objects**, not raw text.

The frontend listens to events and updates the current assistant message.

---

# Event flow

```text id="0m24cw"
user sends message
    ↓
backend starts run
    ↓
node events stream
    ↓
tool events stream
    ↓
final answer tokens stream
    ↓
run completes
```

---

# Recommended transport

For a web chat UI, I recommend:

**Server-Sent Events (SSE)**

Why:

* simple
* lightweight
* perfect for one-way streaming
* easy to manage in chat interfaces

That is usually cleaner than WebSockets for this kind of product.

---

# Event types

Use a small, stable event schema.

---

## 1. `run_started`

Sent once.

Example meaning:

> a new legal reasoning run has started

Frontend behavior:

* create assistant placeholder
* create activity card

---

## 2. `step_started`

Represents LangGraph node start.

Examples:

* classifier
* planner
* retrieval
* aggregator
* reasoner

Frontend behavior:

* show active current step

---

## 3. `step_completed`

Represents node completion.

Frontend behavior:

* mark step complete
* checkmark

---

## 4. `tool_started`

Tool execution begins.

Examples:

* statute search
* case law search
* legislation search

Frontend behavior:

* append tool activity line

---

## 5. `tool_result`

Tool produced structured results.

Frontend behavior:

* update source preview
* store retrieval payload

---

## 6. `answer_started`

Reasoner begins final response.

Frontend behavior:

* create final assistant answer area

---

## 7. `answer_delta`

Token stream.

Frontend behavior:

* append streamed text

---

## 8. `followup_requested`

Missing facts detected.

Frontend behavior:

* stop pipeline
* render clarification question

---

## 9. `run_completed`

Run finished.

Frontend behavior:

* freeze activity card
* finalize citations

---

# Recommended frontend state model

The frontend should keep **one active run state**.

Suggested structure:

```text id="c1t2eh"
chat
 ├─ messages
 ├─ active_run
 │    ├─ steps
 │    ├─ tool_results
 │    ├─ streamed_answer
 │    └─ status
```

---

# Assistant message structure

I recommend treating one assistant turn as **two linked UI objects**.

---

## Activity card

Temporary live workflow state.

---

## Final assistant answer

The actual legal answer.

That separation makes the UI much cleaner.

---

# Exact rendering behavior

---

## `run_started`

Create:

* pending assistant activity card

---

## `step_started`

Set current active step.

Example:

```text id="qzx9f6"
… Searching statutes
```

---

## `step_completed`

Mark complete:

```text id="0m0v4o"
✓ Searching statutes
```

---

## `tool_result`

Update source preview.

Example:

```text id="4z6t8u"
Sources found:
29 U.S.C. § 201
Smith v. Jones
```

---

## `answer_started`

Create assistant message shell.

---

## `answer_delta`

Append streamed tokens.

---

## `run_completed`

Lock final UI.

---

# Recommended step mapping from your LangGraph

## classifier node

Event label:

> Detecting legal domain

---

## planner node

Event label:

> Planning legal research

---

## GovInfo tool

Event label:

> Searching statutes

---

## CourtListener tool

Event label:

> Searching relevant cases

---

## aggregator node

Event label:

> Consolidating legal sources

---

## reasoner node

Event label:

> Preparing legal analysis

---

# Suggested frontend lifecycle

---

## User submits

Immediate optimistic user message.

---

## Backend emits `run_started`

Assistant activity card appears.

---

## Steps update live

Progressive completion.

---

## Answer streams

Structured response appears.

---

## Sources finalize

Citations attach.

---

# Important design rule

The frontend should **never infer legal logic itself**.

It should only render backend events.

Meaning:

* no local planner
* no local domain detection
* no local source ranking

Frontend is presentation only.

That keeps architecture clean.

---

# Recommended failure behavior

If retrieval fails:

Emit a tool failure event.

Frontend can show:

> Case law retrieval unavailable. Continuing with available sources.

That is much better than silent failure.

---

# Recommended follow-up behavior

If backend emits `followup_requested`:

Frontend should:

* freeze current run
* keep activity trace visible
* render assistant clarification message
* wait for user reply
* new run continues from prior conversation state

---

# My practical architecture recommendation

For your demo:

## Frontend

* Next.js
* React

## Transport

* SSE

## Backend

* LangGraph orchestrator

That is a very clean stack.

---

# Simple mental model

Think of it like this:

> **LangGraph produces events.**
>
> **Frontend renders them as live conversation state.**

That’s the whole architecture.

-------------------------------------------------------------------------------------------------
Yes — this is the piece that makes the whole system clean.

The best way is to make **LangGraph emit a stable event protocol** that the frontend consumes over SSE.

---

# Backend event contract

## Transport

Use **Server-Sent Events (SSE)**.

Response headers:

* `Content-Type: text/event-stream`
* `Cache-Control: no-cache`
* `Connection: keep-alive`

Each event should contain:

* `event` → event type
* `data` → JSON payload

---

# Core envelope

Every backend event should share the same top-level fields.

```json
{
  "run_id": "uuid",
  "conversation_id": "uuid",
  "timestamp": "ISO-8601",
  "event": "event_name",
  "payload": {}
}
```

---

# Required event types

---

## 1. `run_started`

Emitted once at the beginning.

### Purpose

Create assistant activity state.

### Payload

```json
{
  "user_message_id": "msg_001",
  "query": "Can a supplier keep my deposit after failing to deliver machinery?"
}
```

---

## 2. `step_started`

Emitted when a LangGraph node starts.

### Payload

```json
{
  "step_id": "step_01",
  "node": "classifier",
  "label": "Detecting legal domain"
}
```

---

## 3. `step_completed`

Emitted when a node completes.

### Payload

```json
{
  "step_id": "step_01",
  "node": "classifier",
  "status": "completed",
  "duration_ms": 84
}
```

---

## 4. `step_output`

Use this only for **structured internal outputs** that may help UI/debugging.

### Example — classifier result

```json
{
  "step_id": "step_01",
  "node": "classifier",
  "output": {
    "domain": "contract_law",
    "intent": "legal_analysis"
  }
}
```

Frontend can hide this by default.

---

# Tool events

---

## 5. `tool_started`

### Payload

```json
{
  "tool_call_id": "tool_001",
  "tool_name": "govinfo_statute_search",
  "label": "Searching statutes",
  "input": {
    "query": "deposit refund supplier non-delivery"
  }
}
```

---

## 6. `tool_result`

### Purpose

Return structured retrieval results.

### Payload

```json
{
  "tool_call_id": "tool_001",
  "tool_name": "govinfo_statute_search",
  "result_count": 2,
  "results": [
    {
      "title": "Uniform Commercial Code",
      "citation": "UCC § 2-711",
      "summary": "Buyer remedies for seller non-delivery",
      "source_url": "https://..."
    }
  ]
}
```

---

## 7. `tool_failed`

### Payload

```json
{
  "tool_call_id": "tool_001",
  "tool_name": "courtlistener_case_search",
  "error": "timeout",
  "recoverable": true
}
```

Frontend should show non-blocking warning.

---

# Aggregation events

---

## 8. `sources_aggregated`

Emitted after retrieval merge.

### Payload

```json
{
  "statutes": 2,
  "cases": 3,
  "deduplicated_total": 4
}
```

This gives useful transparency.

---

# Answer streaming

---

## 9. `answer_started`

Emitted before token streaming.

### Payload

```json
{
  "message_id": "assistant_001"
}
```

---

## 10. `answer_delta`

Token stream.

### Payload

```json
{
  "message_id": "assistant_001",
  "delta": "The defendant is likely liable for breach of contract"
}
```

Frontend appends tokens.

---

## 11. `answer_completed`

Emitted once final structured answer is ready.

### Payload

```json
{
  "message_id": "assistant_001",
  "final": {
    "domain": "contract_law",
    "issue": "Whether the supplier must refund the deposit after non-delivery.",
    "answer": "The supplier is likely required to refund the deposit.",
    "legal_reasoning": "The supplier accepted payment and failed to deliver the contracted goods.",
    "legal_basis": [
      "buyer remedies for non-delivery",
      "restitution after breach"
    ],
    "citations": [
      {
        "title": "UCC § 2-711",
        "source_url": "https://..."
      }
    ],
    "confidence": 0.84
  }
}
```

This is the most important event.

---

# Follow-up events

---

## 12. `followup_requested`

Used when the system lacks facts.

### Payload

```json
{
  "question": "Was there a written delivery deadline in the contract?",
  "missing_fields": [
    "delivery_deadline"
  ]
}
```

Frontend pauses run and asks user.

---

# Completion event

---

## 13. `run_completed`

Sent once.

### Payload

```json
{
  "status": "completed",
  "duration_ms": 2140
}
```

---

# Recommended LangGraph node → event mapping

| LangGraph node | Emits                                              |
| -------------- | -------------------------------------------------- |
| classifier     | step_started → step_output → step_completed        |
| planner        | step_started → step_output → step_completed        |
| tool executor  | tool_started → tool_result / tool_failed           |
| aggregator     | step_started → sources_aggregated → step_completed |
| reasoner       | answer_started → answer_delta → answer_completed   |
| finalizer      | run_completed                                      |

---

# Recommended backend rule

**Every event must be append-only.**

Never mutate prior events.

That gives:

* reliable replay
* easy debugging
* stable frontend rendering

---

# Practical frontend rule

The frontend should render based only on:

* ordered event stream
* `run_id`

No hidden client-side assumptions.

---

# Recommended production addition

Include sequence numbers.

Add this to every event:

```json
{
  "seq": 14
}
```

That helps with ordering and reconnect recovery.

---

# My recommendation for your legal system

For your app, I would use exactly **13 events only**.

That is enough.

Do not add more now.

Keep the protocol small and stable.

---

## Best mental model

Think of it like this:

> **LangGraph is an event producer.**
>
> **Frontend is an event renderer.**

That separation will make your system much easier to build.


-----------------------------------------------------------------------------------------
Yes — this is the internal object that every node reads and updates.

Think of it as the **single shared legal workflow state**.

---

# LangGraph runtime state schema

Use **one canonical state object**.

```json id="81006"
{
  "run_id": "uuid",
  "conversation_id": "uuid",
  "user_input": "",
  "followup_context": null,
  "classification": {},
  "plan": {},
  "retrieval": {},
  "aggregation": {},
  "reasoning": {},
  "output": {},
  "meta": {}
}
```

---

# 1. identity

Runtime metadata.

```json id="73843"
{
  "run_id": "uuid",
  "conversation_id": "uuid"
}
```

---

# 2. user_input

Raw current user request.

```json id="68388"
{
  "user_input": "Can a supplier keep my deposit after failing to deliver machinery?"
}
```

This should always remain unchanged.

---

# 3. followup_context

Used only when the user is answering a clarification question.

```json id="71622"
{
  "followup_context": {
    "previous_run_id": "run_001",
    "missing_fields": [
      "delivery_deadline"
    ],
    "answers": {
      "delivery_deadline": "June 10, 2025"
    }
  }
}
```

If not used:

```json id="60941"
null
```

---

# 4. classification

Output of classifier node.

```json id="39281"
{
  "classification": {
    "domain": "contract_law",
    "intent": "legal_analysis",
    "confidence": 0.91
  }
}
```

---

## Recommended intent values

Use a small fixed set:

* `legal_analysis`
* `statute_lookup`
* `case_lookup`
* `legislation_lookup`
* `company_lookup`
* `followup_required`

Do not make this open-ended.

---

# 5. plan

Output of planner node.

Defines what tools should run.

```json id="37306"
{
  "plan": {
    "tool_calls": [
      {
        "tool_name": "govinfo_statute_search",
        "query": "deposit refund non-delivery machinery"
      },
      {
        "tool_name": "courtlistener_case_search",
        "query": "breach of delivery contract deposit refund"
      }
    ],
    "parallel": true
  }
}
```

---

# 6. retrieval

Raw tool outputs.

Store tool results exactly once.

```json id="64383"
{
  "retrieval": {
    "govinfo_statute_search": [
      {
        "title": "Uniform Commercial Code",
        "citation": "UCC § 2-711",
        "summary": "Buyer remedies for seller non-delivery",
        "source_url": "https://..."
      }
    ],
    "courtlistener_case_search": [
      {
        "case_name": "Smith v. Supplier",
        "citation": "123 F.3d 456",
        "court": "9th Cir.",
        "year": 2021,
        "summary": "Failure to deliver required restitution",
        "source_url": "https://..."
      }
    ]
  }
}
```

---

# 7. aggregation

Normalized retrieval context for reasoner.

This is very important.

The reasoner should **not consume raw tool outputs directly**.

Use aggregated structured context.

```json id="89341"
{
  "aggregation": {
    "legal_sources": [
      {
        "type": "statute",
        "title": "UCC § 2-711",
        "summary": "Buyer remedies for non-delivery",
        "source_url": "https://..."
      },
      {
        "type": "case",
        "title": "Smith v. Supplier",
        "summary": "Restitution after breach",
        "source_url": "https://..."
      }
    ],
    "retrieval_summary": "Two statutes and one relevant case support buyer restitution."
  }
}
```

---

# 8. reasoning

Internal reasoning payload passed to the reasoner node.

```json id="84958"
{
  "reasoning": {
    "case_facts": "supplier accepted deposit and failed to deliver machinery",
    "legal_issue": "whether seller must refund deposit after non-delivery",
    "reasoning_context": [
      "buyer remedies",
      "breach of contract",
      "restitution"
    ]
  }
}
```

This is internal working context.

Not final output.

---

# 9. output

Final user-facing answer.

```json id="25328"
{
  "output": {
    "domain": "contract_law",
    "issue": "Whether the supplier must refund the deposit after non-delivery.",
    "answer": "The supplier is likely required to refund the deposit.",
    "legal_reasoning": "The supplier accepted payment and failed to deliver the contracted goods.",
    "legal_basis": [
      "buyer remedies for non-delivery",
      "restitution after breach"
    ],
    "citations": [
      {
        "title": "UCC § 2-711",
        "source_url": "https://..."
      }
    ],
    "confidence": 0.84
  }
}
```

This is what gets streamed to the frontend.

---

# 10. meta

Execution metadata.

```json id="93524"
{
  "meta": {
    "created_at": "ISO-8601",
    "started_at": "ISO-8601",
    "completed_at": "ISO-8601",
    "status": "running"
  }
}
```

---

# Recommended state mutation rules

These are important.

---

## classifier

May only write:

* `classification`

---

## planner

May only write:

* `plan`

---

## tools

May only write:

* `retrieval`

---

## aggregator

May only write:

* `aggregation`

---

## reasoner

May only write:

* `reasoning`
* `output`

---

## runtime manager

May only write:

* `meta`

---

# Best architectural rule

**Earlier nodes should never overwrite later nodes.**

That keeps graph execution predictable.

---

# Recommended execution path

```text id="53733"
user_input
   ↓
classification
   ↓
plan
   ↓
retrieval
   ↓
aggregation
   ↓
reasoning
   ↓
output
```

That should be your canonical pipeline.

---

# Why this schema fits your fine-tuned dataset

Your dataset already naturally maps to:

* **case** → `user_input`
* **domain** → `classification.domain`
* **issue** → `reasoning.legal_issue`
* **reasoning** → `output.legal_reasoning`
* **judgment** → `output.answer`

That is why your dataset is a good fit.

---

# My recommendation

For your legal agent, **do not make the state larger right now**.

This schema is enough for:

* fine-tuned legal reasoning
* tool orchestration
* streaming UI
* follow-up handling
* citations

