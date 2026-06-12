# Xeno Mini CRM — AI-Native Campaign Platform

A full-stack AI-native CRM that helps consumer brands decide **who to talk to**, **what to say**, and **how they performed** — with an AI Copilot at the centre of the workflow.

---

## Product Bet

I built a **chat-first + dashboard hybrid**. The primary interface is a natural-language Copilot powered by a LangGraph ReAct agent. The marketer describes a goal; the Copilot segments the audience, drafts the message, confirms details, and executes the campaign — all through conversation. Traditional CRUD views (Customers, Segments, Campaigns) exist as secondary views for transparency and control.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Xeno Mini CRM                                 │
├─────────────────┬───────────────────────────┬───────────────────────────┤
│   Frontend      │       CRM Backend          │     Channel Service       │
│  React + Vite   │  FastAPI + PostgreSQL       │   FastAPI (stub)          │
│  Port 3000      │     Port 8000              │    Port 8001              │
│                 │                            │                           │
│ ┌───────────┐   │  ┌─────────────────────┐  │  ┌────────────────────┐  │
│ │ Copilot   │◄─SSE─►│  /api/agent/chat   │  │  │  Delivery          │  │
│ │ (Chat UI) │  │  │  LangGraph ReAct     │  │  │  Simulator         │  │
│ └───────────┘  │  │  Agent + Groq LLaMA  │  │  │  (async tasks)     │  │
│                │  └─────────────────────┘  │  └────────────────────┘  │
│ ┌───────────┐  │  ┌─────────────────────┐  │           │               │
│ │Dashboard  │──┼──►│  REST APIs         │──┼───POST /send──────────────►│
│ │Segments   │  │  │  customers/segments/│  │           │               │
│ │Campaigns  │  │  │  campaigns/receipts │◄─┼──POST /api/receipts/──────┤
│ └───────────┘  │  └─────────────────────┘  │  (delivery events)        │
└─────────────────┴───────────────────────────┴───────────────────────────┘
                                  │
                      ┌───────────▼───────────┐
                      │      PostgreSQL        │
                      │  customers · orders   │
                      │  segments · campaigns │
                      │  communications       │
                      └───────────────────────┘
```

### Two-service delivery loop

1. CRM creates campaign + per-recipient `Communication` rows in the DB
2. CRM calls `POST /send` on the Channel Service (fire-and-forget)
3. Channel Service responds **202 immediately** and simulates delivery in background asyncio tasks
4. For each communication, the Channel Service waits a random delay then `POST /api/receipts/` back to the CRM with a delivery event (`sent`, `delivered`, `failed`, `opened`, `read`, `clicked`, `converted`)
5. CRM receipt handler updates the `Communication` status and increments campaign counters — idempotently
6. Frontend polls running campaigns every 3 seconds; the dashboard updates live

---

## AI Agent Design

The Copilot uses a **LangGraph ReAct agent** backed by **Groq LLaMA-3.3-70b**.

### Tools

| Tool | What it does |
|------|-------------|
| `get_customer_stats` | Overview: total customers, revenue, city distribution |
| `preview_segment` | Count customers matching rules — validate before saving |
| `create_segment` | Save a named segment with JSON rules to the DB |
| `list_segments` | Browse existing segments |
| `launch_campaign` | Create campaign, build communications, fire to channel service |
| `get_campaign_analytics` | Delivery + engagement rates for a campaign |
| `list_campaigns` | Overview of all campaigns |

### Segment rules engine

Rules are stored as JSON and evaluated at query time by the `segment_engine.py` module, which translates them into SQLAlchemy conditions. Supported fields: `total_spent`, `total_orders`, `days_since_last_order`, `city`, `created_within_days`. Conditions can be combined with `AND` / `OR`.

```json
{
  "operator": "AND",
  "conditions": [
    {"field": "total_spent",           "operator": "gte", "value": 5000},
    {"field": "days_since_last_order", "operator": "gte", "value": 60},
    {"field": "city",                  "operator": "in",  "value": ["Mumbai", "Delhi"]}
  ]
}
```

---

## Tech Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| CRM Backend | FastAPI + SQLAlchemy | Async-friendly, clean DI, great for SSE streaming |
| Database | PostgreSQL | Relational integrity for campaigns/comms; JSON columns for rules/items |
| AI | LangGraph + Groq LLaMA-3.3 | ReAct agent with real tool use; Groq for speed |
| Channel Service | FastAPI | Separate service, asyncio background tasks, easy to swap for real provider |
| Frontend | React + Vite + Tailwind | Fast DX, TypeScript safety, Recharts for metrics |
| Infrastructure | Docker Compose | One-command local dev; maps cleanly to Railway/Render for production |

---

## Quick Start

### Prerequisites
- Docker + Docker Compose
- A [Groq API key](https://console.groq.com)

### Run locally

```bash
git clone <your-repo-url>
cd xeno-crm

