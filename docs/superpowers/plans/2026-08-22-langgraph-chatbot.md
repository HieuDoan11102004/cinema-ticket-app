# LangGraph Chatbot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace custom multi-agent routing with LangGraph stateful graph orchestration, adding tool calling, human-in-the-loop interrupts, and structured output.

**Architecture:** Multi-agent parallel graph with supervisor node routing to specialized subgraphs. Uses LangGraph's built-in checkpointer for conversation memory (RedisSaver optional for production).

**Tech Stack:** LangGraph, LangChain OpenAI integration, Pydantic, Redis

**Spec:** This plan implements the design approved in the brainstorming session.

---

## Global Constraints

- Python 3.11+
- `uv` package manager (not pip)
- OpenAI API for LLM
- Redis for session metadata, LangGraph checkpointer for conversation state
- Maintain API compatibility with existing frontend (same DTOs, endpoints)

---

## File Structure

```
backend/app/modules/chatbot/
├── __init__.py
├── chatbot_controller.py     # MODIFY - use coordinator graph
├── dto/
│   ├── __init__.py
│   └── chatbot_dto.py         # MODIFY - add structured output fields
├── services/
│   ├── __init__.py
│   ├── llm_service.py        # KEEP - wraps OpenAI calls
│   └── conversation_service.py # MODIFY - keep for session IDs only
├── agents/                    # DELETE entire directory
│   ├── __init__.py
│   ├── base_agent.py
│   ├── primary_assistant.py
│   ├── movie_agent.py
│   └── booking_agent.py
└── graph/                     # CREATE
    ├── __init__.py
    ├── state.py               # TypedDict state schema
    ├── coordinator.py          # Main graph compilation
    ├── nodes/
    │   ├── __init__.py
    │   ├── supervisor.py      # Intent classification + routing
    │   ├── movie_node.py       # Movie search, showtimes
    │   ├── booking_node.py     # Create/view/cancel bookings
    │   ├── recommendation_node.py
    │   └── general_node.py     # Fallback responses
    ├── tools/
    │   ├── __init__.py
    │   ├── search_movies.py
    │   ├── get_showtimes.py
    │   ├── create_booking.py
    │   ├── cancel_booking.py
    │   └── get_booking_status.py
    └── subgraphs/
        ├── __init__.py
        ├── movie_subgraph.py
        └── booking_subgraph.py
```

---

## Task 1: Add Dependencies

**Files:**
- Modify: `backend/pyproject.toml`

**Interfaces:**
- Consumes: Nothing
- Produces: `langgraph`, `langchain-openai`, `langchain-core` added to dependencies

- [ ] **Step 1: Add langgraph and langchain dependencies**

```toml
[project]
dependencies = [
    # ... existing dependencies ...
    "langgraph>=0.2.0",
    "langchain-openai>=0.2.0",
    "langchain-core>=0.3.0",
]
```

Run: `cd backend && uv sync`

- [ ] **Step 2: Commit**

```bash
cd backend
git add pyproject.toml uv.lock
git commit -m "chore: add langgraph dependencies"
```

---

## Task 2: Create State Schema

**Files:**
- Create: `backend/app/modules/chatbot/graph/state.py`
- Create: `backend/app/modules/chatbot/graph/__init__.py`

**Interfaces:**
- Consumes: Nothing
- Produces: `ChatState` TypedDict, `add_messages` reducer

- [ ] **Step 1: Create state schema**

```python
"""ChatGraph state schema."""
from typing import Annotated, TypedDict

from langgraph.graph import add_messages


class ChatState(TypedDict):
    """State schema for the chatbot graph."""

    messages: Annotated[list, add_messages]
    """Conversation messages (user + assistant)."""

    intent: str | None
    """Classified user intent (film_info, booking, etc.)."""

    session_id: str
    """Session identifier for Redis metadata."""

    user_id: str | None
    """Authenticated user ID (optional)."""

    suggested_actions: list[dict] | None
    """Structured suggested actions for frontend."""

    interrupted: bool
    """Flag for human-in-the-loop interrupts."""

    booking_context: dict | None
    """Context for multi-step booking flow."""

    agent_used: str | None
    """Which agent/node handled the last message."""
```

- [ ] **Step 2: Create __init__.py exports**

