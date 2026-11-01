import pytest

from business_rules import apply_discount, pix_price


def test_apply_discount_rounds_half_up_to_cents():
    assert apply_discount(599.90, 5) == 569.91


def test_apply_discount_with_promotion_percent():
    assert apply_discount(549.00, 20) == 439.20


def test_apply_discount_zero_keeps_price():
    assert apply_discount(1299.00, 0) == 1299.00


def test_apply_discount_rejects_invalid_percent():
    with pytest.raises(ValueError):
        apply_discount(100.00, 120)


def test_pix_price_gets_five_percent_off_list_price():
    assert pix_price(2199.00, is_promotional=False) == 2089.05


def test_pix_price_is_not_cumulative_with_promotion():
    assert pix_price(439.20, is_promotional=True) == 439.20