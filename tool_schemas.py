"""Tool definitions sent to the model, in the OpenAI function calling format.

The descriptions tell the model when to use each tool: data lookups (catalog, orders)
or policy lookups (store manual).
"""

from policies import POLICY_TOPICS
from tools import read_table

CATEGORY_NAMES = read_table("categories")["name"].tolist()

# Tool definitions in the OpenAI function calling format; the descriptions tell the model when to use each one
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Search the store catalog. Use it for any question about which instruments exist, "
                "their price or availability. Never state a price or availability without calling a tool."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Words of the product name, brand or model."},
                    "category": {"type": "string", "enum": CATEGORY_NAMES},
                    "max_price": {"type": "number", "description": "Maximum price in BRL."},
                    "only_available": {
                        "type": "boolean",
                        "description": "True (default) to list only products in stock.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_details",
            "description": (
                "Get the price, PIX price, installments and specs of one product. "
                "Use the product_id returned by search_products."
            ),
            "parameters": {
                "type": "object",
                "properties": {"product_id": {"type": "integer"}},
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": (
                "Get the status of a customer order, including return and warranty rights. "
                "Ask the customer for the order number and the e-mail or phone registered for it before calling."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer"},
                    "contact": {"type": "string", "description": "E-mail or phone registered for the order."},
                },
                "required": ["order_id", "contact"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_store_policy",
            "description": (
                "Get the store policy text for a topic: store info and address, opening hours, payment methods, "
                "returns and exchanges, shipping, promotions rules, warranty or privacy."
            ),
            "parameters": {
                "type": "object",
                "properties": {"topic": {"type": "string", "enum": list(POLICY_TOPICS)}},
                "required": ["topic"],
            },
        },
    },
]