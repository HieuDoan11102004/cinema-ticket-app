"""Pydantic DTOs for chatbot API."""
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Agent types in the chatbot system."""

    PRIMARY = "primary_assistant"
    MOVIE = "movie_agent"
    BOOKING = "booking_agent"


class SuggestedAction(BaseModel):
    """Suggested action for the user."""

    label: str = Field(..., description="Human-readable label for the action")
    action: str = Field(..., description="Action type (book, showtimes, etc.)")
    params: dict | None = Field(None, description="Additional parameters for the action")


class ChatMessageRequest(BaseModel):
    """Request model for sending a chat message."""

    message: str = Field(..., min_length=1, max_length=2000, description="User's message")
    user_id: UUID | None = Field(None, description="User ID for authenticated users")
    session_id: str | None = Field(None, description="Session ID for conversation continuity")


class ChatMessageResponse(BaseModel):
    """Response model for chat messages."""

    response: str = Field(..., description="Agent's text response")
    session_id: str = Field(..., description="Session ID for this conversation")
    agent_used: AgentType = Field(..., description="Which agent handled the request")
    suggested_actions: list[SuggestedAction] = Field(
        default_factory=list, description="Suggested follow-up actions"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MessageEntry(BaseModel):
    """A single message in the conversation history."""

    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    agent: AgentType | None = Field(None, description="Which agent sent this message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history."""

    session_id: str = Field(..., description="Session ID")
    messages: list[MessageEntry] = Field(default_factory=list, description="Conversation history")
    created_at: datetime = Field(..., description="When the conversation started")
    last_updated: datetime = Field(..., description="When the conversation was last updated")


class ConfirmBookingRequest(BaseModel):
    """Request to confirm a booking from chat."""

    session_id: str = Field(..., description="Chat session ID")
    showtime_id: int = Field(..., description="Showtime ID to book")
    seat_ids: list[int] = Field(..., min_length=1, description="Seat IDs to book")


class CancelBookingRequest(BaseModel):
    """Request to cancel a booking from chat."""

    session_id: str = Field(..., description="Chat session ID")
    booking_code: str = Field(..., description="Booking code to cancel")
    reason: str | None = Field(None, max_length=500, description="Cancellation reason")
