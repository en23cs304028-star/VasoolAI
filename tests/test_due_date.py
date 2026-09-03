import datetime
from backend.interest_engine import calculate_due_date

def test_due_date_default_15_days():
    invoice_date = datetime.date(2023, 1, 1)
    due_date = calculate_due_date(invoice_date, None)
    assert due_date == datetime.date(2023, 1, 16)

def test_due_date_agreed_less_than_45():
    invoice_date = datetime.date(2023, 1, 1)
    due_date = calculate_due_date(invoice_date, 30)
    assert due_date == datetime.date(2023, 1, 31)

def test_due_date_agreed_capped_at_45():
    invoice_date = datetime.date(2023, 1, 1)
    due_date = calculate_due_date(invoice_date, 60)
    assert due_date == datetime.date(2023, 2, 15)
