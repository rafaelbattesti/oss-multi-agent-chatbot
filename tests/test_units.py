"""Deterministic unit tests for pure logic (no network, no LLM)."""

import logging

import pytest
from a2a.helpers.proto_helpers import new_data_message, new_text_message
from a2a.types import Artifact, Role, Task, TaskState
from google.protobuf.json_format import MessageToDict

from coordinator.graph import _route
from mcp_arxiv import server as mcp_arxiv_server
from librarian.mcp_tools import _coerce
import thesis_config as config
from a2a_core import client as a2a_client
from a2a_core import (
    JSON_MEDIA_TYPE,
    PayloadContractError,
    message_from_model,
    model_from_message,
    model_from_task,
    part_from_model,
)
from a2a_core.server import (
    CONTRACT_EXTENSION_URI,
    A2AAgentExecutor,
    build_card,
)
from observability import parse_log_level
from thesis_contracts import (
    CONTRACT_VERSION,
    Critique,
    CritiqueRequest,
    CritiqueResponse,
    ResearchFindings,
    ResearchRequest,
    ResearchResponse,
    Source,
    SynthesisRequest,
    ThesisDraft,
    ThesisResult,
)


def test_coerce_unwraps_mcp_text_blocks():
    blocks = [
        {"type": "text", "text": '{"title": "T", "summary": "S", "url": "U"}', "id": "1"}
    ]
    assert _coerce(blocks) == [{"title": "T", "summary": "S", "url": "U"}]


def test_coerce_passes_through_plain_dicts():
    data = [{"title": "T", "summary": "S", "url": "U"}]
    assert _coerce(data) == data


def test_coerce_handles_garbage():
    assert _coerce("not json") == []
    assert _coerce(None) == []


def test_arxiv_search_returns_empty_when_rate_limited(monkeypatch):
    class RateLimitedClient:
        def results(self, search):
            raise mcp_arxiv_server.arxiv.HTTPError("https://arxiv.example", 5, 429)

    monkeypatch.setattr(mcp_arxiv_server, "_client", RateLimitedClient())

    assert mcp_arxiv_server.arxiv_search("retrieval augmented generation") == []


def test_arxiv_search_raises_unexpected_http_errors(monkeypatch):
    class BadRequestClient:
        def results(self, search):
            raise mcp_arxiv_server.arxiv.HTTPError("https://arxiv.example", 5, 400)

    monkeypatch.setattr(mcp_arxiv_server, "_client", BadRequestClient())

    with pytest.raises(mcp_arxiv_server.arxiv.HTTPError):
        mcp_arxiv_server.arxiv_search("bad query")


def test_parse_log_level_accepts_names_and_numeric_values():
    assert parse_log_level("INFO") == 20
    assert parse_log_level("debug") == 10
    assert parse_log_level("30") == 30


def test_parse_log_level_rejects_invalid_values():
    assert parse_log_level("chatty") is None


@pytest.mark.asyncio
async def test_call_agent_logs_transport_failures(monkeypatch, caplog):
    async def fail_create_client(base_url, client_config):
        raise RuntimeError("card resolution failed")

    monkeypatch.setattr(a2a_client, "create_client", fail_create_client)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(RuntimeError, match="card resolution failed"):
            await a2a_client.call_agent(
                "http://agent_researcher:8080",
                ResearchRequest(topic="efficient RAG"),
                ResearchResponse,
            )

    assert "failed while sending ResearchRequest" in caplog.text


@pytest.mark.asyncio
async def test_executor_runs_task_lifecycle():
    async def invoke(request: ResearchRequest) -> ResearchResponse:
        return ResearchResponse(
            findings=ResearchFindings(topic=request.topic, synthesis="s")
        )

    class _RecordingQueue:
        def __init__(self) -> None:
            self.events = []

        async def enqueue_event(self, event):
            self.events.append(event)

    class _Context:
        message = message_from_model(
            ResearchRequest(topic="efficient RAG"), role=Role.ROLE_USER
        )
        current_task = None

    executor = A2AAgentExecutor(invoke, request_model=ResearchRequest)
    queue = _RecordingQueue()

    await executor.execute(_Context(), queue)

    states = [
        event.status.state
        for event in queue.events
        if getattr(event, "status", None) is not None
    ]
    assert TaskState.TASK_STATE_WORKING in states
    assert TaskState.TASK_STATE_COMPLETED in states

    artifact_events = [
        event for event in queue.events if getattr(event, "artifact", None) is not None
    ]
    assert len(artifact_events) == 1
    parsed = model_from_task(
        Task(artifacts=[artifact_events[0].artifact]), ResearchResponse
    )
    assert parsed.findings.topic == "efficient RAG"


def test_a2a_artifact_roundtrips_typed_payload():
    response = ResearchResponse(findings=ResearchFindings(topic="t", synthesis="s"))
    task = Task(
        artifacts=[
            Artifact(parts=[part_from_model(response)], name="research_findings")
        ]
    )

    assert model_from_task(task, ResearchResponse) == response


