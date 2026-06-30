# `rag-graph/` — What's Implemented (Teammate Contribution Overview)

> A grounded read of the `rag-graph/` module added in commit `3dc4811`
> ("Add RAG fraud-chat + fraud-graph intelligence module"). Both halves are
> verified against the actual code, not just her READMEs.

---

## TL;DR — how much it helps

She built a **self-contained fraud-intelligence subsystem** in two halves that
share one MongoDB collection as the hand-off:

1. **RAG fraud-chat** — a multilingual (Hindi / Hinglish / English) assistant.
   A user describes a suspicious call/message and gets a retrieval-grounded,
   in-language safety reply, while the system **silently extracts structured
   scam-incident fields in the background** and persists them.
2. **Graph intelligence** — turns those stored incidents into a **fraud
   network graph** (NetworkX locally, Neo4j Aura optionally) and surfaces
   reused mule accounts, fraud rings, regional/jurisdiction overlap, and
   evidence-style reports.

This is a **genuinely substantial contribution** (~3,600 lines), and it lines
up with the two things she was asked to own: **the RAG part and graph
intelligence**. It runs as a standalone Python package (`python -m src.rag.*`
/ `python -m src.graph.*`); it is **not yet wired into our FastAPI backend or
the app** — integration is the work left for us.

---

## Capabilities she added

- **Multilingual grounded chat** over a curated fraud knowledge base
  (digital-arrest, courier/KYC/UPI/job/investment/lottery scams, reporting
  procedures, cybercrime glossary) — replies in the user's own language/script.
- **Retrieval pipeline**: local multilingual embeddings + FAISS vector search
  with a relevance floor so short replies don't pull in junk context.
- **Passive incident capture**: as the victim chats, scam fields (caller
  number, mule account / UPI, amounts, region, scam type, claimed authority,
  payment method, remote-app request) are extracted by a background LLM pass
  and stored — the user never fills a form.
- **Conversation-quality engineering**: ask-each-field-once slot filling (no
  nagging loops), a repetition guard against the model repeating itself,
  bare-negation suppression, streaming replies, multi-turn memory that
  survives process restart.
- **Durable persistence with graceful fallback**: MongoDB Atlas, auto-falling
  back to a local JSONL file when Mongo is unreachable.
- **Fraud network graph construction** from incidents (entities = mule
  accounts, phone numbers, UPI IDs, victim regions; edges = co-occurrence in
  the same incident).
- **Ring detection & risk scoring**: Louvain community detection (fraud
  rings) + per-entity risk scores; reused-account and multi-region detection.
- **Two graph backends**: in-memory NetworkX (no external DB needed) and
  Neo4j Aura (real graph DB + Cypher pattern queries).
- **Intelligence/evidence layer**: confidence-scored rings (documented
  heuristic), ring core-member identification, region→state jurisdiction
  mapping, chronological evidence chains, and exported reports
  (`.graphml`, JSON, text, a quick PNG visualization).

---

## Subsystem 1 — RAG fraud-chat (`src/rag/`) — code-verified

### Stack
| Concern | Choice |
| --- | --- |
| LLM (reply + field extraction) | **Sarvam `sarvam-30b`** via the `openai` SDK pointed at `https://api.sarvam.ai/v1` |
| Embeddings | **`paraphrase-multilingual-MiniLM-L12-v2`** (sentence-transformers, CPU, ~470 MB first download) |
| Vector store | **FAISS** (`IndexFlatIP`, exact cosine over normalized vectors) |
| Storage | **MongoDB** (`pymongo`) → falls back to local `data/rag/incidents.jsonl` |

### End-to-end flow
**Offline (once / on KB change):** `ingest.py` chunks `knowledge_base/*.md`
(~350-token greedy packing) → embeds → builds `data/rag/index.faiss` +
`chunks.json`. *(Already prebuilt and committed: 29 chunks.)*

**Per chat turn (`chat.py`):**
1. Embed the user message → FAISS search → drop matches below `score 0.35` →
   format as `(source: …) text`.