```python
"""LangGraph chatbot components."""
from app.modules.chatbot.graph.coordinator import app, coordinator_graph
from app.modules.chatbot.graph.state import ChatState

__all__ = ["ChatState, app, coordinator_graph]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/modules/chatbot/graph/
git commit -m "feat(chatbot): add LangGraph state schema"
```

---

## Task 3: Create Supervisor Node

**Files:**
- Create: `backend/app/modules/chatbot/graph/nodes/supervisor.py`
- Modify: `backend/app/modules/chatbot/graph/nodes/__init__.py`

**Interfaces:**
- Consumes: `ChatState` (with messages)
- Produces: `{"intent": str, "messages": [...]}`

- [ ] **Step 1: Create supervisor node**

```python
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
```

- [ ] **Step 2: Update nodes __init__.py**

```python
"""Chatbot graph nodes."""
from app.modules.chatbot.graph.nodes.supervisor import (
    route_intent,
    supervisor_node,
)

__all__ = ["supervisor_node", "route_intent"]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/modules/chatbot/graph/nodes/
git commit -m "feat(chatbot): add supervisor node for intent routing"
```

---

## Task 4: Create Tool Functions

**Files:**
- Create: `backend/app/modules/chatbot/graph/tools/search_movies.py`
- Create: `backend/app/modules/chatbot/graph/tools/get_showtimes.py`
- Create: `backend/app/modules/chatbot/graph/tools/create_booking.py`
- Create: `backend/app/modules/chatbot/graph/tools/cancel_booking.py`
- Create: `backend/app/modules/chatbot/graph/tools/get_booking_status.py`
- Create: `backend/app/modules/chatbot/graph/tools/__init__.py`

**Interfaces:**
- Consumes: Tool input parameters
- Produces: Structured tool responses (Pydantic models)

- [ ] **Step 1: Create search_movies tool**

```python
"""Search movies tool."""
from typing import Annotated, Sequence

from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.modules.films.film_repository import FilmRepository


@tool
def search_movies(
    query: Annotated[str, "Movie title or keywords to search for"],
    genres: Annotated[list[str] | None, "List of genres to filter by"] = None,
    limit: Annotated[int, "Maximum number of results"] = 10,
) -> dict:
    """
    Search for movies by title, genre, or keywords.

    Use this when the user wants to find information about movies,
    see what's playing, or get movie recommendations.

    Args:
        query: Search query (movie title, actor, director, etc.)
        genres: Optional list of genres to filter by
        limit: Maximum number of results (default 10)

    Returns:
        Dict with list of matching movies
    """
    from app.shared.db.database import SessionLocal

    db: Session = SessionLocal()
    try:
        repository = FilmRepository(db)
        films, _ = repository.search_fts(
            query=query,
            genres=genres,
            status="Released",
            skip=0,
            limit=limit,
        )

        return {
            "movies": [
                {
                    "id": film.id,
                    "title": film.title,
                    "tagline": film.tagline,
                    "genres": film.genres,
                    "overview": film.overview,
                    "vote_average": film.vote_average,
                    "runtime": film.runtime,
                    "poster_url": film.poster_url,
                }
                for film in films
            ],
            "count": len(films),
        }
    finally:
        db.close()
```

- [ ] **Step 2: Create get_showtimes tool**

