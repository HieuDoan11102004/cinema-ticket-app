"""Supervisor node - intent classification and routing."""
from typing import Literal

from langchain_openai import ChatOpenAI

from app.modules.chatbot.graph.state import ChatState
from app.shared.core.config import LLM_MODEL, LLM_TEMPERATURE, OPENAI_API_KEY

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

# Initialize LLM for classification
llm = ChatOpenAI(model=LLM_MODEL, temperature=0.1, api_key=OPENAI_API_KEY)


async def supervisor_node(state: ChatState) -> dict:
    """
    Classify user intent and route to appropriate agent.

    Args:
        state: Current chat state with messages

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

    # Use the LLM to classify intent
    response = await llm.ainvoke(
        [
            ("system", "You are an intent classifier. Return ONLY the intent name, nothing else."),
            ("user", prompt),
        ]
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
    "movie_node",
    "booking_node",
    "recommendation_node",
    "general_node",
]:
    """
    Route to appropriate node based on classified intent.

    Args:
        state: Current chat state

    Returns:
        Name of the next node to execute
    """
    intent = state.get("intent", "general")

    intent_map = {
        "film_info": "movie_node",
        "showtimes": "movie_node",
        "booking": "booking_node",
        "cancel_booking": "booking_node",
        "booking_status": "booking_node",
        "recommendation": "recommendation_node",
        "general": "general_node",
    }

    return intent_map.get(intent, "general_node")
