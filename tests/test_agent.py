from datetime import date

import pytest
from openai import OpenAI

from agent import create_llm_client, load_reference_date


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