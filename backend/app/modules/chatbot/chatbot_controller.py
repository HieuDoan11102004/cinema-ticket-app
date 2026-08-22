"""Chatbot Controller - FastAPI router for chatbot endpoints."""
from uuid import UUID

import redis.asyncio as redis
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.chatbot.dto.chatbot_dto import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationHistoryResponse,
    SuggestedAction,
)
from app.modules.chatbot.graph.coordinator import run_chatbot
from app.modules.chatbot.services.conversation_service import ConversationService
from app.shared.db.database import get_db
from app.shared.redis import get_redis

router = APIRouter(prefix="/api/v1/chatbot", tags=["chatbot"])


async def get_conversation_service(
    redis_client: redis.Redis = Depends(get_redis),
) -> ConversationService:
    """Dependency to get conversation service."""
    return ConversationService(redis_client)


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    conversation_service: ConversationService = Depends(get_conversation_service),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
) -> ChatMessageResponse:
    """
    Send a message to the chatbot and receive a response.

    Uses LangGraph for multi-agent orchestration with tool calling.
    """
    # Get or create session
    session_id, _is_new = await conversation_service.get_or_create_session(request.session_id)

    # Get user_id as string
    user_id_str = str(request.user_id) if request.user_id else None

    # Run the LangGraph chatbot
    result = await run_chatbot(
        session_id=session_id,
        user_message=request.message,
        user_id=user_id_str,
    )

    # Convert suggested actions
    suggested = [
        SuggestedAction(**action) for action in (result.get("suggested_actions") or [])
    ]

    return ChatMessageResponse(
        response=result["response"],
        session_id=result["session_id"],
        agent_used=result.get("agent_used", "assistant"),
        suggested_actions=suggested,
    )


@router.get("/conversation/{session_id}", response_model=ConversationHistoryResponse)
async def get_conversation(
    session_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ConversationHistoryResponse:
    """Get the conversation history for a session."""
    messages = await conversation_service.get_conversation(session_id)
    session_info = await conversation_service.get_session_info(session_id)

    if not session_info:
        return ConversationHistoryResponse(
            session_id=session_id,
            messages=[],
            created_at=messages[0].timestamp if messages else None,
            last_updated=messages[-1].timestamp if messages else None,
        )

    return ConversationHistoryResponse(
        session_id=session_id,
        messages=messages,
        created_at=session_info.get("created_at"),
        last_updated=session_info.get("last_updated"),
    )


@router.delete("/conversation/{session_id}")
async def clear_conversation(
    session_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> dict[str, str]:
    """Clear the conversation history for a session."""
    success = await conversation_service.clear_conversation(session_id)

    if success:
        return {"message": "Conversation cleared successfully", "session_id": session_id}
    else:
        return {"message": "Session not found", "session_id": session_id}


@router.post("/conversation")
async def create_new_session(
    conversation_service: ConversationService = Depends(get_conversation_service),
    user_id: UUID | None = None,
) -> dict[str, str]:
    """Create a new conversation session."""
    session_id = await conversation_service.create_session(str(user_id) if user_id else None)
    return {"session_id": session_id}