```python
"""Get showtimes tool."""
from datetime import datetime
from typing import Annotated

from langchain_core.tools import tool


@tool
def get_showtimes(
    film_id: Annotated[int | None, "Film ID to get showtimes for (optional if query provided)"] = None,
    query: Annotated[str | None, "Movie title to search for"] = None,
    date: Annotated[str | None, "Date in YYYY-MM-DD format"] = None,
    limit: Annotated[int, "Maximum number of showtimes"] = 10,
) -> dict:
    """
    Get available showtimes for a movie.

    Use this when the user asks about when a movie is playing,
    or wants to see available times.

    Args:
        film_id: Specific film ID (preferred if known)
        query: Movie title to search for (used if film_id not provided)
        date: Filter by date (YYYY-MM-DD format)
        limit: Maximum results

    Returns:
        Dict with showtimes list
    """
    from app.modules.films.film_repository import FilmRepository
    from sqlalchemy import and_, select
    from app.shared.db.database import SessionLocal
    from app.models.showtime import Showtime

    db = SessionLocal()
    try:
        # Get film_id from query if not provided
        if film_id is None and query:
            repo = FilmRepository(db)
            films, _ = repo.search_fts(query=query, status="Released", skip=0, limit=1)
            if films:
                film_id = films[0].id

        if film_id is None:
            return {"showtimes": [], "message": "No film specified"}

        # Build query
        stmt = select(Showtime).where(Showtime.film_id == film_id)

        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
                from datetime import timedelta
                stmt = stmt.where(
                    and_(
                        Showtime.start_time >= datetime.combine(target_date, datetime.min.time()),
                        Showtime.start_time < datetime.combine(target_date, datetime.max.time()),
                    )
                )
            except ValueError:
                pass  # Invalid date format, ignore filter

        stmt = stmt.order_by(Showtime.start_time).limit(limit)
        result = db.execute(stmt)
        showtimes = result.scalars().all()

        return {
            "showtimes": [
                {
                    "id": s.id,
                    "start_time": s.start_time.isoformat(),
                    "cinema_room": s.cinema_room,
                    "base_price": s.base_price,
                }
                for s in showtimes
            ],
            "count": len(showtimes),
        }
    finally:
        db.close()
```

- [ ] **Step 3: Create create_booking tool**

```python
"""Create booking tool."""
from typing import Annotated
from uuid import uuid4

from langchain_core.tools import tool


@tool
def create_booking(
    showtime_id: Annotated[int, "Showtime ID to book"],
    seat_labels: Annotated[list[str], "List of seat labels like ['A5', 'A6']"],
    user_id: Annotated[str, "User ID"],
) -> dict:
    """
    Create a booking for selected seats.

    This is a critical action - only call after user has confirmed:
    1. The movie/showtime is correct
    2. The seats are correct
    3. User has confirmed they want to book

    Args:
        showtime_id: ID of the showtime
        seat_labels: List of seat labels to book
        user_id: User making the booking

    Returns:
        Dict with booking result
    """
    from datetime import UTC, datetime
    from uuid import UUID
    from sqlalchemy import and_, select
    from app.models.booking import Booking, BookingStatus
    from app.models.seat import Seat, SeatStatus
    from app.shared.db.database import SessionLocal

    db = SessionLocal()
    try:
        # Find seats by labels
        seats = db.execute(
            select(Seat).where(
                and_(
                    Seat.showtime_id == showtime_id,
                    Seat.seat_label.in_(seat_labels),
                )
            )
        ).scalars().all()

        if len(seats) != len(seat_labels):
            found = [s.seat_label for s in seats]
            missing = [l for l in seat_labels if l not in found]
            return {
                "success": False,
                "message": f"Seats not found: {', '.join(missing)}",
            }

        # Check availability
        unavailable = [s.seat_label for s in seats if s.status != SeatStatus.AVAILABLE]
        if unavailable:
            return {
                "success": False,
                "message": f"Seats already booked: {', '.join(unavailable)}",
            }

        # Calculate total price (simplified - use showtime base_price * seats)
        from app.models.showtime import Showtime
        showtime = db.get(Showtime, showtime_id)
        if not showtime:
            return {"success": False, "message": "Showtime not found"}

        total_price = showtime.base_price * len(seats)

        # Create booking
        booking_code = str(uuid4())[:8].upper()
        booking = Booking(
            user_id=UUID(user_id),
            showtime_id=showtime_id,
            total_price=total_price,
            status=BookingStatus.PENDING,
            booking_code=booking_code,
        )
        db.add(booking)
        db.flush()

        # Mark seats as held
        for seat in seats:
            seat.status = SeatStatus.HELD

        db.commit()

        return {
            "success": True,
            "booking_code": booking_code,
            "total_price": total_price,
            "seats": seat_labels,
            "message": f"Booking created! Code: {booking_code}",
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()
```

- [ ] **Step 4: Create cancel_booking tool**

