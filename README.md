# Enterprise Customer Service Agent

A locally runnable customer-service agent that connects conversational workflows to product, order, policy, and support-ticket tools. The project focuses on application behaviour: tool selection, retrieval quality, multi-turn state, confirmation before sensitive actions, and predictable failure handling.

The bundled sample data and current intent rules are primarily Chinese, so the example prompts below use the language exercised by the tests. This README is in English; some user-facing strings and code comments remain Chinese.

## Features

- Product recommendations, stock checks, pricing, and order tracking.
- Hybrid retrieval over return, refund, warranty, and invoice policies, with source references.
- Multi-turn conversation state and customer-detail extraction.
- Explicit confirmation before creating a human-review ticket for order cancellation and other sensitive requests; the agent does not change orders itself.
- Keyword-based checks for selected prompt-injection phrases, one retry for failed tools, and a local draft fallback when optional OpenAI wording fails.
- SQLite-backed escalation tickets for complaints and requests that need a person.
- FastAPI, a small browser client, a command-line mode, and an MCP tool server.

## Request flow

```text
message
  -> intent and entity extraction
  -> product / order / policy / support tools
  -> confirmation and failure handling
  -> response with tool history and sources
```

## Run locally

Python 3.11 or newer is required.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt

# Web mode
python main.py --web
# Open http://127.0.0.1:8000

# Command-line mode
python main.py
```

The default `LLM_PROVIDER=local` mode does not require an API key. To use an OpenAI model for response wording, copy the example environment file and set `LLM_PROVIDER=openai` and `OPENAI_API_KEY`.

```bash
cp .env.example .env
python main.py --web
```

## MCP server

```bash
python -m src.mcp_server
```

The server exposes `search_products`, `lookup_orders`, and `escalate_to_human`.

## Tests and evaluation

```bash
python -m pytest -q
python -m evals.run_eval
```

The test suite covers retrieval, product and order tools, multi-turn state, confirmation, escalation, and the HTTP API. The six-case offline evaluation reports exact intent matches, required answer-text matches, expected tool use, and citation presence. Citation presence is not a check that the cited source supports every statement.

## Evidence behind project claims

The [LangGraph workflow](src/agent_graph.py) contains intent routing,
confirmation and tool-failure handling. [Business tools](src/business_tools.py)
read sample catalogue/order data and create [SQLite tickets](src/tickets.py).
The [retriever](src/rag_engine.py) combines BM25 and character-bigram cosine
similarity; policy answers attach document titles and IDs. The [MCP server](src/mcp_server.py)
reuses those business functions. [Agent tests](tests/test_agent.py) exercise the
main paths, while the [offline evaluator](evals/run_eval.py) specifies its
scoring rules. Describe these as local, fixture-backed behaviours rather than
production support outcomes or general prompt-injection protection.

## Example prompts

Use the Chinese customer questions in [`evals/dataset.json`](evals/dataset.json)
or [`tests/test_agent.py`](tests/test_agent.py). They exercise the implemented
intent rules; translated English prompts are not equivalent test fixtures.

## Repository layout

```text
data/                  Sample catalogue, order, and policy data
src/agent_graph.py     LangGraph workflow
src/rag_engine.py      BM25 and character-similarity retrieval
src/langchain_tools.py LangChain tool adapters
src/mcp_server.py      MCP server
src/api.py             FastAPI interface
web/index.html         Browser demo
tests/                 Automated tests
evals/                 Application-level evaluation set
```
