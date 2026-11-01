"""Store business rules with objective criteria from the policy manual.

Money values are rounded to cents with commercial rounding (half up).
"""

from datetime import date, datetime, time
from decimal import ROUND_HALF_UP, Decimal
from zoneinfo import ZoneInfo

PIX_DISCOUNT_PERCENT = 5  # Manual 3: PIX payments get 5% off the list price
CENTS = Decimal("0.01")
MAX_INSTALLMENTS = 12
# Manual 3.1: (highest number of installments in the tier, minimum installment value in BRL)
INSTALLMENT_TIERS = [(3, 50.0), (6, 80.0), (12, 100.0)]
COMBINED_PAYMENT_THRESHOLD = 2000.0  # Manual 3.1: payment methods can be combined above this total
METRO_CITY = "Campo Grande"
FREE_SHIPPING_THRESHOLD = 500.0  # Manual 5.1: free shipping above this total
METRO_SHIPPING_FEE = 35.0  # Manual 5.1: fixed fee below the threshold
RETURN_WINDOW_DAYS = 7  # Manual 4.1 and 4.3: calendar days after receipt
DEFECT_EXCHANGE_DAYS = 30  # Manual 4.2: calendar days after purchase
LEGAL_WARRANTY_DAYS = 90  # Manual 8.1: calendar days after receipt
STORE_EXCHANGE = "store_exchange"
LEGAL_WARRANTY = "legal_warranty"
MANUFACTURER_WARRANTY = "manufacturer_warranty"
CAMPO_GRANDE_TZ = ZoneInfo("America/Campo_Grande")
# Manual 2, local Campo Grande time. Keys follow datetime.weekday(): Monday = 0; Sunday is closed
OPENING_HOURS = {
    0: (time(9), time(18)),
    1: (time(9), time(18)),
    2: (time(9), time(18)),
    3: (time(9), time(18)),
    4: (time(9), time(18)),
    5: (time(9), time(13)),
}

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


def shipping_fee(order_total: float, city: str) -> float | None:
    """Return the shipping fee for Campo Grande, or None when the team must quote it.

    Outside Campo Grande the price depends on ZIP code, weight and dimensions (manual 5.2).
    """
    if city.strip().casefold() != METRO_CITY.casefold():
        return None
    if order_total > FREE_SHIPPING_THRESHOLD:
        return 0.0
    return METRO_SHIPPING_FEE


def is_within_return_window(received_date: date, reference_date: date) -> bool:
    """Return True if a return or preference exchange is still allowed (manual 4.1 and 4.3)."""
    days_since_receipt = (reference_date - received_date).days
    if days_since_receipt < 0:
        raise ValueError("Reference date is before the receipt date")
    return days_since_receipt <= RETURN_WINDOW_DAYS


def defect_coverage(purchase_date: date, received_date: date, reference_date: date) -> str:
    """Return which coverage applies to a defective product today.

    Up to 30 days from purchase: exchange at the store (manual 4.2). After that and up to
    90 days from receipt: legal warranty, with the store mediating (manual 8.1 and 4.2).
    After that: manufacturer warranty (manual 8.2).
    """
    if reference_date < purchase_date:
        raise ValueError("Reference date is before the purchase date")
    if (reference_date - purchase_date).days <= DEFECT_EXCHANGE_DAYS:
        return STORE_EXCHANGE
    if (reference_date - received_date).days <= LEGAL_WARRANTY_DAYS:
        return LEGAL_WARRANTY
    return MANUFACTURER_WARRANTY


def is_store_open(moment: datetime) -> bool:
    """Return True if the store is open at a given moment (manual 2). Holidays are not handled."""
    if moment.tzinfo is None:
        raise ValueError("The moment must include a time zone")
    local_moment = moment.astimezone(CAMPO_GRANDE_TZ)
    hours = OPENING_HOURS.get(local_moment.weekday())
    if hours is None:
        return False
    opening, closing = hours
    return opening <= local_moment.time() < closing