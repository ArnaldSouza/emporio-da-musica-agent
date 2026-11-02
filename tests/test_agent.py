import json
from datetime import date

import pytest
from openai import OpenAI

from agent import create_llm_client, load_reference_date, load_store, run_tool
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