import pytest

from tools import normalize_text, read_table


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