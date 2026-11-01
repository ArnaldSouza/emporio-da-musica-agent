import pytest

from tools import (
    AVAILABLE,
    COMING_SOON,
    DISCONTINUED,
    OUT_OF_STOCK,
    load_products,
    normalize_text,
    product_availability,
    read_table,
    search_products,
)


def test_read_table_loads_products():
    products = read_table("products")
    assert len(products) == 65
    assert "price_brl" in products.columns


def test_read_table_missing_file_raises_clear_error():
    with pytest.raises(FileNotFoundError):
        read_table("does_not_exist")


def test_normalize_text_removes_accents_and_case():
    assert normalize_text("Violão Elétrico") == "violao eletrico"


def test_normalize_text_handles_cedilla_and_spaces():
    assert normalize_text("  AÇO ") == "aco"


def test_availability_active_with_stock_is_available():
    assert product_availability("active", 5) == AVAILABLE


def test_availability_active_without_stock_is_out_of_stock():
    assert product_availability("active", 0) == OUT_OF_STOCK


def test_availability_status_prevails_over_stock():
    assert product_availability("coming_soon", 2) == COMING_SOON
    assert product_availability("discontinued", 13) == DISCONTINUED


def test_availability_rejects_unknown_status():
    with pytest.raises(ValueError):
        product_availability("archived", 1)


def get_product_row(products, product_id):
    """Return one product row by id (test helper)."""
    return products[products["product_id"] == product_id].iloc[0]


def test_load_products_drops_descriptions():
    assert "description" not in load_products().columns


def test_load_products_applies_only_active_promotions():
    products = load_products()
    assert get_product_row(products, 121)["discount_percent"] == 20
    assert get_product_row(products, 95)["discount_percent"] == 0  # its promotion is inactive


def test_load_products_adds_category_and_availability():
    takamine = get_product_row(load_products(), 95)
    assert takamine["category"] == "Violões"
    assert takamine["availability"] == AVAILABLE


def test_load_products_parses_specs_as_dict():
    assert isinstance(get_product_row(load_products(), 95)["specs"], dict)


PRODUCTS = load_products()


def found_ids(result):
    """Return the product ids in a search result (test helper)."""
    return [product["product_id"] for product in result["products"]]


def test_search_by_category_and_max_price_returns_only_matching_available_products():
    result = search_products(PRODUCTS, category="Violões", max_price=1000)
    assert result["total_found"] > 0
    for product in result["products"]:
        assert product["category"] == "Violões"
        assert product["price_brl"] <= 1000
        assert product["availability"] == AVAILABLE


def test_search_results_are_sorted_by_price():
    prices = [product["price_brl"] for product in search_products(PRODUCTS, category="Violões")["products"]]
    assert prices == sorted(prices)


def test_search_excludes_unavailable_products_by_default():
    ids = found_ids(search_products(PRODUCTS, category="Violões", max_price=1000))
    assert 96 not in ids  # out of stock
    assert 113 not in ids  # discontinued


def test_search_by_name_ignores_case_and_accents():
    assert found_ids(search_products(PRODUCTS, query="TAKAMINE gd20")) == [95]
    assert 130 in found_ids(search_products(PRODUCTS, query="baritono", only_available=False))


def test_search_max_price_uses_promotional_price():
    result = search_products(PRODUCTS, category="Ukuleles", max_price=450)
    ohana = next(product for product in result["products"] if product["product_id"] == 121)
    assert ohana["price_brl"] == 439.20
    assert ohana["original_price_brl"] == 549.00
    assert ohana["discount_percent"] == 20


def test_search_without_matches_returns_empty_result():
    assert search_products(PRODUCTS, query="saxofone") == {"total_found": 0, "products": []}