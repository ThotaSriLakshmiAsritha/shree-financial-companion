from decimal import ROUND_HALF_UP, Decimal


def goal_progress_percentage(current_amount: Decimal, target_amount: Decimal) -> Decimal:
    if target_amount <= 0:
        raise ValueError("Target amount must be greater than zero.")
    percentage = (current_amount / target_amount * Decimal(100)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return min(max(percentage, Decimal("0.00")), Decimal("100.00"))
