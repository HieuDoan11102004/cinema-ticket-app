"""General node - handles non-specialized queries."""
from langchain_openai import ChatOpenAI

from app.modules.chatbot.graph.state import ChatState
from app.shared.core.config import LLM_MODEL, LLM_TEMPERATURE, OPENAI_API_KEY

SYSTEM_PROMPT = """You are CineBook's friendly assistant.

You help users with:
- Movie information and recommendations
- Showtimes and schedules
- Booking tickets
- Managing reservations

If a user asks about something outside these topics, politely redirect
to how you can help with cinema-related questions.

Be conversational, friendly, and helpful."""


llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE, api_key=OPENAI_API_KEY)


async def general_node(state: ChatState) -> dict:
    """
    Handle general conversation.

    Args:
        state: Current chat state

    Returns:
        Updated state with general response
    """
    messages = state["messages"]

    context_messages = [("system", SYSTEM_PROMPT)]
    for msg in messages[-10:]:
        if msg.type == "human":
            context_messages.append(("user", msg.content))
        else:
            context_messages.append(("assistant", msg.content))

    response = await llm.ainvoke(context_messages)

    suggested_actions = [
        {"label": "Find a movie", "action": "list_movies", "params": {}},
        {"label": "Check showtimes", "action": "showtimes", "params": {}},
        {"label": "Book tickets", "action": "booking", "params": {}},
    ]

    return {
        "messages": [response],
        "suggested_actions": suggested_actions,
        "agent_used": "assistant",
    }