# Add your Groq key
echo "GROQ_API_KEY=your_key_here" > .env

# Start all services
docker-compose up --build
```

The database is migrated and seeded automatically with 100 realistic customers.

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| CRM API + Swagger | http://localhost:8000/docs |
| Channel Service | http://localhost:8001/docs |

### Running without Docker (local dev)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in GROQ_API_KEY + DATABASE_URL
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000

# Channel service (new terminal)
cd channel-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Frontend (new terminal)
cd frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev
```

---

## Walkthrough — Copilot Demo Script

1. Open **AI Copilot** tab
2. Type: *"Show me my customer base overview"*
   → Agent calls `get_customer_stats`, returns revenue, city breakdown
3. Type: *"Find customers who spent over ₹5000 but haven't ordered in 60 days"*
   → Agent calls `preview_segment` to validate count, then `create_segment`
4. Type: *"Launch a WhatsApp win-back campaign to this segment with a 20% discount offer"*
   → Agent drafts message, confirms plan, calls `launch_campaign`
5. Switch to **Campaigns** tab — watch delivery stats update live as the channel simulator fires callbacks
6. Back in Copilot: *"How is the campaign performing?"*
   → Agent calls `get_campaign_analytics`, returns delivery/click/conversion rates

---

## API Reference

```
GET  /api/customers/             List customers (filter by city)
POST /api/customers/             Create customer
POST /api/customers/import/csv   Bulk CSV import
GET  /api/customers/stats/overview  Aggregate stats

POST /api/orders/                Create order (updates customer aggregates)

POST /api/segments/preview       Count matching customers (no save)
POST /api/segments/              Create segment
GET  /api/segments/              List segments
GET  /api/segments/{id}/customers  Customers in segment

POST /api/campaigns/             Create campaign (draft)
POST /api/campaigns/{id}/launch  Launch campaign → fires to channel service
GET  /api/campaigns/             List campaigns
GET  /api/campaigns/stats/overview  All-time stats
GET  /api/campaigns/{id}/communications  Per-recipient statuses

POST /api/receipts/              Delivery event callback (from channel service)

POST /api/agent/chat             SSE-streaming AI agent endpoint
POST /api/agent/chat/sync        Non-streaming fallback
```

---

## Scale Assumptions & Trade-offs

| Decision | What I did | What I'd do at scale |
|----------|-----------|---------------------|
| Segment evaluation | Query-time SQLAlchemy filter | Pre-compute and cache segment membership; CDC to invalidate |
| Customer aggregates | Denormalised on customer row | Keep for read performance; update via DB trigger or event stream |
| Delivery callbacks | Direct HTTP POST to CRM | Kafka/SQS queue between channel service and CRM; idempotent consumer |
| Campaign execution | Single DB write + HTTP fire | Chunk large campaigns (>10k); use Celery workers with retry logic |
| AI agent | Stateless per-request invoke | Session memory in Redis; persist conversation IDs |
| Auth | None (assignment scope) | JWT + row-level tenancy for multi-brand isolation |
| Polling | 3s frontend poll for live stats | WebSocket or SSE push from CRM when counters change |

The receipt handler is already **idempotent** (checks if timestamp already set before processing), which is the most important property for a production callback system.

---

## Project Structure

```
xeno-crm/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, router registration
│   │   ├── config.py            # Pydantic settings from env
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── api/                 # Route handlers
│   │   │   ├── receipts.py      # ← Callback from channel service
│   │   │   └── agent.py         # ← SSE streaming AI endpoint
│   │   ├── agents/
│   │   │   ├── graph.py         # LangGraph ReAct agent
│   │   │   ├── tools.py         # Agent tools (CRM operations)
│   │   │   └── prompts.py       # System prompt
│   │   ├── services/
│   │   │   ├── segment_engine.py # JSON rules → SQLAlchemy query
│   │   │   └── channel_client.py # HTTP client to channel service
│   │   └── seed.py              # 100 realistic demo customers
│   └── alembic/                 # DB migrations
├── channel-service/
│   ├── app/
│   │   ├── main.py              # Accepts send requests, responds 202
│   │   └── simulator.py         # Async delivery simulation engine
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Copilot.tsx      # SSE-streaming chat interface
│       │   ├── Dashboard.tsx    # Stats + charts
│       │   ├── Customers.tsx    # Table + CSV import
│       │   ├── Segments.tsx     # Rule builder + preview
│       │   └── Campaigns.tsx    # Detail + funnel chart + live polling
│       └── lib/api.ts           # Typed API client + SSE helper
└── docker-compose.yml
```
