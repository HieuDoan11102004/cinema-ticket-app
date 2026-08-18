**CineBook**

Online Cinema Ticket Booking Platform

_Project Design & Technical Specification Document_

Version 1.0

August 2026

# Table of Contents

# 1\. Project Overview

CineBook is a full-stack web application that allows users to browse films and showtimes, select seats, book and pay for cinema tickets online, receive personalized film recommendations, and get instant answers from an AI chatbot. The system is designed as a modular monorepo with a decoupled frontend and backend, so each feature area (booking, recommendations, chat) can evolve independently.

## 1.1 Goals

- Provide a smooth, low-friction ticket booking flow from film discovery to payment confirmation.
- Prevent double-booking of seats under concurrent access.
- Personalize film discovery through a recommendation engine.
- Offer conversational self-service support via an AI chatbot grounded in real showtime data.
- Support secure, auditable payments through a third-party payment gateway.

## 1.2 Target Users

- Guests browsing films and schedules without an account.
- Registered users who book tickets, pay, and receive recommendations.
- (Future scope) Cinema staff/admins managing films, showtimes, and seat maps.

## 1.3 Core Features

| **Feature**             | **Description**                                                       |
| ----------------------- | --------------------------------------------------------------------- |
| Authentication          | Sign up, log in, log out, session/token management                    |
| Film & Schedule Listing | Browse films, view details, see showtimes by cinema/date              |
| Ticket Booking          | Select showtime, pick seats, hold seats temporarily, confirm booking  |
| Payment                 | Checkout and pay via a payment gateway; handle success/failure/refund |
| Recommendation System   | Suggest films based on content similarity and/or user history         |
| Chatbot                 | Answer user questions about films, showtimes, and bookings using RAG  |

# 2\. Technology Stack

## 2.1 Frontend

| **Layer**  | **Choice**                   | **Why**                                              |
| ---------- | ---------------------------- | ---------------------------------------------------- |
| Framework  | Next.js (React) + TypeScript | SSR/SSG for SEO on film pages; strong ecosystem      |
| Styling    | Tailwind CSS                 | Fast iteration, consistent design system             |
| State/Data | React Query (TanStack Query) | Caching and syncing server state (films, bookings)   |
| Forms      | React Hook Form + Zod        | Type-safe validation for signup/login/checkout forms |

## 2.2 Backend

| **Layer**       | **Choice**                    | **Why**                                                         |
| --------------- | ----------------------------- | --------------------------------------------------------------- |
| API Framework   | FastAPI (Python)              | Async, fast, automatic OpenAPI docs, strong typing via Pydantic |
| ORM             | SQLAlchemy 2.0 + Alembic      | Mature ORM with migrations for schema evolution                 |
| Auth            | JWT (access + refresh tokens) | Stateless auth that scales horizontally                         |
| Background jobs | APScheduler or Celery + Redis | Release expired seat holds, send emails                         |

## 2.3 Data & Infrastructure

| **Component**    | **Choice**                       | **Why**                                                   |
| ---------------- | -------------------------------- | --------------------------------------------------------- |
| Primary DB       | PostgreSQL                       | Relational integrity for users, films, bookings, payments |
| Cache / Locking  | Redis                            | Seat-hold TTL locks, caching hot film/showtime queries    |
| Containerization | Docker + Docker Compose          | Consistent local/dev/prod environments                    |
| Frontend hosting | Vercel                           | Native Next.js support, edge caching                      |
| Backend hosting  | Railway / Render / Fly.io or VPS | Simple managed deploys for FastAPI + Postgres             |

## 2.4 Feature-Specific Services

| **Feature**      | **Choice**                                                        | **Why**                                           |
| ---------------- | ----------------------------------------------------------------- | ------------------------------------------------- |
| Payments         | Stripe (international) and/or VNPay / MoMo / ZaloPay (local VN)   | Card coverage + locally preferred wallets         |
| Recommendations  | scikit-learn (content-based) / sentence-transformers (embeddings) | Fast to prototype; upgrade path to embeddings     |
| Chatbot          | Claude API with Retrieval-Augmented Generation (RAG) + tool use   | Grounded answers over live film/showtime data     |
| Seed data source | TMDB API (films), Faker/factory_boy (synthetic users/bookings)    | Realistic film metadata plus structured fake data |

# 3\. System Architecture

The system follows a three-tier architecture: a Next.js frontend, a FastAPI backend exposing a versioned REST API, and a PostgreSQL + Redis data layer. The chatbot and recommendation engine run as internal services called by the backend rather than as separate deployable systems, which keeps the initial architecture simple while leaving room to extract them into microservices later if load requires it.

