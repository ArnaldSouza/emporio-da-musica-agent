"""Store business rules with objective criteria from the policy manual.

Money values are rounded to cents with commercial rounding (half up).
"""

from decimal import ROUND_HALF_UP, Decimal

PIX_DISCOUNT_PERCENT = 5  # Manual 3: PIX payments get 5% off the list price
CENTS = Decimal("0.01")


def apply_discount(price: float, discount_percent: float) -> float:
    """Return the price after a percentage discount, rounded to cents."""
    if not 0 <= discount_percent <= 100:
        raise ValueError(f"Invalid discount percent: {discount_percent}")
    # Decimal avoids float errors such as 599.90 * 0.95 = 569.9049999...
    discounted = Decimal(str(price)) * (100 - Decimal(str(discount_percent))) / 100
    return float(discounted.quantize(CENTS, rounding=ROUND_HALF_UP))


def pix_price(price: float, is_promotional: bool) -> float:
    """Return the price paid with PIX.

    Promotions are not cumulative, so a promotional price gets no extra PIX discount (manual 6.2).
    """
    if is_promotional:
        return price
    return apply_discount(price, PIX_DISCOUNT_PERCENT)