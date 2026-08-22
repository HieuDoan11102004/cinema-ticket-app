"""Movie node - handles film info, search, and showtimes."""
from langchain_openai import ChatOpenAI

from app.modules.chatbot.graph.state import ChatState
from app.modules.chatbot.graph.tools import get_showtimes, search_movies
from app.shared.core.config import LLM_MODEL, LLM_TEMPERATURE, OPENAI_API_KEY

SYSTEM_PROMPT = """You are the Movie Expert for CineBook cinema chatbot.

Your role is to help users discover movies, get information about films, and find showtimes.

Guidelines:
- Be friendly and enthusiastic about movies
- Provide accurate movie information including ratings, genres, runtime
- List showtimes with date, time, and price
- Format responses nicely with markdown (bold for titles, etc.)
- Keep responses concise but informative

When searching for movies, use the search_movies and get_showtimes tools
to get accurate, real-time information from the database."""


llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE, api_key=OPENAI_API_KEY)
llm_with_tools = llm.bind_tools([search_movies, get_showtimes])


async def movie_node(state: ChatState) -> dict:
    """
    Handle movie-related queries.

    Args:
        state: Current chat state

    Returns:
        Updated state with movie information
    """
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""

    # Build context for LLM
    context_messages = [
        ("system", SYSTEM_PROMPT),
    ]

    # Add conversation history (last 10 messages)
    for msg in messages[-10:]:
        if msg.type == "human":
            context_messages.append(("user", msg.content))
        else:
            context_messages.append(("assistant", msg.content))

    # Get LLM response with tool calls
    response = await llm_with_tools.ainvoke(context_messages)

    # Execute any tool calls
    tool_messages = []
    if hasattr(response, "tool_calls") and response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            if tool_name == "search_movies":
                result = search_movies.invoke(tool_args)
                tool_messages.append(tool_call)
                # Add tool result
                if hasattr(response, "tool_call_chunks"):
                    continue

            elif tool_name == "get_showtimes":
                result = get_showtimes.invoke(tool_args)

        # If tools were called, get final response
        if tool_messages:
            # Re-invoke with tool results
            full_messages = context_messages + [response] + tool_messages
            response = await llm.ainvoke(full_messages)

    # Extract suggested actions
    suggested_actions = []
    if "Inception" in last_message or "Dune" in last_message:
        suggested_actions = [
            {"label": "Book tickets", "action": "book", "params": {}},
            {"label": "See all showtimes", "action": "showtimes", "params": {}},
        ]

    return {
        "messages": [response],
        "suggested_actions": suggested_actions,
        "agent_used": "movie_agent",
    }