## 3.1 High-Level Flow

- Client (browser) → Next.js frontend → REST API calls → FastAPI backend.
- FastAPI backend → PostgreSQL for persistent data (users, films, bookings, payments).
- FastAPI backend → Redis for ephemeral seat-hold locks and caching.
- FastAPI backend → Payment gateway (Stripe/VNPay) for checkout and webhooks.
- FastAPI backend → Claude API for chatbot responses, with function calls back into the booking/film data.

## 3.2 Seat Locking Flow (Concurrency Control)

This is the most failure-prone part of a booking system, so it is called out explicitly:

- 1\. User selects seats for a showtime → backend checks seat status in Postgres.
- 2\. Backend writes a short-lived hold key to Redis (e.g. TTL = 10 minutes) per seat.
- 3\. If payment succeeds within the TTL, seats are marked 'booked' in Postgres and the Redis hold is cleared.
- 4\. If the TTL expires without payment, the hold is released automatically and seats become available again.
- 5\. A background worker periodically reconciles any orphaned holds.

# 4\. Project Structure

The project is organized as a monorepo with clearly separated frontend and backend codebases.

## 4.1 Backend (FastAPI)

backend/app/

main.py API entrypoint

core/ config, security, shared dependencies

db/ DB session setup, seed scripts

models/ SQLAlchemy ORM models

schemas/ Pydantic request/response models

repository/ database access layer (CRUD operations for each model)

api/v1/ route handlers (auth, films, bookings, payments, ...)

services/ business logic (booking, payment, recommendation, chatbot)

worker/ background tasks (expired seat holds)

backend/tests/ pytest test suite

backend/alembic/ DB migrations

## 4.2 Frontend (Next.js)

frontend/app/

(auth)/login, (auth)/signup auth pages

films/ film listing + detail pages

booking/\[showtimeId\]/ seat selection + checkout

profile/ user profile & booking history

frontend/components/ UI, film cards, seat map, chat widget

frontend/lib/ API client, auth helpers

frontend/hooks/ custom React hooks

frontend/types/ shared TypeScript types

# 5\. Database Schema (Core Entities)

## 5.1 users

| **Column**    | **Type**     | **Notes**             |
| ------------- | ------------ | --------------------- |
| id            | serial       | Primary key, auto-inc |
| first_name    | varchar      |                       |
| last_name     | varchar      |                       |
| email         | varchar, unique | Login identifier    |
| address       | varchar      |                       |
| phone_number  | varchar      |                       |
| birth_date    | date         |                       |
| created_at    | timestamp    |                       |
| updated_at    | timestamp    |                       |

## 5.2 films

| **Column**   | **Type**              | **Notes**                       |
| ------------ | --------------------- | ------------------------------- |
| id           | UUID / serial         | Primary key                     |
| title        | varchar               |                                 |
| genres       | text\[\] / join table | For recommendations & filtering |
| overview     | text                  | Used for embeddings/RAG         |
| poster_url   | varchar               |                                 |
| duration_min | int                   |                                 |
| release_date | date                  |                                 |
| tmdb_id      | int                   | Reference back to source data   |

## 5.3 showtimes

| **Column**  | **Type**       | **Notes**   |
| ----------- | -------------- | ----------- |
| id          | UUID / serial  | Primary key |
| film_id     | FK -> films.id |             |
| cinema_room | varchar        |             |
| start_time  | timestamp      |             |
| base_price  | numeric        |             |

## 5.4 seats

| **Column**  | **Type**           | **Notes**                 |
| ----------- | ------------------ | ------------------------- |
| id          | UUID / serial      | Primary key               |
| showtime_id | FK -> showtimes.id |                           |
| seat_label  | varchar            | e.g. 'A5'                 |
| status      | enum               | available / held / booked |

## 5.5 bookings & payments

| **Column**        | **Type**           | **Notes**                               |
| ----------------- | ------------------ | --------------------------------------- |
| id                | UUID / serial      | Primary key                             |
| user_id           | FK -> users.id     |                                         |
| showtime_id       | FK -> showtimes.id |                                         |
| seat_ids          | array / join table | Seats included in this booking          |
| status            | enum               | pending / confirmed / cancelled         |
| payment_id        | FK -> payments.id  |                                         |
| payments.provider | varchar            | stripe / vnpay / momo                   |
| payments.status   | enum               | pending / succeeded / failed / refunded |
| payments.amount   | numeric            |                                         |

