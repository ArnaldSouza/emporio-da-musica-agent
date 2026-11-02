from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from business_rules import (
    CAMPO_GRANDE_TZ,
    LEGAL_WARRANTY,
    MANUFACTURER_WARRANTY,
    STORE_EXCHANGE,
    apply_discount,
    can_combine_payments,
    defect_coverage,
    format_brl,
    installment_value,
    is_store_open,
    is_within_return_window,
    max_installments,
    pix_price,
    shipping_fee,
)

REFERENCE_DATE = date(2026, 3, 25)


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


def test_shipping_is_free_above_threshold_in_campo_grande():
    assert shipping_fee(599.90, "Campo Grande") == 0.0


def test_shipping_has_fixed_fee_below_threshold_in_campo_grande():
    assert shipping_fee(349.90, "Campo Grande") == 35.0


def test_shipping_exactly_at_threshold_pays_fee():
    assert shipping_fee(500.00, "Campo Grande") == 35.0


def test_shipping_city_comparison_ignores_case_and_spaces():
    assert shipping_fee(599.90, "  campo grande ") == 0.0


def test_shipping_outside_campo_grande_needs_quote():
    assert shipping_fee(599.90, "Dourados") is None


def test_return_window_includes_seventh_day():
    assert is_within_return_window(date(2026, 3, 18), date(2026, 3, 25)) is True


def test_return_window_closes_after_seventh_day():
    assert is_within_return_window(date(2026, 3, 17), date(2026, 3, 25)) is False


def test_return_window_rejects_reference_before_receipt():
    with pytest.raises(ValueError):
        is_within_return_window(date(2026, 3, 26), date(2026, 3, 25))


def test_defect_within_thirty_days_of_purchase_is_store_exchange():
    assert defect_coverage(date(2026, 2, 23), date(2026, 2, 27), REFERENCE_DATE) == STORE_EXCHANGE


def test_defect_after_thirty_days_within_ninety_of_receipt_is_legal_warranty():
    assert defect_coverage(date(2026, 1, 5), date(2026, 1, 18), REFERENCE_DATE) == LEGAL_WARRANTY


def test_defect_after_ninety_days_of_receipt_is_manufacturer_warranty():
    assert defect_coverage(date(2025, 10, 15), date(2025, 10, 25), REFERENCE_DATE) == MANUFACTURER_WARRANTY


def test_defect_rejects_reference_before_purchase():
    with pytest.raises(ValueError):
        defect_coverage(date(2026, 3, 26), date(2026, 3, 28), REFERENCE_DATE)


def test_store_is_open_on_weekday_business_hours():
    assert is_store_open(datetime(2026, 3, 25, 10, 0, tzinfo=CAMPO_GRANDE_TZ)) is True


def test_store_closes_at_closing_time():
    assert is_store_open(datetime(2026, 3, 25, 18, 0, tzinfo=CAMPO_GRANDE_TZ)) is False


def test_store_closes_at_one_pm_on_saturday():
    assert is_store_open(datetime(2026, 3, 28, 12, 59, tzinfo=CAMPO_GRANDE_TZ)) is True
    assert is_store_open(datetime(2026, 3, 28, 13, 0, tzinfo=CAMPO_GRANDE_TZ)) is False


def test_store_is_closed_on_sunday():
    assert is_store_open(datetime(2026, 3, 29, 10, 0, tzinfo=CAMPO_GRANDE_TZ)) is False


def test_store_hours_use_campo_grande_time_for_brasilia_moments():
    brasilia_9_30 = datetime(2026, 3, 25, 9, 30, tzinfo=ZoneInfo("America/Sao_Paulo"))
    assert is_store_open(brasilia_9_30) is False  # 08:30 in Campo Grande


def test_store_open_rejects_moment_without_time_zone():
    with pytest.raises(ValueError):
        is_store_open(datetime(2026, 3, 25, 10, 0))


def test_installment_value_divides_total():
    assert installment_value(2199.00, 12) == 183.25


def test_installment_value_rounds_half_up_to_cents():
    assert installment_value(100.01, 2) == 50.01


def test_installment_value_rejects_zero_installments():
    with pytest.raises(ValueError):
        installment_value(100.00, 0)


def test_format_brl_uses_brazilian_separators():
    assert format_brl(1967.18) == "R$ 1.967,18"
    assert format_brl(11499) == "R$ 11.499,00"


def test_format_brl_small_values_and_zero():
    assert format_brl(35) == "R$ 35,00"
    assert format_brl(0.0) == "R$ 0,00"