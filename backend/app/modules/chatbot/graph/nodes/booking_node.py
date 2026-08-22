"""Booking node - handles booking, cancellation, and status."""
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.modules.chatbot.graph.state import ChatState
from app.modules.chatbot.graph.tools import create_booking, cancel_booking, get_booking_status
from app.shared.core.config import LLM_MODEL, LLM_TEMPERATURE, OPENAI_API_KEY


SYSTEM_PROMPT = """You are the Booking Expert for CineBook cinema chatbot.

Your role is to help users book movie tickets, view their bookings, and manage reservations.

Guidelines:
- Guide users through the booking process step by step
- Confirm all booking details before creating a booking
- Mention seat availability and pricing
- Provide booking codes after successful bookings
- Help users cancel or modify bookings when possible

IMPORTANT: Before creating a booking, you MUST:
1. Confirm the movie and showtime with the user
2. Ask them to select specific seats
3. Ask them to confirm before calling create_booking tool

For checking bookings, use get_booking_status tool.
For cancellations, use cancel_booking tool (confirm with user first)."""


llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE, api_key=OPENAI_API_KEY)
llm_with_tools = llm.bind_tools([create_booking, cancel_booking, get_booking_status])


async def booking_node(state: ChatState) -> dict:
    """
    Handle booking-related queries.

    Args:
        state: Current chat state

    Returns:
        Updated state with booking information
    """
    messages = state["messages"]
    user_id = state.get("user_id")

    context_messages = [("system", SYSTEM_PROMPT)]

    # Add conversation history
    for msg in messages[-10:]:
        if msg.type == "human":
            context_messages.append(("user", msg.content))
        else:
            context_messages.append(("assistant", msg.content))

    # Get LLM response
    response = await llm_with_tools.ainvoke(context_messages)

    # Execute tool calls if any
    if hasattr(response, "tool_calls") and response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            if tool_name == "create_booking" and user_id:
                tool_args["user_id"] = user_id
                result = create_booking.invoke(tool_args)

            elif tool_name == "cancel_booking" and user_id:
                tool_args["user_id"] = user_id
                result = cancel_booking.invoke(tool_args)

            elif tool_name == "get_booking_status":
                result = get_booking_status.invoke(tool_args)

    suggested_actions = [
        {"label": "View my bookings", "action": "view_bookings", "params": {}},
        {"label": "Browse movies", "action": "list_movies", "params": {}},
    ]

    return {
        "messages": [response],
        "suggested_actions": suggested_actions,
        "agent_used": "booking_agent",
    }
