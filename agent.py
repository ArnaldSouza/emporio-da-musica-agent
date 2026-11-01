"""Customer service agent "Clave": settings, tools and the conversation loop."""

import os
from datetime import date

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # reads the .env file once, when the module is imported

DEFAULT_REFERENCE_DATE = "2026-03-25"  # Assumption: end of the data snapshot


def create_llm_client() -> tuple[OpenAI, str]:
    """Create the LLM client from the .env settings and return it with the model name."""
    api_key = os.getenv("LLM_API_KEY", "").strip()
    base_url = os.getenv("LLM_BASE_URL", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()
    if not (api_key and base_url and model):
        raise RuntimeError("Set LLM_API_KEY, LLM_BASE_URL and LLM_MODEL in the .env file (see .env.example).")
    return OpenAI(api_key=api_key, base_url=base_url), model


def load_reference_date() -> date:
    """Return the date treated as "today" by the date-based rules (REFERENCE_DATE in .env)."""
    value = os.getenv("REFERENCE_DATE", DEFAULT_REFERENCE_DATE).strip()
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise RuntimeError(f"REFERENCE_DATE must use the YYYY-MM-DD format, got: {value!r}") from None