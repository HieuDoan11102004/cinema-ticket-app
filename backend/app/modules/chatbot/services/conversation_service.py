"""Conversation Service - Redis-based conversation management for chatbot."""
import json
from datetime import UTC, datetime
from uuid import uuid4

import redis.asyncio as redis

from app.modules.chatbot.dto.chatbot_dto import AgentType, MessageEntry
from app.shared.core.config import LLM_CONVERSATION_TTL


class ConversationService:
    """Service for managing conversation history in Redis."""

    CONVERSATION_PREFIX = "chatbot:conversation:"
    SESSION_PREFIX = "chatbot:session:"

    def __init__(self, redis_client: redis.Redis, ttl: int = LLM_CONVERSATION_TTL):
        """Initialize the conversation service."""
        self.redis = redis_client
        self.ttl = ttl

    def _conversation_key(self, session_id: str) -> str:
        """Get the Redis key for a conversation."""
        return f"{self.CONVERSATION_PREFIX}{session_id}"

    def _session_key(self, session_id: str) -> str:
        """Get the Redis key for session metadata."""
        return f"{self.SESSION_PREFIX}{session_id}"

    async def create_session(self, user_id: str | None = None) -> str:
        """
        Create a new conversation session.

        Args:
            user_id: Optional user ID to associate with the session

        Returns:
            The new session ID
        """
        session_id = str(uuid4())

        # Store session metadata
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now(UTC).isoformat(),
            "last_updated": datetime.now(UTC).isoformat(),
        }
        await self.redis.setex(
            self._session_key(session_id),
            self.ttl,
            json.dumps(session_data),
        )

        # Initialize empty conversation
        await self.redis.setex(
            self._conversation_key(session_id),
            self.ttl,
            json.dumps([]),
        )

        return session_id

    async def get_or_create_session(self, session_id: str | None = None) -> tuple[str, bool]:
        """
        Get an existing session or create a new one.

        Args:
            session_id: Optional existing session ID

        Returns:
            Tuple of (session_id, is_new) where is_new indicates if session was created
        """
        if session_id:
            # Check if session exists
            exists = await self.redis.exists(self._conversation_key(session_id))
            if exists:
                # Refresh TTL and return existing session
                await self.redis.expire(self._conversation_key(session_id), self.ttl)
                await self.redis.expire(self._session_key(session_id), self.ttl)
                return session_id, False

        # Create new session
        new_session_id = await self.create_session()
        return new_session_id, True

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        agent: AgentType | None = None,
    ) -> list[MessageEntry]:
        """
        Add a message to the conversation history.

        Args:
            session_id: The session ID
            role: Message role ("user" or "assistant")
            content: Message content
            agent: Which agent sent the message (for assistant messages)

        Returns:
            Updated conversation history
        """
        message = MessageEntry(
            role=role,
            content=content,
            agent=agent,
            timestamp=datetime.now(UTC),
        )

        # Get existing conversation
        conversation = await self.get_conversation(session_id)
        conversation.append(message)

        # Save updated conversation
        await self.redis.setex(
            self._conversation_key(session_id),
            self.ttl,
            json.dumps([msg.model_dump(mode="json") for msg in conversation], default=str),
        )

        # Update session last_updated
        session_key = self._session_key(session_id)
        session_data = await self.redis.get(session_key)
        if session_data:
            data = json.loads(session_data)
            data["last_updated"] = datetime.now(UTC).isoformat()
            await self.redis.setex(session_key, self.ttl, json.dumps(data))

        return conversation

    async def get_conversation(self, session_id: str) -> list[MessageEntry]:
        """
        Get the conversation history for a session.

        Args:
            session_id: The session ID

        Returns:
            List of message entries
        """
        data = await self.redis.get(self._conversation_key(session_id))
        if not data:
            return []

        messages = json.loads(data)
        return [MessageEntry(**msg) for msg in messages]

    async def get_conversation_for_llm(
        self,
        session_id: str,
        max_messages: int = 20,
    ) -> list[dict]:
        """
        Get conversation formatted for LLM API.

        Args:
            session_id: The session ID
            max_messages: Maximum number of recent messages to return

        Returns:
            List of messages in LLM format [{"role": ..., "content": ...}]
        """
        conversation = await self.get_conversation(session_id)
        # Take the most recent messages
        recent = conversation[-max_messages:] if len(conversation) > max_messages else conversation
        return [{"role": msg.role, "content": msg.content} for msg in recent]

    async def clear_conversation(self, session_id: str) -> bool:
        """
        Clear the conversation history for a session.

        Args:
            session_id: The session ID

        Returns:
            True if session existed and was cleared
        """
        conversation_key = self._conversation_key(session_id)

        # Check if session exists
        exists = await self.redis.exists(conversation_key)
        if not exists:
            return False

        # Clear conversation but keep session
        await self.redis.setex(conversation_key, self.ttl, json.dumps([]))
        return True

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and its conversation.

        Args:
            session_id: The session ID

        Returns:
            True if session existed and was deleted
        """
        conversation_key = self._conversation_key(session_id)
        session_key = self._session_key(session_id)

        # Delete both keys
        result = await self.redis.delete(conversation_key, session_key)
        return result > 0

    async def get_session_info(self, session_id: str) -> dict | None:
        """
        Get session metadata.

        Args:
            session_id: The session ID

        Returns:
            Session metadata dict or None if not found
        """
        data = await self.redis.get(self._session_key(session_id))
        if not data:
            return None
        return json.loads(data)

    async def get_langgraph_config(self, session_id: str) -> dict:
        """
        Get LangGraph checkpointer config for a session.

        Args:
            session_id: The session ID

        Returns:
            Config dict for LangGraph checkpointer
        """
        return {"configurable": {"thread_id": session_id}}
