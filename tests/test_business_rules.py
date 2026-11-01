import pytest

from business_rules import apply_discount, can_combine_payments, max_installments, pix_price


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


def test_max_installments_high_value_reaches_twelve():
    assert max_installments(2199.00) == 12


def test_max_installments_stops_at_tier_minimum():
    assert max_installments(359.00) == 4


def test_max_installments_accepts_exact_tier_limit():
    assert max_installments(480.00) == 6


def test_max_installments_low_value_is_single_payment():
    assert max_installments(99.90) == 1


def test_max_installments_rejects_invalid_total():
    with pytest.raises(ValueError):
        max_installments(0)


def test_can_combine_payments_only_above_threshold():
    assert can_combine_payments(2000.00) is False
    assert can_combine_payments(2000.01) is True