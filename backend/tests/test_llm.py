"""Exercise the installed provider SDK over fake HTTP, with no network calls."""
import asyncio
import json
from types import SimpleNamespace

import httpx
import openai
import pytest
from fastapi.testclient import TestClient
from openai.resources.chat.completions import AsyncCompletions
from pydantic import ValidationError

from app.agents import graph, llm
from app.agents.llm import LLMClient, LLMConfigurationError, LLMError
from app.agents.rider_agent import RiderAdvocateAgent
from app.api import routes
from app.config import Settings
from app.db.store import InMemoryDisputeStore
from app.main import app
from app.schemas.dispute import AdvocateCase
from test_rider_agent import case_data, context_for, forbid_downstream


def real_client(**overrides):
    values = dict(
        _env_file=None, llm_provider="tokenhub", llm_api_key="test-key",
        llm_base_url="https://tokenhub-intl.tencentcloudmaas.com/v1", llm_model="hy3",
    )
    return LLMClient(Settings(**{**values, **overrides}))


def completion(content, *, refusal=None, finish_reason="stop"):
    return {
        "id": "test-completion", "object": "chat.completion", "created": 0,
        "model": "hy3",
        "choices": [{
            "index": 0, "finish_reason": finish_reason,
            "message": {"role": "assistant", "content": content, "refusal": refusal},
        }],
    }


@pytest.fixture
def provider_transport(monkeypatch):
    original = openai.AsyncOpenAI
    captured = []

    def install(handler):
        def factory(**kwargs):
            client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            captured.append((kwargs, client))
            return original(**kwargs, http_client=client)
        monkeypatch.setattr(openai, "AsyncOpenAI", factory)
        return captured

    return install


async def test_structured_provider_request_uses_existing_schema(provider_transport):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=completion(json.dumps(case_data())))

    captured = provider_transport(handler)
    context = context_for()
    result = await RiderAdvocateAgent(real_client()).run(context)
    assert result == AdvocateCase.model_validate(case_data())
    assert len(requests) == 1
    request = requests[0]
    assert str(request.url) == "https://tokenhub-intl.tencentcloudmaas.com/v1/chat/completions"
    body = json.loads(request.content)
    assert body["model"] == "hy3"
    assert body["stream"] is False
    assert request.headers["authorization"] == "Bearer test-key"
    assert [m["role"] for m in body["messages"]] == ["system", "user"]
    assert json.loads(body["messages"][1]["content"]) == context.model_dump(mode="json")
    schema = body["response_format"]
    assert schema["type"] == "json_schema"
    assert schema["json_schema"]["strict"] is True
    assert schema["json_schema"]["name"] == "AdvocateCase"
    assert schema["json_schema"]["schema"] == AdvocateCase.model_json_schema()
    assert captured[0][0]["max_retries"] == 0
    assert captured[0][0]["timeout"] == 60.0
    assert captured[0][1].is_closed


@pytest.mark.parametrize("failure", [
    "unauthorized", "server", "timeout", "malformed", "missing_field", "extra_field",
    "refusal", "empty", "null", "truncated", "filtered", "no_choices", "bad_reference",
])
async def test_provider_failures_reach_controlled_workflow(monkeypatch, provider_transport, failure):
    requests = []

    def handler(request):
        requests.append(request)
        if failure == "timeout":
            raise httpx.ReadTimeout("private diagnostic", request=request)
        if failure in ("unauthorized", "server"):
            return httpx.Response(
                401 if failure == "unauthorized" else 500,
                json={"error": {"message": "private provider diagnostic"}},
            )
        data = case_data()
        if failure == "missing_field":
            data.pop("claim")
        if failure == "extra_field":
            data["private_reasoning"] = "unexpected"
        if failure == "bad_reference":
            data["claim"] = "[evidence:invented]"
        content = json.dumps(data)
        if failure == "malformed":
            content = "{broken"
        elif failure == "empty":
            content = ""
        elif failure == "null":
            content = None
        body = completion(
            content, refusal="declined" if failure == "refusal" else None,
            finish_reason={"truncated": "length", "filtered": "content_filter"}.get(failure, "stop"),
        )
        if failure == "no_choices":
            body["choices"] = []
        return httpx.Response(200, json=body)

    captured = provider_transport(handler)
    monkeypatch.setattr(graph, "rider_advocate_agent", RiderAdvocateAgent(real_client()))
    forbid_downstream(monkeypatch)
    with pytest.raises(graph.AdvocateContractError) as caught:
        await graph.run_dispute_graph(context_for().dispute)
    assert caught.value.detail.stage == "rider_advocate"
    assert isinstance(caught.value.__cause__, (LLMError, ValidationError))
    assert len(requests) == 1
    assert captured[0][1].is_closed