def test_route_finalizes_when_viable():
    state = {"critique": {"viable": True, "issues": [], "suggestions": []}, "revisions": 0}
    assert _route(state) == "finalize"


def test_route_revises_under_budget(monkeypatch):
    monkeypatch.setattr(config, "MAX_REVISIONS", 2)
    state = {"critique": {"viable": False, "issues": ["x"], "suggestions": []}, "revisions": 1}
    assert _route(state) == "synthesize"


def test_route_finalizes_at_budget(monkeypatch):
    monkeypatch.setattr(config, "MAX_REVISIONS", 2)
    state = {"critique": {"viable": False, "issues": ["x"], "suggestions": []}, "revisions": 2}
    assert _route(state) == "finalize"


def test_thesis_result_roundtrips():
    result = ThesisResult(
        topic="t",
        statement="s",
        argument="a",
        viability=Critique(viable=True),
        sources=[Source(title="T", summary="S", url="U")],
        revisions=1,
    )
    assert ThesisResult(**result.model_dump()) == result


def test_a2a_data_part_roundtrips_typed_payload():
    payload = ResearchRequest(topic="efficient RAG for code")
    message = message_from_model(payload, role=Role.ROLE_USER)

    assert model_from_message(message, ResearchRequest) == payload


def test_a2a_text_part_payload_is_rejected():
    message = new_text_message('{"topic": "efficient RAG"}', role=Role.ROLE_USER)

    with pytest.raises(PayloadContractError, match="data part"):
        model_from_message(message, ResearchRequest)


def test_malformed_synthesis_payload_fails_before_graph_execution():
    message = new_data_message({"topic": "efficient RAG"}, role=Role.ROLE_USER)

    with pytest.raises(PayloadContractError, match="Invalid SynthesisRequest"):
        model_from_message(message, SynthesisRequest)


def test_synthesis_and_critique_requests_do_not_require_top_level_topic():
    findings = ResearchFindings(topic="efficient RAG", synthesis="Evidence summary")
    draft = ThesisDraft(statement="S", argument="A")

    synthesis = SynthesisRequest(findings=findings)
    critique = CritiqueRequest(draft=draft, findings=findings)

    assert synthesis.findings.topic == "efficient RAG"
    assert critique.findings.topic == "efficient RAG"


def test_synthesis_request_rejects_extra_top_level_topic():
    findings = {
        "topic": "efficient RAG",
        "synthesis": "Evidence summary",
        "sources": [],
    }

    with pytest.raises(ValueError, match="Extra inputs are not permitted"):
        SynthesisRequest.model_validate(
            {"topic": "discarded topic", "findings": findings}
        )


def test_agent_card_advertises_payload_contracts():
    card = build_card(
        name="Researcher",
        description="Gathers evidence.",
        skill_id="gather_evidence",
        public_url="http://agent_researcher:8080",
        input_model=ResearchRequest,
        output_model=ResearchResponse,
        semantic_tags=("research", "evidence", "arxiv", "mcp"),
    )

    skill = card.skills[0]
    extension = card.capabilities.extensions[0]
    params = MessageToDict(extension.params)

    assert card.default_input_modes == [JSON_MEDIA_TYPE]
    assert card.default_output_modes == [JSON_MEDIA_TYPE]
    assert skill.input_modes == [JSON_MEDIA_TYPE]
    assert skill.output_modes == [JSON_MEDIA_TYPE]
    assert f"contract:{CONTRACT_VERSION}" in skill.tags
    assert "input:ResearchRequest" in skill.tags
    assert "output:ResearchResponse" in skill.tags
    assert extension.uri == CONTRACT_EXTENSION_URI
    assert params["contract_version"] == CONTRACT_VERSION
    assert params["input"]["name"] == "ResearchRequest"
    assert params["input"]["media_type"] == JSON_MEDIA_TYPE
    assert params["input"]["json_schema"]["title"] == "ResearchRequest"
    assert params["input"]["json_schema"]["properties"]["topic"]["type"] == "string"
    assert params["output"]["name"] == "ResearchResponse"
    assert params["output"]["media_type"] == JSON_MEDIA_TYPE
    assert params["output"]["json_schema"]["title"] == "ResearchResponse"


def test_common_card_builder_does_not_homogenize_semantic_tags():
    card = build_card(
        name="Critic",
        description="Judges thesis viability.",
        skill_id="critique_thesis",
        public_url="http://agent_critic:8080",
        input_model=CritiqueRequest,
        output_model=CritiqueResponse,
        semantic_tags=("critique", "viability-review"),
    )

    tags = set(card.skills[0].tags)

    assert {"critique", "viability-review"}.issubset(tags)
    assert "contract:1.0.0" in tags
    assert "research" not in tags
    assert "thesis" not in tags
