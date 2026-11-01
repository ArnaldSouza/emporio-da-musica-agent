"""Store business rules with objective criteria from the policy manual.

Money values are rounded to cents with commercial rounding (half up).
"""

from decimal import ROUND_HALF_UP, Decimal

PIX_DISCOUNT_PERCENT = 5  # Manual 3: PIX payments get 5% off the list price
CENTS = Decimal("0.01")
MAX_INSTALLMENTS = 12
# Manual 3.1: (highest number of installments in the tier, minimum installment value in BRL)
INSTALLMENT_TIERS = [(3, 50.0), (6, 80.0), (12, 100.0)]
COMBINED_PAYMENT_THRESHOLD = 2000.0  # Manual 3.1: payment methods can be combined above this total

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


def _minimum_installment(installments: int) -> float:
    """Return the minimum installment value for a number of installments (manual 3.1)."""
    for highest_in_tier, minimum in INSTALLMENT_TIERS:
        if installments <= highest_in_tier:
            return minimum
    raise ValueError(f"More installments than allowed: {installments}")


def max_installments(total: float) -> int:
    """Return the highest number of interest-free installments allowed for a total."""
    if total <= 0:
        raise ValueError(f"Invalid total: {total}")
    for installments in range(MAX_INSTALLMENTS, 1, -1):
        # Multiplying avoids float division errors exactly at the tier limits
        if total >= installments * _minimum_installment(installments):
            return installments
    return 1  # a single payment is always allowed


def can_combine_payments(total: float) -> bool:
    """Return True if the total allows combining payment methods (manual 3.1)."""
    return total > COMBINED_PAYMENT_THRESHOLD