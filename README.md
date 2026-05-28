# a2a-langgraph — thesis multi-agent system

A coordinator-pattern multi-agent system that turns a research topic into a
**reasoned, viability-checked research thesis**. Each agent is its own LangGraph
graph and its own Docker image. Agents talk over **A2A**; the researcher reaches
arXiv through an **MCP** server. All LLM inference runs against **Ollama on the
host** (`llama3.1:8b`).

```
 CLI ──A2A──▶ Coordinator ──A2A──▶ Researcher ──MCP──▶ arXiv MCP server ──▶ arXiv
                  │  ▲
                  ├──A2A──▶ Synthesizer        (Researcher / Critic / Synthesizer
                  └──A2A──▶ Critic              run inference against host Ollama)

 Coordinator flow:  research (once) ─▶ [ synthesize ─▶ critique ]*
 Loop repeats while the Critic rejects viability, up to MAX_REVISIONS.
```

## Prerequisites

- **Docker** + Docker Compose
- **Ollama** running on the host at `0.0.0.0:11434` with the model pulled:
  ```bash
  ollama pull llama3.1:8b
  ```
- **uv** (only needed to run the CLI / tests on the host): https://docs.astral.sh/uv/

## Quickstart

```bash
cp .env.example .env          # optional; sensible defaults are baked in
docker compose up --build     # starts mcp_arxiv + 4 agents

# in another terminal, ask for a thesis (CLI runs on the host):
uv run thesis-cli "efficient retrieval-augmented generation for code"
```

The CLI sends the topic to the coordinator's A2A endpoint (`http://localhost:9000`)
and prints the thesis, its viability verdict, and the arXiv sources used.

## Local run without Docker

Each service reads its config from the environment, so you can run them as plain
processes (point everything at `localhost` instead of compose service names):

```bash
OLLAMA_BASE_URL=http://localhost:11434 MCP_ARXIV_URL=http://localhost:8000/mcp \
PORT=8000 uv run python -m mcp_arxiv.server &
PORT=8081 PUBLIC_URL=http://localhost:8081 uv run python -m researcher &
PORT=8082 PUBLIC_URL=http://localhost:8082 uv run python -m critic &
PORT=8083 PUBLIC_URL=http://localhost:8083 uv run python -m synthesizer &
PORT=9000 PUBLIC_URL=http://localhost:9000 \
  RESEARCHER_URL=http://localhost:8081 CRITIC_URL=http://localhost:8082 \
  SYNTHESIZER_URL=http://localhost:8083 uv run python -m coordinator &

uv run thesis-cli "your topic here"
```

## Layout

```
packages/
  common/            shared schemas, config, LLM factory, A2A server/client helpers
  agent_coordinator/ orchestration graph + A2A server + A2A clients to peers
  agent_researcher/  graph + A2A server + MCP client (arXiv)
  agent_critic/      graph + A2A server
  agent_synthesizer/ graph + A2A server
  mcp_arxiv/         MCP server exposing an `arxiv_search` tool
  cli/               thin A2A client (runs on host)
```

## Sequence diagrams

These are layered: diagram **1** treats each agent call as a single logical hop;
diagram **2** expands what *one* hop actually does; diagram **3** zooms into one
agent's internals (MCP + Ollama). The rest cover the remaining shapes.

### 1. End-to-end orchestration (with the refine loop)

```mermaid
sequenceDiagram
    actor User
    participant CLI as thesis-cli
    participant CO as Coordinator
    participant R as Researcher
    participant S as Synthesizer
    participant C as Critic

    User->>CLI: topic
    CLI->>CO: A2A message/send {topic}
    Note over CO: LangGraph: research → [synthesize → critique]* → finalize

    CO->>R: A2A {topic}
    R-->>CO: ResearchFindings {sources, synthesis}

    loop until viable OR revisions >= MAX_REVISIONS
        CO->>S: A2A {topic, findings, critique?, revision}
        S-->>CO: ThesisDraft {statement, argument}
        CO->>C: A2A {topic, draft, findings}
        C-->>CO: Critique {viable, issues, suggestions}
        Note over CO: revisions += 1
        alt viable OR revisions >= MAX_REVISIONS
            Note over CO: exit loop, go to finalize
        else not viable and budget remains
            Note over CO: loop back, passing critique as feedback
        end
    end

    Note over CO: finalize builds ThesisResult
    CO-->>CLI: ThesisResult {statement, argument, viability, sources, revisions}
    CLI-->>User: rendered thesis
```

### 2. Anatomy of a single A2A hop

