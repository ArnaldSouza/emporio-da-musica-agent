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