@pytest.mark.parametrize("key", ["", "   "])
async def test_missing_credentials_fail_before_client_construction(monkeypatch, key):
    def forbidden(**kwargs):
        pytest.fail("Missing credentials must not construct a provider client")
    monkeypatch.setattr(openai, "AsyncOpenAI", forbidden)
    with pytest.raises(LLMConfigurationError, match="LLM_API_KEY"):
        await real_client(llm_api_key=key).complete("system", "user", response_model=AdvocateCase)


@pytest.mark.parametrize("settings", [
    {"llm_provider": "typo"},
    {"llm_model": ""},
    {"llm_model": "   "},
])
def test_invalid_provider_configuration_rejected(settings):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **settings)


MALFORMED_ENVELOPES = [
    pytest.param(b"<html>private upstream failure</html>", "text/html", id="non-json-200"),
    pytest.param(b"{broken", "application/json", id="invalid-json-200"),
    pytest.param(b"\xff", "application/json", id="invalid-encoding"),
    pytest.param(b"[" * 1100 + b"]" * 1100, "application/json", id="decoder-recursion"),
    pytest.param(b"null", "application/json", id="null-envelope"),
    pytest.param(b"[]", "application/json", id="array-envelope"),
    pytest.param(b"{}", "application/json", id="missing-choices"),
    pytest.param(b'{"choices":null}', "application/json", id="null-choices"),
    pytest.param(b'{"choices":{}}', "application/json", id="object-choices"),
    pytest.param(b'{"choices":[]}', "application/json", id="empty-choices"),
    pytest.param(b'{"choices":[null]}', "application/json", id="null-choice"),
    pytest.param(b'{"choices":[{"finish_reason":"stop"}]}', "application/json", id="missing-message"),
    pytest.param(b'{"choices":[{"finish_reason":"stop","message":null}]}', "application/json", id="null-message"),
    pytest.param(b'{"choices":[{"finish_reason":"stop","message":[]}]}', "application/json", id="array-message"),
    pytest.param(
        b'{"choices":[{"finish_reason":"stop","message":{"role":"assistant","content":42}}]}',
        "application/json", id="non-string-content",
    ),
]


@pytest.mark.parametrize("body,content_type", MALFORMED_ENVELOPES)
def test_malformed_provider_envelope_returns_controlled_502(
    monkeypatch, provider_transport, body, content_type,
):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, content=body, headers={"content-type": content_type})

    captured = provider_transport(handler)
    monkeypatch.setattr(graph, "rider_advocate_agent", RiderAdvocateAgent(real_client()))
    monkeypatch.setattr(routes, "store", InMemoryDisputeStore())
    forbid_downstream(monkeypatch)
    with TestClient(app) as client:
        response = client.post("/disputes", json={
            "scenario_id": "route_deviation_001", "category": "route_deviation",
        })
        assert response.status_code == 502
        assert response.json() == {"detail": {
            "code": "advocate_contract_failure",
            "stage": "rider_advocate",
            "message": (
                "Rider advocate returned an invalid case; "
                "workflow stopped before judge execution."
            ),
        }}
        assert client.get("/disputes").json() == []
    assert len(requests) == 1
    assert captured[0][1].is_closed


