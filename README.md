# Enterprise Customer Service Agent

A locally runnable customer-service agent that connects conversational workflows to product, order, policy, and support-ticket tools. The project focuses on application behaviour: tool selection, retrieval quality, multi-turn state, confirmation before sensitive actions, and predictable failure handling.

The bundled sample data is Chinese so the project can exercise retrieval and customer-support behaviour outside an English-only demo. The code and developer documentation are written in English.

## Features

- Product recommendations, stock checks, pricing, and order tracking.
- Hybrid retrieval over return, refund, warranty, and invoice policies, with source references.
- Multi-turn conversation state and customer-detail extraction.
- Explicit confirmation before order cancellation and other sensitive actions.
- Prompt-injection checks, tool retry handling, and deterministic local fallbacks.
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

The test suite covers retrieval, product and order tools, multi-turn state, confirmation, escalation, and the HTTP API. The offline evaluation reports intent accuracy, answer quality, tool success, and citation coverage.

## Example prompts

- `Recommend a laptop for office work.`
- `Where is order 9001?`
- `Can I return an item within seven days?`
- `I want to make a complaint and speak to support.`
- `Cancel order 9001`, followed by the required confirmation.

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
