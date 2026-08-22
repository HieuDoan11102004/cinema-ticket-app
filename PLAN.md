# Multi-Agent Chatbot Implementation Plan

## Context

The user wants to build a multi-agent chatbot system for the CineBook cinema ticket platform. Currently, no chatbot implementation exists — the codebase has a planned `/api/v1/chatbot/*` endpoint but no code. The system needs a primary assistant that routes queries to specialized agents (Movie Agent, Booking Agent), following the existing FastAPI module patterns.

## Architecture Overview

```
User Message
     │
     ▼
┌─────────────────────────┐
│   Primary Assistant     │  ← Intent classification, routing
│   (Orchestrator Agent) │
└───────────┬─────────────┘
            │
    ┌───────┼───────┐
    ▼       ▼       ▼
┌───────┐ ┌───────┐ ┌────────────┐
│Movie  │ │Booking │ │  (Future)  │
│Agent  │ │ Agent  │ │  More...   │
└───┬───┘ └───┬───┘ └────────────┘
    │         │
    ▼         ▼
 Database   Database
 (Films)    (Bookings)
```

## Recommended Approach

### 1. LLM Integration

Use **OpenAI GPT API** via `httpx.AsyncClient` following the existing `tmdb_client.py` pattern:
- API keys in `config.yaml` + `.env`
- Async HTTP calls with proper error handling
- Configurable model (default: `gpt-4o-mini` for cost efficiency)
- System prompts for each agent to define their behavior

### 2. Agent Design

| Agent | Responsibility | Tools/Capabilities |
|-------|-----------------|---------------------|
| **Primary Assistant** | Intent classification, query routing, response synthesis | Classify user intent → delegate to specialized agents |
| **Movie Agent** | Film info, showtimes, recommendations | Query films, showtimes, seat availability |
| **Booking Agent** | Create/cancel bookings, booking history | Create holds, confirm bookings, view/cancel existing bookings |

### 3. Conversation Management

Store conversation context in **Redis**:
- Session-based conversations (TTL: 30 minutes)
- Conversation history per user
- Agent handoff state tracking

---

## Implementation Plan

### Phase 1: Core Infrastructure

**Files to create:**
- `backend/app/modules/chatbot/__init__.py`
- `backend/app/modules/chatbot/agents/base_agent.py` — Abstract base class for all agents
- `backend/app/modules/chatbot/services/llm_service.py` — LLM API client
- `backend/app/modules/chatbot/services/conversation_service.py` — Redis-based conversation management
- `backend/app/modules/chatbot/dto/chatbot_dto.py` — Request/Response models

**Files to modify:**
- `backend/app/__init__.py` — Register chatbot router
- `config.yaml` — Add LLM provider settings
- `.env` — Add `OPENAI_API_KEY`

### Phase 2: Primary Assistant Agent

**Files to create/modify:**
- `backend/app/modules/chatbot/agents/primary_assistant.py` — Intent classification + routing

**Primary Assistant capabilities:**
```
INTENTS:
  - film_info:    "What movies are showing?", "Tell me about [movie]"
  - showtimes:    "Show me showtimes for [movie]", "When is [movie] playing?"
  - booking:      "I want to book tickets", "Book seats for [movie]"
  - cancel:       "Cancel my booking", "I want to cancel"
  - booking_status: "What's my booking status?", "Show my bookings"
  - recommendation: "What do you recommend?", "Suggest a movie"
  - general:      Anything else → conversational response
```

### Phase 3: Movie Agent

**Files to create/modify:**
- `backend/app/modules/chatbot/agents/movie_agent.py`
- `backend/app/modules/films/films_service.py` — May need new methods for chatbot queries

**Movie Agent capabilities:**
- Search films by title, genre, actor
- Get film details (description, runtime, rating, poster)
- List currently showing films
- Get showtimes for specific films
- Check seat availability for showtimes
- Generate recommendations based on preferences

### Phase 4: Booking Agent

**Files to create/modify:**
- `backend/app/modules/chatbot/agents/booking_agent.py`
- `backend/app/modules/bookings/bookings_service.py` — May need new methods

**Booking Agent capabilities:**
- Start booking flow (select showtime, seats)
- Create seat holds (via Redis)
- Confirm booking (after payment)
- View user's bookings
- Cancel booking
- Handle payment status

### Phase 5: API Endpoints

**Files to create/modify:**
- `backend/app/modules/chatbot/chatbot_controller.py` — FastAPI router

**Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/chatbot/message` | Send message, receive response |
| GET | `/api/v1/chatbot/conversation` | Get conversation history |
| DELETE | `/api/v1/chatbot/conversation` | Clear conversation |
| POST | `/api/v1/chatbot/confirm-booking` | Confirm booking from chat |
| POST | `/api/v1/chatbot/cancel-booking` | Cancel booking from chat |

---

## Critical Files to Modify

| File | Change |
|------|--------|
| `backend/app/__init__.py` | Import and register `chatbot_router` |
| `backend/app/shared/core/config.py` | Add LLM config loading |
| `config.yaml` | Add `llm:` section with provider, model, api_key |
| `.env` | Add `OPENAI_API_KEY=sk-...` |

## Reusable Patterns to Follow

From existing code:
- **External API calls**: `modules/films/tmdb_client.py` — `httpx.AsyncClient` pattern
- **Redis integration**: `modules/seats/seat_lock_service.py` — Redis Lua scripts
- **Service/repository pattern**: All existing modules follow this
- **DTO patterns**: Standardized Pydantic models in `dto/` folders
- **Dependency injection**: `Depends(get_db)`, `Depends(get_redis)`

---

## API Contract

### Request
```json
POST /api/v1/chatbot/message
{
  "message": "What movies are showing tonight?",
  "user_id": "uuid-string",  // Optional, for authenticated users
  "session_id": "optional-session-id"
}
```

### Response
```json
{
  "response": "Here are the movies showing tonight at CineBook:\n\n1. **Dune: Part Three** - Sci-Fi, Adventure - 9.2/10\n2. **The Batman** - Action, Crime - 8.5/10\n...",
  "session_id": "uuid-session-id",
  "agent_used": "movie_agent",
  "suggested_actions": [
    {"label": "Book tickets for Dune", "action": "book", "film_id": 5},
    {"label": "See showtimes", "action": "showtimes", "film_id": 5}
  ]
}
```

---

## Verification Plan

1. **Unit tests**: Test each agent's intent classification and response generation
2. **Integration tests**: Test full conversation flows with mocked LLM
3. **Manual testing**: Send messages via Swagger UI (`/docs`)
4. **End-to-end test**:
   - Start server: `cd backend && uv run uvicorn app:app --reload`
   - Send message: `curl -X POST http://localhost:8000/api/v1/chatbot/message -H "Content-Type: application/json" -d '{"message": "What movies are playing?"}'`
   - Verify response contains film information
   - Test booking flow end-to-end

## Optional Enhancements (Future)

- **Recommendation Agent**: AI-powered movie suggestions
- **Payment Agent**: Handle payment webhook events
- **Multi-language support**: Vietnamese/English
- **Streaming responses**: Server-sent events for real-time typing effect
- **Memory agent**: Long-term user preference learning

---

## Estimated Complexity

- **Phase 1-2 (Core + Primary Assistant)**: ~2-3 hours
- **Phase 3-4 (Movie + Booking Agents)**: ~3-4 hours
- **Phase 5 (API Endpoints)**: ~1-2 hours
- **Total**: ~6-9 hours for basic implementation
