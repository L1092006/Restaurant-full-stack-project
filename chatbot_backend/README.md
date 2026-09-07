# Chatbot Backend — LangGraph AI Agent

A standalone WebSocket service that runs an AI sales assistant ("Vbot") for the
restaurant site. It is a stateful **LangGraph** agent with short-term, long-term
and cross-session memory, whose tools execute **inside the user's live browser**
rather than on the server.

> Part of the [Restaurant full-stack project](../README.md). The browser
> (`frontend/restaurant`) connects over a WebSocket; the agent shares the same
> MySQL database as the Django API (`backend/`).

## Tech stack

- **LangGraph** — the agent's stateful reasoning graph and SQLite checkpointing
- **LangChain** chat models — provider chosen by the `CLOUD` flag:
  **OpenRouter** when `CLOUD=True`, local **Ollama** otherwise
- **Pinecone** — vector store for long-term memory retrieval
- **websockets** (asyncio) — the transport (note: the `websocket` package is
  also pinned but unused; import `websockets`)
- **PyMySQL** — cross-session user profiles/messages in MySQL
- **SQLite** (`aiosqlite`) — LangGraph conversation checkpoints

## Getting started

```bash
cd chatbot_backend
pip install -r requirements.txt

# Create chatbot_backend/.env (see Configuration)

python server.py        # WebSocket on :8001, HTTP GET /health -> 200 (for the ALB)
```

Requirements: a reachable MySQL server, a Pinecone API key, and either an
OpenRouter API key (`CLOUD=True`) or a running Ollama model (`CLOUD=False`).

## Configuration

Read from `chatbot_backend/.env` at import time — several variables have no
default and will crash the process if unset.

| Variable | Purpose |
|---|---|
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | MySQL connection |
| `CLOUD` | `True` → OpenRouter; anything else → Ollama |
| `OPENROUTER_MODEL`, `OPENROUTER_API_KEY` | Cloud LLM (when `CLOUD=True`) |
| `PINECONE_API_KEY`, `INDEX_NAME` | Long-term memory vector index |
| `MODEL_CONTEXT` | Model context window (drives memory/summary budgeting) |
| `MEMORY_LENGTH` | Max words per stored memory chunk |
| `DEBUG` | `True` to print verbose graph logs |

Site identity (`web_name`, `web_description`) lives in **`config.json`** and is
read by `prompts.py` at import — edit it to rebrand the assistant.

## Architecture

### The agent acts inside the user's browser

The chatbot's tools do not perform actions server-side. Instead they use a
WebSocket tool-call protocol so each tool executes in the user's live app:

1. `chatbot.py` defines LangGraph tools that `send()` a
   `{type: "tool_call", content: {tool_name, arguments}}` message and `recv()`
   the result.
2. The frontend (`ChatbotContext.jsx`) executes it against the real app
   (React Router navigation, cart mutations, REST fetches) and replies with
   `{type: "tool_result", content: {status, result}}`.
3. `send_message` pushes a `chat_message` for display; `terminate` is a local
   no-op tool that ends the current graph invocation.

Browser-executed tools: `navigate`, `get_items`, `add_item`, `get_cartitems`,
`get_orders`. Add new browser tools by mirroring the existing `send()`/`recv()`
pattern.

### The graph (`chatbot.py`)

```
START → init_node → reasoning → summarize → {tools | think | shutdown}
                       ▲                         │        │
                       └─────────────────────────┘        └→ (tools/think loop back to reasoning)
shutdown → END
```

- **init_node** — assembles the full system prompt, fetches related memories
  from Pinecone, injects a status message, and clears the previous turn's tool
  results.
- **reasoning** — invokes the tool-bound chat model.
- **summarize** — once history passes 30 messages, compacts the older half into
  the running summary.
- **think** — nudges the model to call a tool when it produced text but no tool
  call.
- **shutdown** — reached when the model calls `terminate` alone; ends the run.

### Memory (three tiers)

- **Short-term** — LangGraph SQLite checkpoints (`assistant.db`), keyed by
  `thread_id = user id`.
- **Long-term** — Pinecone, with namespaces keyed by username and by
  `web_name`. The index (`llama-text-embed-v2`) is auto-created if missing.
- **Cross-session profiles** — MySQL `users` / `user_messages` tables, created
  by `server.py` on startup. On disconnect, the agent updates each logged-in
  user's profile and last-conversation summary.

## Wire protocol

Authoritative contract is the docstring at the top of `server.py`. Every message
is `{type, content}`.

- **Client → server** types: `status_update`, `chat_message`, `tool_result`.
  The **first** message on a connection **must** be `status_update`, or the
  socket is closed with code `1008`.
- **Server → client** types: `chat_message`, `tool_call`.

`status_update.content` carries `user_id`, `username`, a `web_state`
(`web_name`, `current_url`), and a `paths_schema` describing the frontend
routes the agent may navigate to.

## Health check

`GET /health` returns `200 ok` (used by the ALB target group). All other traffic
is handled as WebSocket connections on port `8001` (host and port are
hardcoded).

## Notes / legacy files

- **`test_client.py` is stale** — it sends `type: "message"`, but the server
  expects `chat_message`.
- `init.sql` / `update.sql` and the committed `*.db` files describe an old
  SQLite-based store; the live cross-session persistence is MySQL (tables are
  created in `server.py`). `assistant.db` is a live LangGraph checkpoint file.
- `chatbot.ipynb` is a scratch notebook used while developing the graph.
