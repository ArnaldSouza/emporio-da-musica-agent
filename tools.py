"""Data access tools used by the agent: product catalog and orders."""

import json
from datetime import date
import unicodedata
from pathlib import Path

import pandas as pd

from business_rules import (
    METRO_CITY,
    apply_discount,
    can_combine_payments,
    defect_coverage,
    installment_value,
    is_within_return_window,
    max_installments,
    pix_price,
    shipping_fee,
)

DATA_DIR = Path(__file__).resolve().parent / "data"
CSV_PREFIX = "desafio_tecnico_ai_eng - "  # original file names are kept unchanged
ACTIVE_STATUS = "active"
COMING_SOON_STATUS = "coming_soon"
DISCONTINUED_STATUS = "discontinued"
ACTIVE_PROMOTION_FLAG = 1
# Availability labels in Portuguese, since the agent talks to Brazilian customers
AVAILABLE = "disponível"
OUT_OF_STOCK = "esgotado"
COMING_SOON = "em breve"
DISCONTINUED = "fora do catálogo"
MAX_SEARCH_RESULTS = 10  # keeps the tool answer short for the model
DELIVERED_STATUS = "delivered"
ORDER_STATUS_LABELS = {
    "pending": "pendente",
    "confirmed": "confirmado",
    "shipped": "enviado",
    "delivered": "entregue",
    "cancelled": "cancelado",
}
PAYMENT_LABELS = {"pix": "PIX", "debit": "cartão de débito", "boleto": "boleto bancário"}
CREDIT_PREFIX = "credit_"  # e.g. "credit_6x" means credit card in 6 installments
ORDER_NOT_FOUND = "Order not found or the contact does not match the one registered for it."


def read_table(name: str) -> pd.DataFrame:
    """Read one of the provided CSV files by table name, e.g. "products"."""
    path = DATA_DIR / f"{CSV_PREFIX}{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}. Keep the original file names in data/.")
    return pd.read_csv(path)


def normalize_text(text: str) -> str:
    """Lowercase text and remove accents, so "Violão" and "violao" match."""
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return without_accents.casefold().strip()


def product_availability(status: str, stock_quantity: int) -> str:
    """Return the availability label for a product. Status prevails over stock (manual 7.3)."""
    if status == COMING_SOON_STATUS:
        return COMING_SOON
    if status == DISCONTINUED_STATUS:
        return DISCONTINUED
    if status == ACTIVE_STATUS:
        return AVAILABLE if stock_quantity > 0 else OUT_OF_STOCK
    raise ValueError(f"Unknown product status: {status}")


def load_products() -> pd.DataFrame:
    """Load the product catalog ready for the agent tools.

    Adds the category name, the active promotion, the availability label and a normalized
    search text. Descriptions are dropped because some contradict the product name.
    """
    products = read_table("products").drop(columns=["description"])
    categories = read_table("categories")[["category_id", "name"]].rename(columns={"name": "category"})
    promotions = read_table("promotions").rename(columns={"description": "promotion_name"})

    active = promotions[promotions["is_active"] == ACTIVE_PROMOTION_FLAG]
    # If a product ever has two active promotions, keep only the highest discount
    best_active = active.sort_values("discount_percent", ascending=False).drop_duplicates("product_id")

    products = products.merge(categories, on="category_id", how="left")
    products = products.merge(best_active[["product_id", "discount_percent", "promotion_name"]], on="product_id", how="left")
    products["discount_percent"] = products["discount_percent"].fillna(0)
    products["promotion_name"] = products["promotion_name"].fillna("")
    products["availability"] = [
        product_availability(status, stock)
        for status, stock in zip(products["status"], products["stock_quantity"])
    ]
    products["specs"] = products["specs"].map(json.loads)
    products["search_text"] = (products["name"] + " " + products["category"]).map(normalize_text)
    return products


def _product_summary(product: pd.Series) -> dict:
    """Return the main fields of a product, with the promotional price when there is one."""
    summary = {
        "product_id": int(product["product_id"]),
        "name": product["name"],
        "category": product["category"],
        "availability": product["availability"],
        "price_brl": float(product["price_brl"]),
    }
    discount = float(product["discount_percent"])
    if discount > 0:
        # Manual 6.2: promotional prices are shown with the original price and the discount
        summary["original_price_brl"] = summary["price_brl"]
        summary["price_brl"] = apply_discount(summary["original_price_brl"], discount)
        summary["discount_percent"] = int(discount)
        summary["promotion_name"] = product["promotion_name"]
    return summary


