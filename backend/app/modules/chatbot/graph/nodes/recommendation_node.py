"""Recommendation node - handles movie recommendations."""
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.modules.chatbot.graph.state import ChatState
from app.modules.chatbot.graph.tools import search_movies
from app.shared.core.config import LLM_MODEL, LLM_TEMPERATURE, OPENAI_API_KEY


SYSTEM_PROMPT = """You are CineBook's movie recommendation expert.

Your role is to suggest movies based on user preferences, mood, or recent trends.

Guidelines:
- Ask follow-up questions to understand preferences
- Consider genres, mood, and similar movies they've enjoyed
- Provide 2-3 recommendations with brief explanations
- Use the search_movies tool to get current movie information
- Be enthusiastic and personal in your recommendations"""

llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE, api_key=OPENAI_API_KEY)
llm_with_tools = llm.bind_tools([search_movies])


async def recommendation_node(state: ChatState) -> dict:
    """
    Handle movie recommendation requests.

    Args:
        state: Current chat state

    Returns:
        Updated state with recommendations
    """
    messages = state["messages"]

    context_messages = [("system", SYSTEM_PROMPT)]
    for msg in messages[-10:]:
        if msg.type == "human":
            context_messages.append(("user", msg.content))
        else:
            context_messages.append(("assistant", msg.content))

    response = await llm_with_tools.ainvoke(context_messages)

    suggested_actions = [
        {"label": "Book recommended movie", "action": "book", "params": {}},
        {"label": "See showtimes", "action": "showtimes", "params": {}},
        {"label": "Get more recommendations", "action": "recommend", "params": {}},
    ]

    return {
        "messages": [response],
        "suggested_actions": suggested_actions,
        "agent_used": "recommendation_agent",
    }
