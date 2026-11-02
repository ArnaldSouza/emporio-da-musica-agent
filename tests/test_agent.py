import json
from datetime import date, datetime
from types import SimpleNamespace

import pytest
from openai import OpenAI
from openai.types.chat import ChatCompletion

from agent import FALLBACK_REPLY, MAX_TOOL_ROUNDS, answer, create_llm_client, load_reference_date, load_store, run_tool
from business_rules import CAMPO_GRANDE_TZ
from policies import POLICY_TOPICS
from tool_schemas import TOOL_SCHEMAS


def test_create_llm_client_reads_settings(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    client, model = create_llm_client()
    assert isinstance(client, OpenAI)
    assert model == "test-model"


def test_create_llm_client_without_key_raises_clear_error(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "")
    with pytest.raises(RuntimeError):
        create_llm_client()


def test_reference_date_defaults_to_end_of_data_snapshot(monkeypatch):
    monkeypatch.delenv("REFERENCE_DATE", raising=False)
    assert load_reference_date() == date(2026, 3, 25)


def test_reference_date_with_invalid_format_raises_clear_error(monkeypatch):
    monkeypatch.setenv("REFERENCE_DATE", "25/03/2026")
    with pytest.raises(RuntimeError):
        load_reference_date()
        
        
STORE = load_store()


def schema_of(tool_name):
    """Return the function schema of a tool by name (test helper)."""
    return next(tool["function"] for tool in TOOL_SCHEMAS if tool["function"]["name"] == tool_name)


def test_tool_schemas_offer_the_four_tools():
    names = [tool["function"]["name"] for tool in TOOL_SCHEMAS]
    assert names == ["search_products", "get_product_details", "get_order_status", "get_store_policy"]


def test_tool_schemas_list_categories_and_policy_topics():
    assert "Violões" in schema_of("search_products")["parameters"]["properties"]["category"]["enum"]
    assert schema_of("get_store_policy")["parameters"]["properties"]["topic"]["enum"] == list(POLICY_TOPICS)


def test_run_tool_search_products():
    result = json.loads(run_tool("search_products", '{"category": "Violões", "max_price": 1000}', STORE))
    assert result["total_found"] > 0


def test_run_tool_order_status_uses_reference_date():
    arguments = '{"order_id": 5, "contact": "rafael.pereira@jmail.com"}'
    result = json.loads(run_tool("get_order_status", arguments, STORE))
    assert result["status"] == "entregue"
    assert "defect_coverage" in result


def test_run_tool_store_policy():
    result = json.loads(run_tool("get_store_policy", '{"topic": "opening_hours"}', STORE))
    assert "09:00 às 18:00" in result["text"]


def test_run_tool_unknown_tool_returns_error():
    assert "error" in json.loads(run_tool("delete_orders", "{}", STORE))


def test_run_tool_invalid_arguments_return_error():
    assert "error" in json.loads(run_tool("search_products", "not json", STORE))
    assert "error" in json.loads(run_tool("get_product_details", '{"id": 95}', STORE))
    
    
NOW = datetime(2026, 3, 25, 10, 0, tzinfo=CAMPO_GRANDE_TZ)


def make_completion(content=None, tool_calls=None):
    """Build a fake model response in the real OpenAI format (test helper)."""
    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    return ChatCompletion.model_validate({
        "id": "test",
        "object": "chat.completion",
        "created": 0,
        "model": "test-model",
        "choices": [{"index": 0, "finish_reason": "stop", "message": message}],
    })


def make_tool_call(name, arguments):
    """Build a fake tool call requested by the model (test helper)."""
    return {"id": "call_1", "type": "function", "function": {"name": name, "arguments": arguments}}


def make_fake_client(responses, sent_requests):
    """Return a fake client that answers with the given responses and records each request."""
    def create(**request):
        sent_requests.append(request)
        return responses.pop(0)
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def test_answer_returns_direct_reply_and_updates_history():
    sent = []
    client = make_fake_client([make_completion("Olá! Como posso ajudar?")], sent)
    history = [{"role": "user", "content": "Oi"}]
    assert answer(client, "test-model", history, STORE, NOW) == "Olá! Como posso ajudar?"
    assert history[-1] == {"role": "assistant", "content": "Olá! Como posso ajudar?"}
    assert sent[0]["messages"][0]["role"] == "system"
    assert sent[0]["tools"] == TOOL_SCHEMAS


def test_answer_runs_requested_tool_and_sends_result_back():
    sent = []
    tool_call = make_tool_call("get_store_policy", '{"topic": "opening_hours"}')
    responses = [make_completion(tool_calls=[tool_call]), make_completion("Abrimos às 9h.")]
    history = [{"role": "user", "content": "Que horas vocês abrem?"}]
    reply = answer(make_fake_client(responses, sent), "test-model", history, STORE, NOW)
    assert reply == "Abrimos às 9h."
    tool_message = next(message for message in history if message["role"] == "tool")
    assert "09:00 às 18:00" in tool_message["content"]
    assert len(sent) == 2  # one request to choose the tool, one to write the reply


def test_answer_gives_fallback_when_model_never_stops_calling_tools():
    tool_call = make_tool_call("get_store_policy", '{"topic": "opening_hours"}')
    responses = [make_completion(tool_calls=[tool_call]) for _ in range(MAX_TOOL_ROUNDS)]
    history = [{"role": "user", "content": "Oi"}]
    assert answer(make_fake_client(responses, []), "test-model", history, STORE, NOW) == FALLBACK_REPLY