def search_products(
    products: pd.DataFrame,
    query: str = "",
    category: str = "",
    max_price: float | None = None,
    only_available: bool | None = None,
    only_promotions: bool = False,
) -> dict:
    """Search the catalog by words in the name, category, maximum price and promotion, cheapest first.

    By default a search by name also returns unavailable products, so the agent can say a product is
    out of stock, coming soon or discontinued (manual 7.3); other searches list only available products.
    """
    if only_available is None:
        only_available = not query
    results = products
    if category:
        results = results[results["category"].map(normalize_text) == normalize_text(category)]
    for word in normalize_text(query).split():
        results = results[results["search_text"].str.contains(word, regex=False)]
    if only_available:
        results = results[results["availability"] == AVAILABLE]
    if only_promotions:
        results = results[results["discount_percent"] > 0]

    summaries = [_product_summary(product) for _, product in results.iterrows()]
    if max_price is not None:
        # Compared with the current price, so promotions are taken into account
        summaries = [summary for summary in summaries if summary["price_brl"] <= max_price]
    summaries.sort(key=lambda summary: summary["price_brl"])
    return {"total_found": len(summaries), "products": summaries[:MAX_SEARCH_RESULTS]}


def get_product_details(products: pd.DataFrame, product_id: int) -> dict:
    """Return price, payment conditions and specs of one product."""
    matches = products[products["product_id"] == product_id]
    if matches.empty:
        return {"error": f"No product found with id {product_id}"}
    product = matches.iloc[0]
    details = _product_summary(product)
    price = details["price_brl"]
    installments = max_installments(price)
    details["pix_price_brl"] = pix_price(price, is_promotional="discount_percent" in details)
    details["max_installments"] = installments
    details["installment_value_brl"] = installment_value(price, installments)
    details["can_combine_payments"] = can_combine_payments(price)
    # Only Campo Grande has a fixed rule; other cities need a quote from the team (manual 5.2)
    details["shipping_campo_grande_brl"] = shipping_fee(price, METRO_CITY)
    details["specs"] = product["specs"]
    return details


def load_orders() -> pd.DataFrame:
    """Load orders joined with the customer's contact data and a readable list of items."""
    orders = read_table("orders")
    customers = read_table("customers").rename(columns={"name": "customer_name"})
    items = read_table("order_items").merge(read_table("products")[["product_id", "name"]], on="product_id", how="left")

    items["item"] = items["quantity"].astype(str) + "x " + items["name"]
    items_by_order = items.groupby("order_id")["item"].apply(list).reset_index(name="items")

    orders = orders.merge(customers[["customer_id", "customer_name", "email", "phone", "city"]], on="customer_id", how="left")
    orders = orders.merge(items_by_order, on="order_id", how="left")
    orders["order_date"] = pd.to_datetime(orders["order_date"]).dt.date
    orders["estimated_delivery"] = pd.to_datetime(orders["estimated_delivery"]).dt.date
    return orders


def _digits(text: str) -> str:
    """Keep only the digits of a text, e.g. "(67) 98432-1098" -> "67984321098"."""
    return "".join(char for char in text if char.isdigit())


def contact_matches_customer(order: pd.Series, contact: str) -> bool:
    """Return True if the contact (e-mail or phone) is the one registered for the order."""
    contact = contact.strip()
    if "@" in contact:
        return contact.casefold() == order["email"].casefold()
    contact_digits = _digits(contact)
    return contact_digits != "" and contact_digits == _digits(order["phone"])


def _payment_label(payment_method: str) -> str:
    """Translate a payment code into Portuguese, e.g. "credit_6x" -> "cartão de crédito em 6x"."""
    if payment_method.startswith(CREDIT_PREFIX):
        installments = payment_method.removeprefix(CREDIT_PREFIX).rstrip("x")
        return f"cartão de crédito em {installments}x"
    return PAYMENT_LABELS.get(payment_method, payment_method)


def get_order_status(orders: pd.DataFrame, order_id: int, contact: str, reference_date: date) -> dict:
    """Return the status of an order after checking the customer's contact (manual 9, LGPD)."""
    matches = orders[orders["order_id"] == order_id]
    # Same answer for an unknown order and a wrong contact, so order numbers cannot be guessed
    if matches.empty or not contact_matches_customer(matches.iloc[0], contact):
        return {"error": ORDER_NOT_FOUND}
    order = matches.iloc[0]
    has_delivery_date = not pd.isna(order["estimated_delivery"])

    status = {
        "order_id": int(order["order_id"]),
        "customer_first_name": order["customer_name"].split()[0],
        "status": ORDER_STATUS_LABELS.get(order["status"], order["status"]),
        "order_date": order["order_date"].isoformat(),
        "items": order["items"],
        "total_brl": float(order["total_brl"]),
        "payment": _payment_label(order["payment_method"]),
        "tracking_code": None if pd.isna(order["tracking_code"]) else order["tracking_code"],
        "estimated_delivery": order["estimated_delivery"].isoformat() if has_delivery_date else None,
    }
    if not pd.isna(order["notes"]):
        status["notes"] = order["notes"]
    if order["status"] == DELIVERED_STATUS:
        # Assumption: the estimated delivery date is treated as the date the customer received it
        received = order["estimated_delivery"]
        status["return_window_open"] = is_within_return_window(received, reference_date)
        status["defect_coverage"] = defect_coverage(order["order_date"], received, reference_date)
    return status