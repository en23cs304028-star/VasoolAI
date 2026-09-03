import random
import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from backend.models import Buyer, Invoice, InvoiceStatus, BUYER_SECTORS, Action, RiskScore
from backend.interest_engine import calculate_due_date
from backend.config import settings

def generate_synthetic_batch(db: Session, n: int = 250, seed: int = 42) -> dict:
    random.seed(seed)
    
    # Clear existing for a clean batch
    db.query(Action).delete()
    db.query(RiskScore).delete()
    db.query(Invoice).delete()
    db.query(Buyer).delete()
    db.commit()
    
    buyers = []
    
    # Create buyers
    for i in range(random.randint(30, 40)):
        # Due to Twilio Sandbox restricting messaging to only verified numbers (in trial mode),
        # all synthetic buyers share the exact same verified test number provided in the .env.
        buyer = Buyer(
            name=f"Buyer Company {i+1}",
            sector=random.choice(BUYER_SECTORS),
            phone_number=settings.TEST_WHATSAPP_NUMBER
        )
        db.add(buyer)
        buyers.append(buyer)
        
    db.commit()
    
    invoices_created = 0
    today = datetime.date.today()
    
    for i in range(n):
        buyer = random.choice(buyers)
        
        # Invoice date in the past 120 days
        days_ago = random.randint(10, 120)
        invoice_date = today - datetime.timedelta(days=days_ago)
        
        agreed_credit_days = random.choice([None, 15, 30, 45, 60])
        due_date = calculate_due_date(invoice_date, agreed_credit_days)
        
        principal = Decimal(random.randint(10000, 400000))
        
        is_open = random.choice([True, False])
        
        if is_open:
            status = InvoiceStatus.open
            actual_payment_date = None
            actual_payment_amount = None
        else:
            status = InvoiceStatus.paid
            actual_payment_amount = principal
            
            # To get ~40% late overall
            is_late = random.random() < 0.4
            if is_late:
                # paid after due date
                days_late = random.randint(1, 90)
                actual_payment_date = due_date + datetime.timedelta(days=days_late)
                if actual_payment_date > today:
                    actual_payment_date = today # Can't pay in the future
            else:
                # paid on time
                actual_payment_date = invoice_date + datetime.timedelta(days=random.randint(1, max(1, (due_date - invoice_date).days)))

        invoice = Invoice(
            buyer_id=buyer.id,
            invoice_number=f"INV-{i+1000}",
            invoice_date=invoice_date,
            agreed_credit_days=agreed_credit_days,
            due_date=due_date,
            principal_amount=principal,
            status=status,
            actual_payment_date=actual_payment_date,
            actual_payment_amount=actual_payment_amount
        )
        db.add(invoice)
        invoices_created += 1
        
    db.commit()
    return {"buyers_created": len(buyers), "invoices_created": invoices_created}
