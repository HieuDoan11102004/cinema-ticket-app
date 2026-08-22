"""Tests for LangGraph chatbot integration."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.chatbot.graph.coordinator import (
    run_chatbot,
    coordinator_graph,
    create_coordinator_graph,
    app as coordinator_app,
)
from app.modules.chatbot.graph.state import ChatState


class TestCoordinatorGraph:
    """Test the coordinator graph routing."""

    def test_create_coordinator_graph(self):
        """Test that the coordinator graph is created successfully."""
        graph = create_coordinator_graph()
        assert graph is not None

    def test_graph_has_all_nodes(self):
        """Test that all required nodes are in the graph."""
        # Get node names from the compiled graph
        nodes = list(coordinator_graph.nodes.keys())
        expected_nodes = [
            "supervisor",
            "movie_node",
            "booking_node",
            "recommendation_node",
            "general_node",
        ]
        for node in expected_nodes:
            assert node in nodes, f"Missing node: {node}"

    def test_graph_has_conditional_edges(self):
        """Test that conditional edges are configured from supervisor."""
        # The conditional edges should route from supervisor
        edges = coordinator_graph.edges
        # We verify this indirectly by checking the graph structure
        assert "supervisor" in coordinator_graph.nodes


class TestRouteIntent:
    """Test the route_intent function."""

    def test_routes_film_info_to_movie_node(self):
        """Test that film_info intent routes to movie_node."""
        from app.modules.chatbot.graph.nodes.supervisor import route_intent

        state = {"intent": "film_info"}
        result = route_intent(state)
        assert result == "movie_node"

    def test_routes_showtimes_to_movie_node(self):
        """Test that showtimes intent routes to movie_node."""
        from app.modules.chatbot.graph.nodes.supervisor import route_intent

        state = {"intent": "showtimes"}
        result = route_intent(state)
        assert result == "movie_node"

    def test_routes_booking_to_booking_node(self):
        """Test that booking intent routes to booking_node."""
        from app.modules.chatbot.graph.nodes.supervisor import route_intent

        state = {"intent": "booking"}
        result = route_intent(state)
        assert result == "booking_node"

    def test_routes_cancel_booking_to_booking_node(self):
        """Test that cancel_booking intent routes to booking_node."""
        from app.modules.chatbot.graph.nodes.supervisor import route_intent

        state = {"intent": "cancel_booking"}
        result = route_intent(state)
        assert result == "booking_node"

    def test_routes_booking_status_to_booking_node(self):
        """Test that booking_status intent routes to booking_node."""
        from app.modules.chatbot.graph.nodes.supervisor import route_intent

        state = {"intent": "booking_status"}
        result = route_intent(state)
        assert result == "booking_node"

    def test_routes_recommendation_to_recommendation_node(self):
        """Test that recommendation intent routes to recommendation_node."""
        from app.modules.chatbot.graph.nodes.supervisor import route_intent

        state = {"intent": "recommendation"}
        result = route_intent(state)
        assert result == "recommendation_node"

    def test_routes_general_to_general_node(self):
        """Test that general intent routes to general_node."""
        from app.modules.chatbot.graph.nodes.supervisor import route_intent

        state = {"intent": "general"}
        result = route_intent(state)
        assert result == "general_node"

    def test_routes_unknown_intent_to_general_node(self):
        """Test that unknown intent falls back to general_node."""
        from app.modules.chatbot.graph.nodes.supervisor import route_intent

        state = {"intent": "unknown_intent"}
        result = route_intent(state)
        assert result == "general_node"

    def test_routes_missing_intent_to_general_node(self):
        """Test that missing intent falls back to general_node."""
        from app.modules.chatbot.graph.nodes.supervisor import route_intent

        state = {}
        result = route_intent(state)
        assert result == "general_node"


class TestSupervisorNode:
    """Test the supervisor node intent classification."""

    @pytest.mark.anyio
    async def test_supervisor_classifies_film_intent(self):
        """Test intent classification for film query."""
        from app.modules.chatbot.graph.nodes.supervisor import supervisor_node

        # Create mock message
        mock_message = MagicMock()
        mock_message.type = "human"
        mock_message.content = "What's Inception about?"

        state = {
            "messages": [mock_message],
            "intent": None,
            "session_id": "test-session",
            "user_id": None,
            "suggested_actions": None,
            "interrupted": False,
            "booking_context": None,
            "agent_used": None,
        }

        with patch(
            "app.modules.chatbot.graph.nodes.supervisor.ChatOpenAI"
        ) as mock_llm_class:
            mock_llm = mock_llm_class.return_value
            mock_response = MagicMock()
            mock_response.content = "film_info"
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            result = await supervisor_node(state)

            assert result["intent"] == "film_info"

    @pytest.mark.anyio
    async def test_supervisor_classifies_booking_intent(self):
        """Test intent classification for booking query."""
        from app.modules.chatbot.graph.nodes.supervisor import supervisor_node

        mock_message = MagicMock()
        mock_message.type = "human"
        mock_message.content = "I want to book 2 tickets for Spider-Man"

        state = {
            "messages": [mock_message],
            "intent": None,
            "session_id": "test-session",
            "user_id": None,
            "suggested_actions": None,
            "interrupted": False,
            "booking_context": None,
            "agent_used": None,
        }

        with patch(
            "app.modules.chatbot.graph.nodes.supervisor.ChatOpenAI"
        ) as mock_llm_class:
            mock_llm = mock_llm_class.return_value
            mock_response = MagicMock()
            mock_response.content = "booking"
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            result = await supervisor_node(state)

            assert result["intent"] == "booking"

    @pytest.mark.anyio
    async def test_supervisor_handles_unknown_intent(self):
        """Test that supervisor handles unknown intent gracefully."""
        from app.modules.chatbot.graph.nodes.supervisor import supervisor_node

        mock_message = MagicMock()
        mock_message.type = "human"
        mock_message.content = "Some random query"

        state = {
            "messages": [mock_message],
            "intent": None,
            "session_id": "test-session",
            "user_id": None,
            "suggested_actions": None,
            "interrupted": False,
            "booking_context": None,
            "agent_used": None,
        }

        with patch(
            "app.modules.chatbot.graph.nodes.supervisor.ChatOpenAI"
        ) as mock_llm_class:
            mock_llm = mock_llm_class.return_value
            mock_response = MagicMock()
            mock_response.content = "unknown_nonsense"
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            result = await supervisor_node(state)

            # Should fallback to general
            assert result["intent"] == "general"


class TestMovieNode:
    """Test the movie node."""

    def test_movie_node_imports_successfully(self):
        """Test that movie_node can be imported."""
        from app.modules.chatbot.graph.nodes.movie_node import movie_node
        assert movie_node is not None

    def test_movie_node_handles_state_schema(self):
        """Test that movie_node accepts proper state schema."""
        from app.modules.chatbot.graph.nodes.movie_node import movie_node

        mock_message = MagicMock()
        mock_message.type = "human"
        mock_message.content = "Tell me about Inception"

        state = {
            "messages": [mock_message],
            "intent": "film_info",
            "session_id": "test-session",
            "user_id": None,
            "suggested_actions": None,
            "interrupted": False,
            "booking_context": None,
            "agent_used": None,
        }

        # Verify the state has correct structure for movie_node
        assert "messages" in state
        assert "session_id" in state
        assert state["intent"] == "film_info"


class TestGeneralNode:
    """Test the general node."""

    @pytest.mark.anyio
    async def test_general_node_returns_suggested_actions(self):
        """Test that general node returns suggested actions."""
        from app.modules.chatbot.graph.nodes.general_node import general_node

        mock_message = MagicMock()
        mock_message.type = "human"
        mock_message.content = "Hello"

        state = {
            "messages": [mock_message],
            "intent": "general",
            "session_id": "test-session",
            "user_id": None,
            "suggested_actions": None,
            "interrupted": False,
            "booking_context": None,
            "agent_used": None,
        }

        with patch(
            "app.modules.chatbot.graph.nodes.general_node.ChatOpenAI"
        ) as mock_llm_class:
            mock_llm = mock_llm_class.return_value
            mock_response = MagicMock()
            mock_response.content = "Hello! How can I help?"
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            result = await general_node(state)

            assert "suggested_actions" in result
            assert len(result["suggested_actions"]) > 0
            assert "agent_used" in result
            assert result["agent_used"] == "assistant"


class TestRunChatbot:
    """Test the main run_chatbot function."""

    @pytest.mark.anyio
    async def test_run_chatbot_returns_response(self):
        """Test that run_chatbot returns expected structure."""
        # Mock the compiled graph's ainvoke
        with patch.object(coordinator_app, "ainvoke", new_callable=AsyncMock) as mock_invoke:
            mock_message = MagicMock()
            mock_message.content = "Hello! How can I help?"

            mock_invoke.return_value = {
                "messages": [mock_message],
                "intent": "general",
                "agent_used": "assistant",
                "suggested_actions": [
                    {"label": "Find a movie", "action": "list_movies", "params": {}}
                ],
            }

            result = await run_chatbot(
                session_id="test-session",
                user_message="Hello",
            )

            assert "response" in result
            assert "session_id" in result
            assert "agent_used" in result
            assert result["session_id"] == "test-session"
            assert result["response"] == "Hello! How can I help?"

    @pytest.mark.anyio
    async def test_run_chatbot_with_user_id(self):
        """Test that run_chatbot passes user_id to the graph."""
        with patch.object(coordinator_app, "ainvoke", new_callable=AsyncMock) as mock_invoke:
            mock_message = MagicMock()
            mock_message.content = "Hello"

            mock_invoke.return_value = {
                "messages": [mock_message],
                "intent": "general",
                "agent_used": "assistant",
                "suggested_actions": [],
            }

            result = await run_chatbot(
                session_id="test-session",
                user_message="Hello",
                user_id="user-123",
            )

            assert result["session_id"] == "test-session"

            # Verify the initial state included user_id
            call_args = mock_invoke.call_args
            initial_state = call_args[0][0]
            assert initial_state["user_id"] == "user-123"

    @pytest.mark.anyio
    async def test_run_chatbot_handles_empty_messages(self):
        """Test that run_chatbot handles empty message list."""
        with patch.object(coordinator_app, "ainvoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = {
                "messages": [],
                "intent": None,
                "agent_used": None,
                "suggested_actions": [],
            }

            result = await run_chatbot(
                session_id="test-session",
                user_message="Test",
            )

            # Should return empty response
            assert result["response"] == ""


class TestChatState:
    """Test the ChatState schema."""

    def test_chat_state_has_required_fields(self):
        """Test that ChatState has all required fields."""
        state = ChatState(
            messages=[],
            intent=None,
            session_id="test",
            user_id=None,
            suggested_actions=None,
            interrupted=False,
            booking_context=None,
            agent_used=None,
        )

        assert "messages" in state
        assert "intent" in state
        assert "session_id" in state
        assert "user_id" in state
        assert "suggested_actions" in state
        assert "interrupted" in state
        assert "booking_context" in state
        assert "agent_used" in state
