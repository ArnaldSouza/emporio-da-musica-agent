import pytest
from datetime import date

from business_rules import LEGAL_WARRANTY, MANUFACTURER_WARRANTY
from tools import (
    AVAILABLE,
    COMING_SOON,
    DISCONTINUED,
    OUT_OF_STOCK,
    contact_matches_customer,
    get_order_status,
    get_product_details,
    load_orders,
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


def test_product_details_without_promotion_include_payment_conditions():
    takamine = get_product_details(PRODUCTS, 95)
    assert takamine["price_brl"] == 2199.00
    assert takamine["pix_price_brl"] == 2089.05
    assert takamine["max_installments"] == 12
    assert takamine["installment_value_brl"] == 183.25
    assert takamine["can_combine_payments"] is True
    assert isinstance(takamine["specs"], dict)


def test_product_details_with_promotion_have_no_extra_pix_discount():
    ohana = get_product_details(PRODUCTS, 121)
    assert ohana["price_brl"] == 439.20
    assert ohana["pix_price_brl"] == 439.20
    assert ohana["max_installments"] == 5
    assert ohana["installment_value_brl"] == 87.84


def test_product_details_unknown_id_returns_error():
    assert "error" in get_product_details(PRODUCTS, 9999)


ORDERS = load_orders()


def get_order_row(order_id):
    """Return one order row by id (test helper)."""
    return ORDERS[ORDERS["order_id"] == order_id].iloc[0]


def test_load_orders_joins_customer_and_items():
    order = get_order_row(3)
    assert order["customer_name"] == "Isabela Moreira Cunha"
    assert order["items"] == ["2x Kala KA-ABP-CTG Barítono Cedar"]


def test_load_orders_parses_dates():
    assert get_order_row(1)["order_date"] == date(2025, 10, 15)


def test_contact_matches_email_ignoring_case():
    assert contact_matches_customer(get_order_row(1), "Pedro.Oliveira@JMAIL.com") is True


def test_contact_matches_phone_in_any_format():
    assert contact_matches_customer(get_order_row(1), "67 98432 1098") is True


def test_contact_from_another_customer_does_not_match():
    assert contact_matches_customer(get_order_row(1), "isabela.moreira@jmail.com") is False
    assert contact_matches_customer(get_order_row(1), "") is False


REFERENCE_DATE = date(2026, 3, 25)


def test_order_status_delivered_includes_return_and_warranty_rights():
    order = get_order_status(ORDERS, 5, "rafael.pereira@jmail.com", REFERENCE_DATE)
    assert order["status"] == "entregue"
    assert order["customer_first_name"] == "Rafael"
    assert order["payment"] == "PIX"
    assert order["return_window_open"] is False
    assert order["defect_coverage"] == LEGAL_WARRANTY


def test_order_status_old_delivery_is_manufacturer_warranty():
    order = get_order_status(ORDERS, 1, "(67) 98432-1098", REFERENCE_DATE)
    assert order["defect_coverage"] == MANUFACTURER_WARRANTY


def test_order_status_shipped_has_tracking_and_no_return_rights():
    order = get_order_status(ORDERS, 8, "anacarol.ferreira@coldmail.com", REFERENCE_DATE)
    assert order["status"] == "enviado"
    assert order["tracking_code"] == "BRJL5544332BR"
    assert "return_window_open" not in order


def test_order_status_pending_translates_credit_installments():
    order = get_order_status(ORDERS, 15, "aline.monteiro@jmail.com", REFERENCE_DATE)
    assert order["payment"] == "cartão de crédito em 12x"
    assert order["tracking_code"] is None
    assert len(order["items"]) == 2


def test_order_status_cancelled_includes_notes():
    order = get_order_status(ORDERS, 19, "pedro.oliveira@jmail.com", REFERENCE_DATE)
    assert order["status"] == "cancelado"
    assert order["notes"] == "Pagamento não confirmado dentro do prazo"


def test_order_status_wrong_contact_and_unknown_order_give_same_error():
    wrong_contact = get_order_status(ORDERS, 1, "isabela.moreira@jmail.com", REFERENCE_DATE)
    unknown_order = get_order_status(ORDERS, 999, "pedro.oliveira@jmail.com", REFERENCE_DATE)
    assert "error" in wrong_contact
    assert wrong_contact == unknown_order
    

def test_product_details_include_campo_grande_shipping():
    assert get_product_details(PRODUCTS, 95)["shipping_campo_grande_brl"] == 0.0
    assert get_product_details(PRODUCTS, 121)["shipping_campo_grande_brl"] == 35.0