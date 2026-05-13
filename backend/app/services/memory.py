"""In-memory conversation and case memory store."""

from __future__ import annotations
from typing import Optional
import uuid
from datetime import datetime, timezone
from app.models.state import CaseMemory, ConversationTurn


class ConversationStore:
    """
    Simple in-memory store for conversation history and case memory.
    In production, replace with Redis/PostgreSQL.
    """

    def __init__(self):
        self._conversations: dict[str, dict] = {}

    def create_conversation(self, conversation_id: Optional[str] = None) -> str:
        """Create a new conversation and return its ID."""
        cid = conversation_id or str(uuid.uuid4())
        self._conversations[cid] = {
            "id": cid,
            "title": "New Conversation",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "history": [],           # list[ConversationTurn]
            "case_memory": {},       # CaseMemory
            "messages": [],          # raw message log for UI
            "clarification_count": 0,  # tracks multi-turn rounds
        }
        return cid

    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        """Get conversation by ID."""
        return self._conversations.get(conversation_id)

    def list_conversations(self) -> list[dict]:
        """List all conversations (most recent first)."""
        convos = list(self._conversations.values())
        convos.sort(key=lambda c: c["created_at"], reverse=True)
        return [
            {
                "id": c["id"],
                "title": c["title"],
                "created_at": c["created_at"],
                "message_count": len(c["messages"]),
            }
            for c in convos
        ]

    def get_history(self, conversation_id: str) -> list[ConversationTurn]:
        """Get conversation turn history (last 5)."""
        convo = self._conversations.get(conversation_id)
        if not convo:
            return []
        return convo["history"][-5:]

    def get_case_memory(self, conversation_id: str) -> CaseMemory:
        """Get the active case memory for a conversation."""
        convo = self._conversations.get(conversation_id)
        if not convo:
            return {}
        return convo.get("case_memory", {})

    def get_clarification_count(self, conversation_id: str) -> int:
        """Get the number of clarification rounds so far."""
        convo = self._conversations.get(conversation_id)
        if not convo:
            return 0
        return convo.get("clarification_count", 0)

    def update_after_clarification(
        self,
        conversation_id: str,
        user_input: str,
        question: str,
        case_memory: Optional[CaseMemory] = None,
        title: Optional[str] = None,
    ):
        """Update conversation after a clarification round (early termination)."""
        convo = self._conversations.get(conversation_id)
        if not convo:
            return

        # Increment clarification counter
        convo["clarification_count"] = convo.get("clarification_count", 0) + 1

        # Append turn with clarification marker
        turn: ConversationTurn = {
            "user": user_input,
            "assistant_summary": f"[Clarification] {question}",
            "domain": "",
            "issue": "",
        }
        convo["history"].append(turn)

        # Accumulate case memory facts
        if case_memory:
            existing = convo.get("case_memory", {})
            existing_facts = existing.get("facts", [])
            new_facts = case_memory.get("facts", [])
            # Merge facts without duplicates
            merged_facts = list(dict.fromkeys(existing_facts + new_facts))
            convo["case_memory"] = {
                **existing,
                **case_memory,
                "facts": merged_facts,
            }

        # Update title (from first query)
        if title and convo["title"] == "New Conversation":
            convo["title"] = title

        # Store raw messages for UI
        convo["messages"].append({"role": "user", "content": user_input})
        convo["messages"].append({
            "role": "assistant",
            "content": {"type": "clarification", "question": question},
        })

    def update_after_run(
        self,
        conversation_id: str,
        user_input: str,
        output: dict,
        case_memory: Optional[CaseMemory] = None,
        title: Optional[str] = None,
    ):
        """Update conversation after a completed run."""
        convo = self._conversations.get(conversation_id)
        if not convo:
            return

        # Reset clarification counter on successful full run
        convo["clarification_count"] = 0

        # Append turn
        turn: ConversationTurn = {
            "user": user_input,
            "assistant_summary": output.get("answer", ""),
            "domain": output.get("domain", ""),
            "issue": output.get("issue", ""),
        }
        convo["history"].append(turn)

        # Update case memory
        if case_memory:
            existing = convo.get("case_memory", {})
            existing_facts = existing.get("facts", [])
            new_facts = case_memory.get("facts", [])
            merged_facts = list(dict.fromkeys(existing_facts + new_facts))
            convo["case_memory"] = {
                **existing,
                **case_memory,
                "facts": merged_facts,
            }

        # Update title (from first query)
        if title and convo["title"] == "New Conversation":
            convo["title"] = title

        # Store raw messages for UI
        convo["messages"].append({"role": "user", "content": user_input})
        convo["messages"].append({"role": "assistant", "content": output})

    def get_messages(self, conversation_id: str) -> list[dict]:
        """Get raw message log for the UI."""
        convo = self._conversations.get(conversation_id)
        if not convo:
            return []
        return convo["messages"]


# Global singleton
memory_store = ConversationStore()
