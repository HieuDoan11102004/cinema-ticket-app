"""Coordinator graph - main LangGraph chatbot orchestration."""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.modules.chatbot.graph.state import ChatState
from app.modules.chatbot.graph.nodes.supervisor import supervisor_node, route_intent
from app.modules.chatbot.graph.nodes.movie_node import movie_node
from app.modules.chatbot.graph.nodes.booking_node import booking_node
from app.modules.chatbot.graph.nodes.recommendation_node import recommendation_node
from app.modules.chatbot.graph.nodes.general_node import general_node
from app.modules.chatbot.services.llm_service import get_llm_service


def create_coordinator_graph() -> StateGraph:
    """
    Create the main coordinator graph.

    Structure:
        START -> supervisor -> (conditional routing)
                           |
        movie_node <-------+--> booking_node
                           |                    |
        recommendation_node <-----------------+  |
                           |                   |
        general_node <-----+-------------------+
                           |
                          END
    """
    graph = StateGraph(ChatState)

    # Add all nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("movie_node", movie_node)
    graph.add_node("booking_node", booking_node)
    graph.add_node("recommendation_node", recommendation_node)
    graph.add_node("general_node", general_node)

    # Set entry point
    graph.add_edge(START, "supervisor")

    # Add conditional routing from supervisor
    graph.add_conditional_edges(
        "supervisor",
        route_intent,
        {
            "movie_node": "movie_node",
            "booking_node": "booking_node",
            "recommendation_node": "recommendation_node",
            "general_node": "general_node",
        },
    )

    # Add edges to END
    graph.add_edge("movie_node", END)
    graph.add_edge("booking_node", END)
    graph.add_edge("recommendation_node", END)
    graph.add_edge("general_node", END)

    return graph


# Create checkpointer
checkpointer = MemorySaver()

# Compile the graph
coordinator_graph = create_coordinator_graph()
app = coordinator_graph.compile(checkpointer=checkpointer)


async def run_chatbot(
    session_id: str,
    user_message: str,
    user_id: str | None = None,
) -> dict:
    """
    Run the chatbot for a given session.

    Args:
        session_id: Session identifier
        user_message: User's message
        user_id: Optional user ID

    Returns:
        Dict with response, agent_used, and suggested_actions
    """
    from langchain_core.messages import HumanMessage

    config = {"configurable": {"thread_id": session_id}}

    # Initial state
    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "intent": None,
        "session_id": session_id,
        "user_id": user_id,
        "suggested_actions": None,
        "interrupted": False,
        "booking_context": None,
        "agent_used": None,
    }

    # Run the graph
    final_state = await app.ainvoke(initial_state, config)

    # Extract response
    messages = final_state.get("messages", [])
    last_message = messages[-1].content if messages else ""

    return {
        "response": last_message,
        "agent_used": final_state.get("agent_used", "assistant"),
        "suggested_actions": final_state.get("suggested_actions", []),
        "session_id": session_id,
    }
