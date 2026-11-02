"""Customer service agent "Clave": settings, tool dispatch and the conversation loop."""

import json
import os
from datetime import date, datetime

from dotenv import load_dotenv
from openai import OpenAI

from policies import get_store_policy, load_policies
from prompts import STORE_PHONE, build_system_prompt
from tool_schemas import TOOL_SCHEMAS
from tools import get_order_status, get_product_details, load_orders, load_products, search_products

load_dotenv()  # reads the .env file once, when the module is imported

DEFAULT_REFERENCE_DATE = "2026-03-25"  # Assumption: end of the data snapshot
MAX_TOOL_ROUNDS = 5  # stops a model that keeps calling tools without ever answering
FALLBACK_REPLY = (
    "Desculpe, não consegui concluir sua solicitação agora. "
    f"Nossa equipe pode ajudar pelo WhatsApp {STORE_PHONE}."
)


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

   
def load_store() -> dict:
    """Load once everything the tools need: catalog, orders, policies and the reference date."""
    return {
        "products": load_products(),
        "orders": load_orders(),
        "policies": load_policies(),
        "reference_date": load_reference_date(),
    }


def run_tool(name: str, arguments: str, store: dict) -> str:
    """Run the tool requested by the model and return its result as JSON text."""
    try:
        args = json.loads(arguments or "{}")
        if name == "search_products":
            result = search_products(store["products"], **args)
        elif name == "get_product_details":
            result = get_product_details(store["products"], **args)
        elif name == "get_order_status":
            result = get_order_status(store["orders"], reference_date=store["reference_date"], **args)
        elif name == "get_store_policy":
            result = get_store_policy(store["policies"], **args)
        else:
            result = {"error": f"Unknown tool: {name}"}
    except (json.JSONDecodeError, TypeError):
        # Malformed JSON or unexpected argument names: tell the model instead of crashing
        result = {"error": f"Invalid arguments for tool {name}: {arguments}"}
    return json.dumps(result, ensure_ascii=False)


def answer(client: OpenAI, model: str, history: list[dict], store: dict, now: datetime) -> str:
    """Send the conversation to the model, run the tools it asks for and return its final reply.

    The history list is updated in place with the tool calls, the tool results and the reply.
    """
    for _ in range(MAX_TOOL_ROUNDS):
        # The system prompt is rebuilt every round so "open/closed now" is always current
        messages = [{"role": "system", "content": build_system_prompt(now)}, *history]
        response = client.chat.completions.create(model=model, messages=messages, tools=TOOL_SCHEMAS)
        message = response.choices[0].message
        if not message.tool_calls:
            reply = message.content or ""
            history.append({"role": "assistant", "content": reply})
            return reply
        # model_dump keeps every field the provider sent with the tool calls, so nothing is lost
        history.append(message.model_dump(exclude_none=True))
        for tool_call in message.tool_calls:
            result = run_tool(tool_call.function.name, tool_call.function.arguments, store)
            history.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
    return FALLBACK_REPLY