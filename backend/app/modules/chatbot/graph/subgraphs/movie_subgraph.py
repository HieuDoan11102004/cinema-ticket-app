"""Movie subgraph - handles movie-related queries."""
from langgraph.graph import StateGraph, END

from app.modules.chatbot.graph.state import ChatState
from app.modules.chatbot.graph.nodes.movie_node import movie_node


def create_movie_subgraph() -> StateGraph:
    """
    Create the movie subgraph.

    Structure: START -> movie_node -> END
    """
    graph = StateGraph(ChatState)

    graph.add_node("movie_node", movie_node)
    graph.set_entry_point("movie_node")
    graph.add_edge("movie_node", END)

    return graph.compile()


movie_subgraph = create_movie_subgraph()