# 6\. API Endpoints (v1)

## 6.1 Auth

| **Method** | **Endpoint**         | **Description**                                |
| ---------- | -------------------- | ---------------------------------------------- |
| POST       | /api/v1/auth/signup  | Create a new user account                      |
| POST       | /api/v1/auth/login   | Authenticate and receive access/refresh tokens |
| POST       | /api/v1/auth/logout  | Invalidate refresh token                       |
| POST       | /api/v1/auth/refresh | Issue a new access token                       |

## 6.2 Films & Schedule

| **Method** | **Endpoint**                 | **Description**                            |
| ---------- | ---------------------------- | ------------------------------------------ |
| GET        | /api/v1/films                | List films (filter by genre, date, search) |
| GET        | /api/v1/films/{id}           | Film detail                                |
| GET        | /api/v1/films/{id}/showtimes | Showtimes for a film                       |

## 6.3 Booking & Payment

| **Method** | **Endpoint**                  | **Description**                          |
| ---------- | ----------------------------- | ---------------------------------------- |
| GET        | /api/v1/showtimes/{id}/seats  | Seat map with current status             |
| POST       | /api/v1/bookings/hold         | Place a temporary hold on selected seats |
| POST       | /api/v1/bookings/{id}/confirm | Confirm booking after payment success    |
| GET        | /api/v1/bookings/me           | Current user's booking history           |
| POST       | /api/v1/payments/checkout     | Create a payment session/intent          |
| POST       | /api/v1/payments/webhook      | Receive payment provider webhook events  |

## 6.4 Recommendations & Chatbot

| **Method** | **Endpoint**            | **Description**                              |
| ---------- | ----------------------- | -------------------------------------------- |
| GET        | /api/v1/recommendations | Personalized or similar-film recommendations |
| POST       | /api/v1/chatbot/message | Send a user message, receive chatbot reply   |

# 7\. Feature Details

## 7.1 Authentication

- Passwords hashed with bcrypt/argon2; never stored in plaintext.
- JWT access token (short-lived, ~15 min) + refresh token (long-lived, stored httpOnly cookie).
- Logout invalidates the refresh token server-side (denylist or rotation).

## 7.2 Film & Schedule Listing

- Film list supports filtering by genre, date, and text search.
- Showtimes grouped by cinema room and date for easy scanning.

## 7.3 Ticket Booking

- Seat map rendered from the seats table, colored by status (available/held/booked).
- Selecting seats triggers a hold request; Redis TTL enforces the hold window.
- Booking only becomes 'confirmed' after payment webhook confirms success.

## 7.4 Recommendation System

- Phase 1 (content-based): cosine similarity over genre/cast/overview vectors using scikit-learn.
- Phase 2 (embeddings): sentence-transformers embeddings over film overviews for semantic similarity.
- Phase 3 (collaborative): incorporate booking history once sufficient user data exists (e.g. MovieLens-style matrix factorization).

## 7.5 Chatbot

- Backed by the Claude API using Retrieval-Augmented Generation over film/showtime data.
- Uses tool calling so the model can query live showtimes/bookings rather than hallucinate.
- Scoped to cinema-related questions; falls back gracefully outside that scope.

## 7.6 Payment

- Stripe for international card payments; VNPay/MoMo/ZaloPay for local Vietnamese payment methods.
- Webhook-driven confirmation, not client-side confirmation, to avoid trusting the browser.
- Refund flow supported for cancelled bookings within policy windows.

# 8\. Development Roadmap

| **Phase** | **Scope**                                                               |
| --------- | ----------------------------------------------------------------------- |
| 1         | Auth + film listing/schedule (core CRUD), seed real film data from TMDB |
| 2         | Booking flow + seat locking (Redis holds, concurrency handling)         |
| 3         | Payment integration (Stripe and/or local gateway) + webhook handling    |
| 4         | Recommendation system (content-based first, embeddings next)            |
| 5         | Chatbot (RAG + tool use over film/showtime data)                        |
| 6         | Polish: admin tooling, analytics, performance/caching pass              |

# 9\. Non-Functional Requirements

- Security: HTTPS everywhere, hashed passwords, parameterized queries via ORM, payment webhook signature verification.
- Reliability: seat holds must never allow two confirmed bookings for the same seat/showtime.
- Performance: film listing and seat map queries cached in Redis for hot showtimes.
- Scalability: stateless FastAPI instances behind a load balancer; JWT auth avoids server-side session state.
- Observability: structured logging for booking/payment state transitions; alerting on failed webhook deliveries.
