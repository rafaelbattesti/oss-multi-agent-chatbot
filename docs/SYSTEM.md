# SYSTEM.md


## Edge / Identity

- **UI** — Next.js + assistant-ui (A2A client runtime) + official A2UI React renderer; standalone app container.
- **Dex** — OIDC identity provider; federates upstream IdP; issues tokens the guard validates.
- **Backend Server** — A2A Server; authn/z, tenancy, rate limits; enqueue jobs for orchestrator workers, relay event streams as SSE; zero agent logic.

## Agentic Core

- **Orchestrator workers** — supervisor agent; queue consumers; horizontally replicated; state in Postgres.
- **RAG workflow service** — agentic retrieval DAG (query transform, retrieve, grade, conditional re-retrieve); router + hard step budgets.
- **Data analysis agent** — code-gen loop.
- **Sandbox executor** — isolated code execution for the analysis agent.
- **ServiceNow agent** — slot-filling loop + risk-tiered HITL approval; ServiceNow holds long-lived ticket state.

## Agent Connectivity

- **agentgateway (solo.io)** — gates ALL agentic-layer connections; defines networking policy (Cedar); agent-to-LLM, agent-to-tool, agent-to-agent traffic; LLM routing, budgets, failover; unified audit.
- **agentregistry (solo.io)** — catalog of MCP servers, agents, skills; registration/approval workflows.
- **MCP tool servers** — one container per tool surface (ServiceNow MCP, data-source MCPs, RAG-ingest MCP); reachable only via agentgateway.

## Messaging & State

- **Redis (app)** — dispatch queue + run-event streams (A2A event relay, resumability). Dedicated instance.
- **Redis (Langfuse)** — Langfuse queue/cache; noeviction policy. Dedicated instance.
- **Postgres** — conversation state, run records, checkpoints, audit. *(Open: shared with Langfuse vs separate.)*
- **Qdrant** — vector DB for RAG embeddings/retrieval.

## Observability

- **langfuse-web** — UI + ingest APIs.
- **langfuse-worker** — async trace processing.
- **ClickHouse** — Langfuse OLAP store (traces, observations, scores); UTC required.
- **MinIO** — S3-compatible blob storage for Langfuse events.
- **OTel Collector** — traces/metrics fan-out from every service.
- **Prometheus** — metrics.
- **Grafana** — dashboards.

## System decisions

- The UI runs as a Next.js standalone app container built from `apps/chat-ui`.