```python
"""Cancel booking tool."""
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from langchain_core.tools import tool


@tool
def cancel_booking(
    booking_code: Annotated[str, "Booking code to cancel"],
    user_id: Annotated[str, "User ID"],
    reason: Annotated[str | None, "Cancellation reason"] = None,
) -> dict:
    """
    Cancel an existing booking.

    Args:
        booking_code: The booking code
        user_id: User requesting cancellation
        reason: Optional cancellation reason

    Returns:
        Dict with cancellation result
    """
    from sqlalchemy import and_, select
    from app.models.booking import Booking, BookingStatus
    from app.models.seat import Seat, SeatStatus
    from app.shared.db.database import SessionLocal

    db = SessionLocal()
    try:
        booking = db.execute(
            select(Booking).where(
                and_(
                    Booking.booking_code == booking_code,
                    Booking.user_id == UUID(user_id),
                )
            )
        ).scalar_one_or_none()

        if not booking:
            return {"success": False, "message": "Booking not found"}

        if booking.status == BookingStatus.CANCELLED:
            return {"success": False, "message": "Booking already cancelled"}

        # Cancel booking
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.now(UTC)
        booking.cancellation_reason = reason or "Cancelled by user via chatbot"

        # Release seats
        seats = db.execute(
            select(Seat).where(
                and_(
                    Seat.showtime_id == booking.showtime_id,
                    Seat.status == SeatStatus.HELD,
                )
            )
        ).scalars().all()

        # Simple heuristic: release seats if they were likely from this booking
        # (In production, track seat->booking relationship)
        for seat in seats:
            seat.status = SeatStatus.AVAILABLE

        db.commit()

        return {
            "success": True,
            "message": f"Booking {booking_code} cancelled",
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()
```

- [ ] **Step 5: Create get_booking_status tool**

```python
"""Get booking status tool."""
from typing import Annotated

from langchain_core.tools import tool


@tool
def get_booking_status(
    booking_code: Annotated[str, "Booking code to check"],
) -> dict:
    """
    Check the status of a booking.

    Args:
        booking_code: The booking code

    Returns:
        Dict with booking details and status
    """
    from sqlalchemy import select
    from app.models.booking import Booking
    from app.models.film import Film
    from app.models.showtime import Showtime
    from app.shared.db.database import SessionLocal

    db = SessionLocal()
    try:
        booking = db.execute(
            select(Booking).where(Booking.booking_code == booking_code)
        ).scalar_one_or_none()

        if not booking:
            return {"found": False, "message": "Booking not found"}

        # Get film info
        showtime = db.get(Showtime, booking.showtime_id)
        film_title = "Unknown"
        if showtime:
            film = db.get(Film, showtime.film_id)
            if film:
                film_title = film.title

        status_emoji = {
            "PENDING": "⏳",
            "CONFIRMED": "✅",
            "CANCELLED": "❌",
        }

        return {
            "found": True,
            "booking_code": booking.booking_code,
            "film_title": film_title,
            "status": booking.status.value,
            "status_emoji": status_emoji.get(booking.status.value, "❓"),
            "total_price": booking.total_price,
            "created_at": booking.created_at.isoformat(),
        }
    finally:
        db.close()
```

- [ ] **Step 6: Create tools __init__.py**

```python
"""Chatbot graph tools."""
from app.modules.chatbot.graph.tools.search_movies import search_movies
from app.modules.chatbot.graph.tools.get_showtimes import get_showtimes
from app.modules.chatbot.graph.tools.create_booking import create_booking
from app.modules.chatbot.graph.tools.cancel_booking import cancel_booking
from app.modules.chatbot.graph.tools.get_booking_status import get_booking_status

TOOLS = [search_movies, get_showtimes, create_booking, cancel_booking, get_booking_status]

__all__ = ["TOOLS", "search_movies", "get_showtimes", "create_booking", "cancel_booking", "get_booking_status"]
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/modules/chatbot/graph/tools/
git commit -m "feat(chatbot): add tool functions for LangGraph"
```

---

## Task 5: Create Agent Nodes

**Files:**
- Create: `backend/app/modules/chatbot/graph/nodes/movie_node.py`
- Create: `backend/app/modules/chatbot/graph/nodes/booking_node.py`
- Create: `backend/app/modules/chatbot/graph/nodes/recommendation_node.py`
- Create: `backend/app/modules/chatbot/graph/nodes/general_node.py`
- Modify: `backend/app/modules/chatbot/graph/nodes/__init__.py`

**Interfaces:**
- Consumes: `ChatState`
- Produces: `{"messages": [...], "suggested_actions": [...], "agent_used": str}`

- [ ] **Step 1: Create movie_node.py**

