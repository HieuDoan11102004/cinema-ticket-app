"""Supervisor node - intent classification and routing."""
from typing import Literal

from app.modules.chatbot.graph.state import ChatState
from app.modules.chatbot.services.llm_service import LLMMessage, LLMService

INTENTS = [
    "film_info",
    "showtimes",
    "booking",
    "cancel_booking",
    "booking_status",
    "recommendation",
    "general",
]

INTENT_EXAMPLES = {
    "film_info": "What's the rating of Inception?",
    "showtimes": "When is Dune showing?",
    "booking": "I want to book 2 tickets for Spider-Man",
    "cancel_booking": "Cancel my booking ABC123",
    "booking_status": "What's the status of my booking?",
    "recommendation": "What do you recommend I watch tonight?",
}


async def supervisor_node(state: ChatState, llm_service: LLMService) -> dict:
    """
    Classify user intent and route to appropriate agent.

    Args:
        state: Current chat state with messages
        llm_service: LLM service for classification

    Returns:
        Dict with classified intent
    """
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""

    # Build context from recent messages
    context_summary = ""
    if len(messages) > 1:
        recent = messages[-6:-1]  # Last 5 messages for context
        context_summary = "\n\nRecent conversation:\n"
        for msg in recent:
            role = "User" if msg.type == "human" else "Assistant"
            content = msg.content[:100]
            context_summary += f"- {role}: {content}...\n"

    prompt = f"""Classify this user message into one of these intents:
{', '.join(INTENTS)}

Message: "{last_message}"
{context_summary}

Respond with ONLY the intent name (e.g., "film_info")."""

    response = await llm_service.chat(
        messages=[LLMMessage(role="user", content=prompt)],
        system_prompt="You are an intent classifier. Return ONLY the intent name, nothing else.",
        temperature=0.1,
        max_tokens=50,
    )

    intent = response.content.strip().lower()

    # Validate intent
    if intent not in INTENTS:
        # Try partial match
        for valid_intent in INTENTS:
            if valid_intent in intent or intent in valid_intent:
                intent = valid_intent
                break
        else:
            intent = "general"

    return {"intent": intent}


def route_intent(state: ChatState) -> Literal[
    "movie_subgraph",
    "booking_subgraph",
    "recommendation_node",
    "general_node",
]:
    """
    Route to appropriate subgraph based on classified intent.

    Args:
        state: Current chat state

    Returns:
        Name of the next node/subgraph to execute
    """
    intent = state.get("intent", "general")

    intent_map = {
        "film_info": "movie_subgraph",
        "showtimes": "movie_subgraph",
        "booking": "booking_subgraph",
        "cancel_booking": "booking_subgraph",
        "booking_status": "booking_subgraph",
        "recommendation": "recommendation_node",
        "general": "general_node",
    }

    return intent_map.get(intent, "general_node")