```mermaid
sequenceDiagram
    participant Caller as Caller (A2A client)
    participant Res as A2ACardResolver
    participant App as Target agent (Starlette)
    participant Ex as _JsonExecutor
    participant G as Agent LangGraph

    Caller->>Res: get_agent_card(base_url)
    Res->>App: GET /.well-known/agent-card.json
    App-->>Res: AgentCard {url, skills}
    Res-->>Caller: AgentCard

    Caller->>App: POST card.url, JSON-RPC message/send (JSON in TextPart)
    App->>Ex: execute(context, event_queue)
    Ex->>Ex: json.loads(context.get_user_input())
    Ex->>G: handler(payload) -> graph.ainvoke(state)
    G-->>Ex: result dict
    Ex->>App: enqueue new_agent_text_message(json.dumps(result))
    App-->>Caller: SendMessageSuccessResponse {result: Message}
    Caller->>Caller: _extract -> json.loads(text) -> dict
```

### 3. Researcher internals (LangGraph + MCP + Ollama)

```mermaid
sequenceDiagram
    participant CO as Coordinator
    participant RH as Researcher handler
    participant G as Researcher graph
    participant O as Ollama (host)
    participant M as MCP client
    participant AX as arXiv MCP server
    participant API as arXiv API

    CO->>RH: A2A {topic}
    RH->>G: graph.ainvoke({topic})

    Note over G: node plan
    G->>O: complete_text(QUERY_SYSTEM, topic)
    O-->>G: search query

    Note over G: node fetch
    G->>M: arxiv_search(query, max_results=5)
    M->>AX: MCP streamable-HTTP tools/call arxiv_search
    AX->>API: arxiv.Search(query)
    API-->>AX: papers
    AX-->>M: content blocks (text = paper JSON)
    M-->>G: _coerce -> [{title, summary, url}]

    Note over G: node summarize
    G->>O: complete_text(SUMMARY_SYSTEM, abstracts)
    O-->>G: synthesis

    G-->>RH: ResearchFindings
    RH-->>CO: ResearchFindings
```

### 4. Critic / Synthesizer internals (structured output)

```mermaid
sequenceDiagram
    participant CO as Coordinator
    participant H as Agent handler (Critic or Synthesizer)
    participant G as Single-node graph
    participant O as Ollama (host)

    CO->>H: A2A payload
    H->>G: graph.ainvoke(state)
    Note over G: synthesize -> ThesisDraft / critique -> Critique
    G->>O: complete_structured(Schema), JSON-schema constrained
    O-->>G: schema-validated object
    G-->>H: draft / critique dict
    H-->>CO: dict
```

### 5. Startup and dependency ordering

```mermaid
sequenceDiagram
    participant DC as docker compose
    participant MX as mcp_arxiv
    participant R as agent_researcher
    participant S as agent_synthesizer
    participant C as agent_critic
    participant CO as agent_coordinator

    DC->>MX: start
    MX-->>DC: serving :8000/mcp
    par researcher (depends_on mcp_arxiv)
        DC->>R: start, serve card :8080
    and synthesizer
        DC->>S: start, serve card :8080
    and critic
        DC->>C: start, serve card :8080
    end
    DC->>CO: start (depends_on the three specialists)
    CO-->>DC: serving :8080, published to host :9000
    Note over DC,CO: depends_on waits for container start, not readiness;<br/>A2A cards are resolved lazily on first request
```

### 6. Failure path (arXiv MCP unavailable)

```mermaid
sequenceDiagram
    participant G as Researcher graph (fetch)
    participant M as MCP client
    participant AX as arXiv MCP server
    participant O as Ollama

    G->>M: arxiv_search(query)
    alt MCP reachable
        M->>AX: tools/call
        AX-->>M: papers
        M-->>G: sources
    else MCP error or tool missing
        M-->>G: [] (_coerce yields empty list)
        Note over G: summarize falls back to a "no papers retrieved" prompt
    end
    G->>O: complete_text(summary)
    O-->>G: synthesis (sourceless)
```

> Coordinator-level failures (a peer timing out past `call_agent`'s 300s budget)
> propagate up as an error in the MVP — graceful degradation there is a hardening task.

## Configuration

| Variable | Default | Used by |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | all agents |
| `LLAMA_MODEL` | `llama3.1:8b` | all agents |
| `MAX_REVISIONS` | `2` | coordinator |
| `MCP_ARXIV_URL` | `http://mcp_arxiv:8000/mcp` | researcher |
| `RESEARCHER_URL` / `CRITIC_URL` / `SYNTHESIZER_URL` | compose service URLs | coordinator |
| `PUBLIC_URL` / `PORT` | per service | each agent |

## Tests

```bash
uv run pytest          # deterministic unit tests (no network, no LLM)
```

## Notes

- **Python is pinned to 3.12** across the workspace and images for LangChain /
  LangGraph / a2a-sdk compatibility, even though the host may run a newer version.
- **`a2a-sdk` is pinned to `0.3.26`** (classic Starlette + Pydantic API). The
  `1.0.x` line is a protobuf/gRPC redesign with a different surface.
- This is an **MVP**: timeouts are basic, there's no auth/observability, and task
  state is in-memory. Those are the hardening phase.
```