@pytest.mark.parametrize("stage", ["sdk", "decode"])
@pytest.mark.parametrize("error_type", [ValueError, TypeError, AttributeError, RuntimeError])
def test_non_openai_parsing_exceptions_return_controlled_502(
    monkeypatch, provider_transport, stage, error_type,
):
    def handler(request):
        return httpx.Response(200, json=completion(json.dumps(case_data())))

    captured = provider_transport(handler)

    def fail_decode(*args, **kwargs):
        raise error_type("private decoder diagnostic")

    async def fail_sdk(*args, **kwargs):
        raise error_type("private SDK diagnostic")

    if stage == "sdk":
        monkeypatch.setattr(AsyncCompletions, "create", fail_sdk)
    else:
        # Replace only this adapter's decoder reference, not global json.loads.
        monkeypatch.setattr(llm, "json", SimpleNamespace(loads=fail_decode))
    monkeypatch.setattr(graph, "rider_advocate_agent", RiderAdvocateAgent(real_client()))
    monkeypatch.setattr(routes, "store", InMemoryDisputeStore())
    forbid_downstream(monkeypatch)
    with TestClient(app) as client:
        response = client.post("/disputes", json={
            "scenario_id": "route_deviation_001", "category": "route_deviation",
        })
        assert response.status_code == 502
        assert response.json()["detail"]["code"] == "advocate_contract_failure"
        assert response.json()["detail"]["stage"] == "rider_advocate"
        assert "private" not in response.text
        assert client.get("/disputes").json() == []
    assert captured[0][1].is_closed


@pytest.mark.parametrize("content", [json.dumps(case_data()), None])
def test_provider_reasoning_is_never_returned_or_used_as_fallback(
    monkeypatch, provider_transport, content,
):
    def handler(request):
        body = completion(content)
        body["choices"][0]["message"]["reasoning_content"] = "private reasoning marker"
        return httpx.Response(200, json=body)

    provider_transport(handler)
    monkeypatch.setattr(graph, "rider_advocate_agent", RiderAdvocateAgent(real_client()))
    monkeypatch.setattr(routes, "store", InMemoryDisputeStore())
    if content is None:
        forbid_downstream(monkeypatch)
    with TestClient(app) as client:
        response = client.post("/disputes", json={
            "scenario_id": "route_deviation_001", "category": "route_deviation",
        })
        assert response.status_code == (502 if content is None else 200)
        assert "private reasoning marker" not in response.text
        if content is not None:
            assert response.json()["rider_case"] == case_data()


async def test_cancellation_is_not_normalized(monkeypatch, provider_transport):
    def handler(request):
        pytest.fail("Cancelled SDK call must not reach the transport")

    captured = provider_transport(handler)

    async def cancelled(*args, **kwargs):
        raise asyncio.CancelledError

    monkeypatch.setattr(AsyncCompletions, "create", cancelled)
    with pytest.raises(asyncio.CancelledError):
        await RiderAdvocateAgent(real_client()).run(context_for())
    assert captured[0][1].is_closed


@pytest.mark.parametrize("base_url", ["", "   "])
async def test_blank_endpoint_cannot_fall_back_to_openai(monkeypatch, base_url):
    def forbidden(**kwargs):
        pytest.fail("Missing TokenHub endpoint must fail before client construction")
    monkeypatch.setattr(openai, "AsyncOpenAI", forbidden)
    with pytest.raises(LLMConfigurationError, match="LLM_BASE_URL"):
        await real_client(llm_base_url=base_url).complete("system", "user", response_model=AdvocateCase)


def test_hackathon_defaults_select_hy3_without_enabling_live_calls(monkeypatch):
    for key in ("LLM_PROVIDER", "LLM_MODEL", "LLM_BASE_URL"):
        monkeypatch.delenv(key, raising=False)
    settings = Settings(_env_file=None)
    assert settings.llm_provider == "mock"
    assert settings.llm_model == "hy3"
    assert settings.llm_base_url == "https://tokenhub-intl.tencentcloudmaas.com/v1"
