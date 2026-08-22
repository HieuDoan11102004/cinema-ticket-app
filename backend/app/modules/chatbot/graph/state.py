"""ChatGraph state schema."""
from typing import Annotated, TypedDict

from langgraph.graph import add_messages


class ChatState(TypedDict):
    """State schema for the chatbot graph."""

    messages: Annotated[list, add_messages]
    """Conversation messages (user + assistant)."""

    intent: str | None
    """Classified user intent (film_info, booking, etc.)."""

    session_id: str
    """Session identifier for Redis metadata."""

    user_id: str | None
    """Authenticated user ID (optional)."""

    suggested_actions: list[dict] | None
    """Structured suggested actions for frontend."""

    interrupted: bool
    """Flag for human-in-the-loop interrupts."""

    booking_context: dict | None
    """Context for multi-step booking flow."""

    agent_used: str | None
    """Which agent/node handled the last message."""