2. `incident.next_missing_field()` picks at most **one** graph-relevant field
   to gently ask about (each field asked at most once, ever).
3. System prompt + history + retrieved context + the single nudge → Sarvam →
   reply.
4. **Repetition guard** compares the draft to recent replies (`difflib`); if
   near-duplicate, retries once at higher temperature, else uses a templated
   fallback.
5. A **separate background thread** extracts structured fields from the full
   transcript (Sarvam, JSON mode) → merges into the session `Incident` →
   `save_session()`. This never blocks the reply.

### Key files
- `embedder.py` — loads the multilingual model once; returns normalized vectors.
- `vector_store.py` — FAISS build/save/load/search wrapper.
- `ingest.py` — offline index builder (`python -m src.rag.ingest`).
- `retriever.py` — query embed + search + relevance filter.
- `chat.py` (551 lines) — the orchestrator. **Library, not a CLI**; exposes
  `chat_turn()` and `chat_turn_stream()` (the only two functions a UI needs).
  Holds the system prompts, nudge/slot logic, repetition guard, streaming,
  and the background extraction worker. In-process session cache lazily
  rehydrated from storage (memory survives restarts).
- `incident.py` — Pydantic `Incident` schema + `ScamType` enum; "fill once
  then lock" merge logic to resist hallucinated overwrites; placeholder-value
  rejection ("unknown", "n/a", …).
- `incident_store.py` — Mongo upsert by `session_id` (+ full transcript), with
  JSONL fallback. **Runs without Mongo.**
- `knowledge_base/*.md` — 4 advisory docs (~647 lines) RAG retrieves from.
- `ask.py` — the actual test CLI: interactive / one-shot / `--stream` /
  `--session <id>`.

### Entry points & env
- `python -m src.rag.ingest` — build index (offline).
- `python -m src.rag.ask [--stream] ["message"]` — chat.
- Env: **`SARVAM_API_KEY` required** (module raises at import if missing);
  `MONGODB_URI` optional (JSONL fallback); `HF_HOME` optional cache location.

---

## Subsystem 2 — Graph intelligence (`src/graph/`) — code-verified

### Stack
NetworkX (Louvain community detection) for the local pipeline; Neo4j Aura
(`neo4j` driver + Cypher) for the graph-DB pipeline; MongoDB as the incident
source; `matplotlib` for the PNG. Outputs to MongoDB **and** local export files.

### What it builds
Reads incidents from MongoDB and builds an **undirected co-occurrence graph**:
each incident is treated as a clique, so every pair of entities mentioned in
the same incident gets an edge (weight increments on reuse). The four node
types come straight from incident fields:

| Node | Source field |
| --- | --- |
| mule account | `mule_account` |
| phone number | `caller_number` |
| victim region (city) | `victim_region` |
| `scammer_id` — **actually the UPI handle** | `mule_upi` |

> There is **no victim node, no scammer-person node, and no transaction node**
> — `scammer_id` is the payment UPI, not a person. Reuse of an account/number
> across incidents shows up as high node degree.

On top of that:
- **Fraud rings** via Louvain community detection (NetworkX) + per-entity risk
  scoring (`high` ≥10 incidents, `medium` ≥3).
- **Cypher pattern queries** (Neo4j): high-degree/reused accounts, regional
  hotspots, accounts sharing a phone number, accounts spanning multiple regions.
- **Intelligence package**: confidence-scored rings (transparent heuristic —
  `0.7·min(1, incidents/10) + scam-type-consistency`, formula stored with the
  score), ring core members (`is_core_operator` ≥5 incidents), region→state
  jurisdiction mapping, INR-formatted financial totals, and a chronological
  **evidence chain** per ring.

> **Honest scope note:** the only graph *algorithm* actually implemented is
> **Louvain community detection**. Despite the "graph intelligence" framing
> there is no centrality / PageRank / betweenness / shortest-path. The
> "intelligence" is Louvain clustering + heuristic scoring + aggregation. Also,
> account-to-account "money chains" are a **proxy inferred from a shared phone
> number**, not real bank-transaction data (she labels this candidly).

