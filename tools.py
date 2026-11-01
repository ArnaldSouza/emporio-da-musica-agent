"""Data access tools used by the agent: product catalog and orders."""

import unicodedata
from pathlib import Path

import json
import pandas as pd
from business_rules import apply_discount


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
    only_available: bool = True,
) -> dict:
    """Search the catalog by words in the name, category and maximum price, cheapest first."""
    results = products
    if category:
        results = results[results["category"].map(normalize_text) == normalize_text(category)]
    for word in normalize_text(query).split():
        results = results[results["search_text"].str.contains(word, regex=False)]
    if only_available:
        results = results[results["availability"] == AVAILABLE]

    summaries = [_product_summary(product) for _, product in results.iterrows()]
    if max_price is not None:
        # Compared with the current price, so promotions are taken into account
        summaries = [summary for summary in summaries if summary["price_brl"] <= max_price]
    summaries.sort(key=lambda summary: summary["price_brl"])
    return {"total_found": len(summaries), "products": summaries[:MAX_SEARCH_RESULTS]}