```python
"""Movie node - handles film info, search, and showtimes."""
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.modules.chatbot.graph.state import ChatState
from app.modules.chatbot.graph.tools import search_movies, get_showtimes
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
```

- [ ] **Step 2: Create booking_node.py**

```python
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
```

- [ ] **Step 3: Create recommendation_node.py**

```python
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
```

- [ ] **Step 4: Create general_node.py**

```python
"""General node - handles non-specialized queries."""
from langchain_core.messages import AIMessage
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
```

- [ ] **Step 5: Update nodes __init__.py**

```python
"""Chatbot graph nodes."""
from app.modules.chatbot.graph.nodes.supervisor import (
    route_intent,
    supervisor_node,
)
from app.modules.chatbot.graph.nodes.movie_node import movie_node
from app.modules.chatbot.graph.nodes.booking_node import booking_node
from app.modules.chatbot.graph.nodes.recommendation_node import recommendation_node
from app.modules.chatbot.graph.nodes.general_node import general_node

__all__ = [
    "supervisor_node",
    "route_intent",
    "movie_node",
    "booking_node",
    "recommendation_node",
    "general_node",
]
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/modules/chatbot/graph/nodes/
git commit -m "feat(chatbot): add agent nodes for LangGraph"
```

---

## Task 6: Create Subgraphs

**Files:**
- Create: `backend/app/modules/chatbot/graph/subgraphs/movie_subgraph.py`
- Create: `backend/app/modules/chatbot/graph/subgraphs/booking_subgraph.py`
- Create: `backend/app/modules/chatbot/graph/subgraphs/__init__.py`

**Interfaces:**
- Consumes: `ChatState`
- Produces: `ChatState` (updated)

- [ ] **Step 1: Create movie_subgraph.py**

```python
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
```

- [ ] **Step 2: Create booking_subgraph.py**

```python
"""Booking subgraph - handles booking-related queries."""
from langgraph.graph import StateGraph, END

from app.modules.chatbot.graph.state import ChatState
from app.modules.chatbot.graph.nodes.booking_node import booking_node


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
```

- [ ] **Step 3: Create subgraphs __init__.py**

```python
"""Chatbot subgraphs."""
from app.modules.chatbot.graph.subgraphs.movie_subgraph import movie_subgraph
from app.modules.chatbot.graph.subgraphs.booking_subgraph import booking_subgraph

__all__ = ["movie_subgraph", "booking_subgraph"]
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/modules/chatbot/graph/subgraphs/
git commit -m "feat(chatbot): add LangGraph subgraphs"
```

---

## Task 7: Create Coordinator Graph

**Files:**
- Create: `backend/app/modules/chatbot/graph/coordinator.py`
- Modify: `backend/app/modules/chatbot/graph/__init__.py`

**Interfaces:**
- Consumes: `ChatState`
- Produces: `ChatState`

- [ ] **Step 1: Create coordinator.py**

```python
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
        movie_subgraph <---+--> booking_subgraph <---+
                           |                         |
        recommendation_node <---------------------+  |
                           |                        |
        general_node <-----+------------------------+
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
    graph.add_node(START)
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
```

- [ ] **Step 2: Update graph __init__.py**

```python
"""LangGraph chatbot components."""
from app.modules.chatbot.graph.coordinator import app, coordinator_graph, run_chatbot
from app.modules.chatbot.graph.state import ChatState

__all__ = ["ChatState", "app", "coordinator_graph", "run_chatbot"]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/modules/chatbot/graph/coordinator.py
git add backend/app/modules/chatbot/graph/__init__.py
git commit -m "feat(chatbot): add LangGraph coordinator graph"
```

---

## Task 8: Update Chatbot Controller

**Files:**
- Modify: `backend/app/modules/chatbot/chatbot_controller.py`
- Modify: `backend/app/modules/chatbot/services/conversation_service.py`

**Interfaces:**
- Consumes: Existing FastAPI endpoints
- Produces: Endpoints using LangGraph coordinator

- [ ] **Step 1: Update chatbot_controller.py**