### Pipelines & entry points
- **Local (no external DB):** `python -m src.graph.run` → writes
  `network_graph.graphml`, `fraud_rings.json`, `account_intelligence.json`,
  `summary_report.txt`; `python -m src.graph.visualize` → quick PNG.
- **Neo4j:** `python -m src.graph.neo4j_run` (clear + rebuild graph from Mongo
  + basic Cypher analysis); `python -m src.graph.neo4j_intelligence_run`
  (read-only full intelligence + evidence reports).
- Env: `NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD / NEO4J_DATABASE` (graph
  side only).

---

## How the two halves connect

**Via shared MongoDB, not a direct call.** `incident_store.save_session()`
writes to `digital_arrest_shield.incidents`; `src/graph/data.py` reads that
same collection. The chat never queries the graph live during a conversation.

> Note: `src/rag/graph_lookup.py::entity_lookup()` *looks* like an in-chat
> "is this number known-fraud?" lookup, but it's a **hardcoded placeholder**
> (`status: "not_connected"`) and is **called nowhere** — i.e. live graph
> enrichment of the chat is not implemented yet. This is a natural future hook.

---

## Functional vs. stubbed / needs external services

**Functional and runnable (given keys):** the full chat loop, retrieval, FAISS
search, embeddings, repetition guard, background extraction, incident schema,
Mongo+JSONL persistence, the CLI, and the prebuilt index.

**Requires config / services:**
- `SARVAM_API_KEY` — mandatory for any chat.
- ~470 MB embedding-model download on first run (network once).
- MongoDB optional (JSONL fallback); Neo4j only for the Neo4j graph pipeline.

**Stub / placeholder:** `graph_lookup.entity_lookup` (unused placeholder).

**Honest limitations she documents:** ring confidence scores are a heuristic
(not a legal determination); account linkage is inferred from shared phone
infrastructure, not real bank-transaction data; jurisdiction mapping is a small
static city table; victim identity is never collected (anonymous `session_id`);
Louvain runs in NetworkX (Aura free tier lacks the GDS plugin).

---

## What's left for us (integration notes)

- **Relocate** `rag-graph/` into the proper backend layout (it currently sits
  outside `backend/`). The RAG side already mirrors our stack (Sarvam, Mongo),
  so it can likely fold into `backend/` with shared config rather than its own
  `.env` / `requirements.txt`.
- **Expose the chat** through our FastAPI (`chat_turn` / `chat_turn_stream` are
  ready to wrap in an endpoint) instead of the CLI.
- **Reconcile dependencies/config** with our `uv` project and `shared/config.py`
  (she uses `pip`/`requirements.txt` + her own `.env` keys).
- **Optional:** wire `graph_lookup.entity_lookup` to the real graph so the chat
  can flag a known-fraud number/account mid-conversation.

---

## Discrepancies worth knowing (don't trip on these)

- `retriever.py`'s docstring says embeddings are **bge-m3** — stale; the real
  model is **MiniLM** (`embedder.py`). Behavior is fine; the comment is wrong.
- `ask.py` hardcodes a Windows `HF_HOME` default
  (`D:/digital-arrest-shield/.cache/huggingface`) via `setdefault` — override
  by setting `HF_HOME` (matters on our Linux setup).
- **`matplotlib` is missing from `requirements.txt`** but `visualize.py` needs
  it — the PNG step fails on a clean install until it's added.
- `neo4j_load.py` is **MERGE-based and double-counts on rerun without
  clearing**. `neo4j_run.py` clears first (safe); `neo4j_intelligence_run.py`
  is read-only (safe) — just don't call the loader twice by hand.
- No `.env` / `.env.example` is checked in (correct for secrets, but we'll need
  to supply `SARVAM_API_KEY`, `MONGODB_URI`, and the `NEO4J_*` vars ourselves).
