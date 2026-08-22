"""Booking subgraph - handles booking-related queries."""
from langgraph.graph import END, StateGraph

from app.modules.chatbot.graph.nodes.booking_node import booking_node
from app.modules.chatbot.graph.state import ChatState


def create_booking_subgraph() -> StateGraph:
    """
    Create the booking subgraph.

    Structure: START -> booking_node -> END
    """
    graph = StateGraph(ChatState)

    graph.add_node("booking_node", booking_node)
    graph.set_entry_point("booking_node")
    graph.add_edge("booking_node", END)

    return graph.compile()


booking_subgraph = create_booking_subgraph()