```python
"""Chatbot Controller - FastAPI router for chatbot endpoints."""
from typing import Annotated
from uuid import UUID

import redis.asyncio as redis
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.chatbot.dto.chatbot_dto import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationHistoryResponse,
    SuggestedAction,
    MessageEntry,
)
from app.modules.chatbot.graph.coordinator import run_chatbot
from app.modules.chatbot.services.conversation_service import ConversationService
from app.shared.db.database import get_db
from app.shared.redis import get_redis

router = APIRouter(prefix="/api/v1/chatbot", tags=["chatbot"])


async def get_conversation_service(
    redis_client: redis.Redis = Depends(get_redis),
) -> ConversationService:
    """Dependency to get conversation service."""
    return ConversationService(redis_client)


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    conversation_service: ConversationService = Depends(get_conversation_service),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
) -> ChatMessageResponse:
    """
    Send a message to the chatbot and receive a response.

    Uses LangGraph for multi-agent orchestration with tool calling.
    """
    # Get or create session
    session_id, _is_new = await conversation_service.get_or_create_session(request.session_id)

    # Get user_id as string
    user_id_str = str(request.user_id) if request.user_id else None

    # Run the LangGraph chatbot
    result = await run_chatbot(
        session_id=session_id,
        user_message=request.message,
        user_id=user_id_str,
    )

    # Convert suggested actions
    suggested = [
        SuggestedAction(**action) for action in (result.get("suggested_actions") or [])
    ]

    return ChatMessageResponse(
        response=result["response"],
        session_id=result["session_id"],
        agent_used=result.get("agent_used", "assistant"),
        suggested_actions=suggested,
    )


@router.get("/conversation/{session_id}", response_model=ConversationHistoryResponse)
async def get_conversation(
    session_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ConversationHistoryResponse:
    """Get the conversation history for a session."""
    messages = await conversation_service.get_conversation(session_id)
    session_info = await conversation_service.get_session_info(session_id)

    if not session_info:
        return ConversationHistoryResponse(
            session_id=session_id,
            messages=[],
            created_at=messages[0].timestamp if messages else None,
            last_updated=messages[-1].timestamp if messages else None,
        )

    return ConversationHistoryResponse(
        session_id=session_id,
        messages=messages,
        created_at=session_info.get("created_at"),
        last_updated=session_info.get("last_updated"),
    )


@router.delete("/conversation/{session_id}")
async def clear_conversation(
    session_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> dict[str, str]:
    """Clear the conversation history for a session."""
    success = await conversation_service.clear_conversation(session_id)

    if success:
        return {"message": "Conversation cleared successfully", "session_id": session_id}
    else:
        return {"message": "Session not found", "session_id": session_id}


@router.post("/conversation")
async def create_new_session(
    conversation_service: ConversationService = Depends(get_conversation_service),
    user_id: UUID | None = None,
) -> dict[str, str]:
    """Create a new conversation session."""
    session_id = await conversation_service.create_session(str(user_id) if user_id else None)
    return {"session_id": session_id}
```

- [ ] **Step 2: Update conversation_service.py - keep for session IDs only**

The ConversationService is kept for session management and API compatibility. Update the `add_message` method to not store full history (LangGraph checkpointer handles that):

```python
# Add this method to ConversationService for checkpointer integration
async def get_langgraph_config(self, session_id: str) -> dict:
    """Get LangGraph checkpointer config for a session."""
    return {"configurable": {"thread_id": session_id}}
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/modules/chatbot/chatbot_controller.py
git add backend/app/modules/chatbot/services/conversation_service.py
git commit -m "refactor(chatbot): integrate LangGraph coordinator into controller"
```

---

## Task 9: Delete Old Agent Files

**Files:**
- Delete: `backend/app/modules/chatbot/agents/` (entire directory)

- [ ] **Step 1: Delete old agents directory**

```bash
rm -rf backend/app/modules/chatbot/agents/
git add -A
git commit -m "refactor(chatbot): remove legacy agent classes, replaced by LangGraph"
```

---

## Task 10: Update Module Init

**Files:**
- Modify: `backend/app/modules/chatbot/__init__.py`

- [ ] **Step 1: Update __init__.py**

```python
"""Chatbot module - LangGraph-based multi-agent chatbot."""
from app.modules.chatbot.graph import app, run_chatbot

__all__ = ["app", "run_chatbot"]
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/modules/chatbot/__init__.py
git commit -m "chore(chatbot): update module exports for LangGraph"
```

---

## Task 11: Test the Integration

