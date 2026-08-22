"""LLM Service - OpenAI API integration for chatbot agents."""

import httpx
from pydantic import BaseModel

from app.shared.core.config import (
    LLM_MAX_TOKENS,
    LLM_MODEL,
    LLM_TEMPERATURE,
    OPENAI_API_KEY,
)


class LLMMessage(BaseModel):
    """A message in an LLM conversation."""

    role: str  # "system", "user", or "assistant"
    content: str


class LLMResponse(BaseModel):
    """Response from the LLM API."""

    content: str
    usage: dict | None = None
    model: str


class LLMService:
    """Service for interacting with OpenAI's LLM API."""

    BASE_URL = "https://api.openai.com/v1"

    def __init__(
        self,
        api_key: str = OPENAI_API_KEY,
        model: str = LLM_MODEL,
        max_tokens: int = LLM_MAX_TOKENS,
        temperature: float = LLM_TEMPERATURE,
    ):
        """Initialize the LLM service."""
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def chat(
        self,
        messages: list[LLMMessage],
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """
        Send a chat completion request to the LLM.

        Args:
            messages: List of conversation messages
            system_prompt: Optional system prompt to prepend
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            LLMResponse with the model's response

        Raises:
            httpx.HTTPStatusError: If the API returns an error
        """
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured")

        # Build the full message list
        full_messages = []
        if system_prompt:
            full_messages.append(LLMMessage(role="system", content=system_prompt))
        full_messages.extend(messages)

        # Prepare request payload
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in full_messages],
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
        }

        client = await self._get_client()
        response = await client.post("/chat/completions", json=payload)
        response.raise_for_status()

        data = response.json()
        choice = data["choices"][0]
        message = choice["message"]

        return LLMResponse(
            content=message["content"],
            usage=data.get("usage"),
            model=data.get("model", self.model),
        )

    async def classify_intent(
        self,
        user_message: str,
        intents: list[str],
        examples: dict[str, str] | None = None,
    ) -> str:
        """
        Classify user intent using the LLM.

        Args:
            user_message: The user's message
            intents: List of possible intent names
            examples: Optional dict mapping intent -> example messages

        Returns:
            The classified intent name
        """
        intents_str = ", ".join(intents)

        example_text = ""
        if examples:
            example_text = "\n\nExamples:\n" + "\n".join(
                f"- \"{ex}\" -> {intent}" for intent, ex in examples.items()
            )

        system_prompt = f"""You are an intent classifier for a cinema booking chatbot.
Classify the user's message into one of these intents: {intents_str}.
{example_text}
Respond with ONLY the intent name, nothing else."""

        response = await self.chat(
            messages=[LLMMessage(role="user", content=user_message)],
            system_prompt=system_prompt,
            temperature=0.1,  # Low temperature for consistent classification
            max_tokens=50,
        )

        # Parse the response
        intent = response.content.strip().lower()
        # Find matching intent (case-insensitive)
        for possible_intent in intents:
            if possible_intent.lower() == intent:
                return possible_intent

        # Default to general if no match
        return "general"


# Global LLM service instance (lazy initialization)
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """Get or create the global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
