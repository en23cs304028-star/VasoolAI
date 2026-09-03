import datetime
from decimal import Decimal
from backend.config import settings

def calculate_due_date(invoice_date: datetime.date, agreed_credit_days: int | None) -> datetime.date:
    """Calculate the due date based on the MSMED Act."""
    if agreed_credit_days is None:
        return invoice_date + datetime.timedelta(days=15)
    return invoice_date + datetime.timedelta(days=min(agreed_credit_days, 45))

def calculate_interest(principal: Decimal, due_date: datetime.date, actual_payment_date: datetime.date) -> Decimal:
    """
    Calculate compound interest based on MSMED Act.
    Interest accrues at 3x RBI Bank rate, compounded monthly.
    """
    days_overdue = (actual_payment_date - due_date).days
    if days_overdue <= 0:
        return Decimal("0.00")
        
    bank_rate = Decimal(str(settings.RBI_BANK_RATE))
    monthly_rate = 3 * bank_rate / Decimal("12")
    
    full_months = days_overdue // 30
    remaining_days = days_overdue % 30
    
    current_principal = Decimal(principal)
    
    for _ in range(full_months):
        current_principal = current_principal * (Decimal("1") + monthly_rate)
        # Rounding at each step to match exact manual calculation in PRD
        current_principal = current_principal.quantize(Decimal("0.01"))
        
    if remaining_days > 0:
        partial_rate = monthly_rate * Decimal(str(remaining_days)) / Decimal("30")
        current_principal = current_principal * (Decimal("1") + partial_rate)
        current_principal = current_principal.quantize(Decimal("0.01"))
        
    interest_owed = current_principal - Decimal(principal)
    return interest_owed