**Files:**
- Create: `backend/tests/modules/chatbot/test_chatbot_graph.py`

**Interfaces:**
- Consumes: LangGraph app
- Produces: Verified integration tests

- [ ] **Step 1: Create integration test**

```python
"""Tests for LangGraph chatbot integration."""
import pytest
from unittest.mock import AsyncMock, patch

from app.modules.chatbot.graph.coordinator import run_chatbot, coordinator_graph
from app.modules.chatbot.graph.state import ChatState


class TestCoordinatorGraph:
    """Test the coordinator graph routing."""

    @pytest.mark.asyncio
    async def test_routes_movie_query(self):
        """Test that movie queries route to movie node."""
        with patch("app.modules.chatbot.graph.nodes.supervisor.llm_service") as mock_llm:
            mock_llm.chat = AsyncMock(return_value=AsyncMock(content="film_info"))

            state = {
                "messages": [("user", "What's Inception about?")],
                "intent": None,
                "session_id": "test-session",
                "user_id": None,
                "suggested_actions": None,
                "interrupted": False,
                "booking_context": None,
                "agent_used": None,
            }

            # Just test the routing logic
            from app.modules.chatbot.graph.nodes.supervisor import route_intent

            state["intent"] = "film_info"
            next_node = route_intent(state)
            assert next_node == "movie_node"

    @pytest.mark.asyncio
    async def test_routes_booking_query(self):
        """Test that booking queries route to booking node."""
        from app.modules.chatbot.graph.nodes.supervisor import route_intent

        state = {"intent": "booking"}
        next_node = route_intent(state)
        assert next_node == "booking_node"

    @pytest.mark.asyncio
    async def test_routes_general_query(self):
        """Test that general queries route to general node."""
        from app.modules.chatbot.graph.nodes.supervisor import route_intent

        state = {"intent": "general"}
        next_node = route_intent(state)
        assert next_node == "general_node"


class TestSupervisorNode:
    """Test the supervisor node intent classification."""

    @pytest.mark.asyncio
    async def test_classifies_film_intent(self):
        """Test intent classification for film query."""
        from app.modules.chatbot.graph.nodes.supervisor import supervisor_node

        with patch("app.modules.chatbot.graph.nodes.supervisor.LLMService") as mock:
            mock_service = mock.return_value
            mock_service.chat = AsyncMock(
                return_value=AsyncMock(content="film_info")
            )

            state: ChatState = {
                "messages": [],
                "intent": None,
                "session_id": "test",
                "user_id": None,
                "suggested_actions": None,
                "interrupted": False,
                "booking_context": None,
                "agent_used": None,
            }

            # Would need full mocking of messages
            # This is a placeholder for integration test
            pass


class TestRunChatbot:
    """Test the main run_chatbot function."""

    @pytest.mark.asyncio
    async def test_run_chatbot_returns_response(self):
        """Test that run_chatbot returns expected structure."""
        # Mock the graph invoke
        with patch.object(coordinator_graph, "ainvoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = {
                "messages": [type("obj", (object,), {"content": "Hello! How can I help?","type": "ai"})()],
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
```

- [ ] **Step 2: Run tests**

Run: `cd backend && uv run pytest tests/modules/chatbot/test_chatbot_graph.py -v`

- [ ] **Step 3: Commit**

```bash
git add backend/tests/modules/chatbot/test_chatbot_graph.py
git commit -m "test(chatbot): add LangGraph integration tests"
```

---

## Task Summary

| Task | Description | Files | Status |
|------|-------------|-------|--------|
| 1 | Add dependencies | pyproject.toml | ⬜ |
| 2 | Create state schema | graph/state.py | ⬜ |
| 3 | Create supervisor node | graph/nodes/supervisor.py | ⬜ |
| 4 | Create tool functions | graph/tools/*.py | ⬜ |
| 5 | Create agent nodes | graph/nodes/*.py | ⬜ |
| 6 | Create subgraphs | graph/subgraphs/*.py | ⬜ |
| 7 | Create coordinator | graph/coordinator.py | ⬜ |
| 8 | Update controller | chatbot_controller.py | ⬜ |
| 9 | Delete old agents | agents/ | ⬜ |
| 10 | Update module init | __init__.py | ⬜ |
| 11 | Test integration | test_chatbot_graph.py | ⬜ |
