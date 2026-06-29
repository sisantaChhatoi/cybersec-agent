# RAG Fraud-Chat & Fraud-Graph Intelligence

Context file for Claude Code. Lives at the root of `rag-graph/` once merged
into the main `cybersec-agent` repo (this folder is currently developed in
its own repo and pushed into `cybersec-agent`'s `rag_chat` branch as a
self-contained `rag-graph/` subfolder).

## Code style

- Clean, PEP 8 / PEP 20 code. Type-annotate signatures.
- **Minimal comments.** No verbose docstrings. Comment only non-obvious
  *why* (a workaround, an invariant, a known model failure mode it's
  guarding against) — not *what*. Let names carry intent.

## What this is

Two coupled pieces:
1. **`src/rag/`** — a multilingual chat assistant (Hindi/Hinglish/English).
   Someone describes a suspicious call/message, gets a grounded,
   in-language risk verdict, while the system quietly extracts the
   structured details (caller number, mule account/UPI, amount, region)
   that matter for tracing the scam network behind it.
2. **`src/graph/`** — turns those extracted incidents into a fraud network
   graph (NetworkX local + Neo4j Aura) that surfaces reused mule
   accounts/UPI handles, fraud rings (Louvain community detection),
   multi-region operations, and investigative-support evidence reports.

This is **not currently wired into the main app or backend** (`app/`,
`backend/server`). It was built and tested standalone via a CLI
(`python -m src.rag.ask`). See "Integrating into the real app" below for
exactly what that takes.

## Architecture

```
User chats (Hindi / Hinglish / English)
        |
        v
src/rag/   RAG chat: multilingual embeddings + FAISS retrieval over a fraud
        |  knowledge base -> Sarvam-30B generates a grounded, in-language
        |  reply -> a background pass extracts structured fields one at a
        |  time (each graph-relevant field is asked at most once, ever)
        v
MongoDB: <db>.incidents  <- source of truth (currently a separate Atlas
        |  cluster, see "Integrating" below for why that needs to change)
        |
        | every save also auto-syncs that one incident into Neo4j right
        | away (idempotent -- safe as the same incident gains fields over
        | a conversation), so the graph stays current with zero manual
        | steps. python -m src.graph.neo4j_run is only needed for a full
        | rebuild (e.g. after deleting incidents, which doesn't auto-propagate)
        v
src/graph/  builds a fraud network graph from incidents, two backends:
        |     - local: in-memory NetworkX graph + Louvain community detection
        |     - Neo4j Aura: pushed as a real graph DB, Cypher pattern
        |       queries, Louvain still runs in NetworkX (Aura's free tier
        |       has no Graph Data Science plugin)
        v
Fraud rings, reused/high-risk accounts, jurisdiction overlap, and
evidence-style reports -- persisted to MongoDB AND exported as local files
```

## Key files

- `src/rag/chat.py` — `chat_turn()` / `chat_turn_stream(session_id, message)`
  are the only entry points a caller needs. Already accepts an externally
  supplied id rather than generating one — `ask.py` generates a throwaway
  `cli-<uuid>` for standalone testing, but any other caller (e.g. a FastAPI
  route) can pass its own id straight through.
- `src/rag/incident.py` — the `Incident` schema (graph-ready fields:
  `caller_number`, `mule_account`, `mule_upi`, `victim_region`,
  `amount_demanded`, `amount_lost`, `scam_type`...). Fields are filled once
  and locked; each is nudged at most once per conversation, ever
  (`EXTRACTABLE_FIELDS`, `next_missing_field()`). Guards against a known
  model failure mode where two questions get conflated into one reply and
  the user's single answer gets misattributed to two different identity
  fields (`_resolve_identity_conflict`).
- `src/rag/incident_store.py` — persists to MongoDB (falls back to local
  JSONL if Mongo is unreachable), and best-effort auto-syncs every save
  into Neo4j.
- `src/graph/` — `build.py`/`analyze.py`/`report.py` (local NetworkX
  pipeline), `neo4j_load.py`/`neo4j_queries.py`/`neo4j_run.py` (Neo4j Aura
  pipeline), `ring_intelligence.py`/`jurisdiction.py`/`court_reports.py`
  (confidence-scored fraud rings, region→state jurisdiction mapping,
  evidence report generation).

## Stack

| Concern         | Choice                                    |
|------------------|-------------------------------------------|
| Chat LLM         | Sarvam `sarvam-30b` (OpenAI-compatible API) |
| Retrieval        | FAISS (`faiss-cpu`), local, in-process |
| Embeddings       | `paraphrase-multilingual-MiniLM-L12-v2` (HuggingFace, CPU) |
| Storage          | MongoDB Atlas (separate cluster from the main app's `mongo:7` container) |
| Graph DB         | Neo4j Aura (free tier, no GDS plugin — Louvain runs in NetworkX) |

## Integrating into the real app

The app already has a working chat surface: `backend/server/chatbot/`
(router → service → `ChatbotEngine.stream_reply()`), backed by a generic
Groq call with no RAG, no fraud knowledge, no field extraction — it's a
placeholder. The goal is to replace what's *inside* `ChatbotEngine`, not
add a new endpoint; the app already calls the right shape of endpoint
(`POST /chatbot/chats/{id}/messages`, SSE token stream).

Three concrete mismatches to resolve before that swap:

1. **LLM client** — `backend/server/chatbot/engine.py` uses Groq via
   LangChain; this module calls Sarvam directly via an OpenAI-compatible
   client. Either wrap this module's logic behind the same
   `stream_reply(history, message) -> AsyncIterator[str]` shape, or accept
   running two different LLM providers side by side.
2. **Mongo** — the main app uses one shared `mongo:7` container
   (`backend/shared/db.py`, async `AsyncMongoClient`, settings via
   `backend/shared/config.py`). This module currently points at a separate
   MongoDB Atlas cluster via sync `pymongo` (`src/rag/incident_store.py`).
   These need to converge onto one Mongo instance.
3. **Identity** — the main app's chats are scoped to an authenticated
   `user_id` (JWT, tied to `phone_no` in the `users` collection, which
   already collects `state`/`city`/`pin` at signup). This module's
   `Incident.session_id` is just whatever string the caller passes in —
   already flexible enough to accept the app's `chat_id`/`user_id` instead
   of generating its own, with no code change needed on this side. The
   open question is which id(s) the integration should pass through.

Geospatial hotspot work (a planned extension of `src/graph/`) is blocked on
#3 specifically: the app's `users.pin` (precise, geocodable) only becomes
usable for incident-level mapping once a chat session is linkable back to a
real `user_id` — until then, hotspot mapping can only use the free-text
`victim_region` collected per-incident (city-level precision at best).

## Run commands

```powershell
pip install -r requirements.txt

# Knowledge base index (once, or after editing src/rag/knowledge_base/*.md)
python -m src.rag.ingest

# Chat (standalone CLI, for testing without the real app)
python -m src.rag.ask

# Fraud graph, once a few incidents exist
python -m src.graph.run                     # local NetworkX
python -m src.graph.neo4j_run                 # push to Neo4j + basic Cypher analysis
python -m src.graph.neo4j_intelligence_run    # full intelligence packages + evidence reports
```

`.env` needed: `SARVAM_API_KEY`, `MONGODB_URI`, `NEO4J_URI`,
`NEO4J_USERNAME`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`.

## Honest limitations

See the root `README.md` in this folder for the full list (confidence
scores are a documented heuristic not a legal determination, account
linkage is inferred from shared calling infrastructure not bank
transaction data, victim identity is never collected today, jurisdiction
mapping is a small static lookup table not authoritative data).
