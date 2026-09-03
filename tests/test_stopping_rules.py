import datetime
import pytest
from backend.db import SessionLocal
from backend.models import Buyer, Invoice, InvoiceStatus, Action, EscalationTier, Channel, AuditLog
from backend.agent.escalation import check_stopping_rules

def test_max_one_message_per_tier():
    db = SessionLocal()
    buyer = Buyer(name="Test Buyer", sector="IT Services")
    db.add(buyer)
    db.commit()
    
    invoice = Invoice(
        buyer_id=buyer.id,
        invoice_number="TEST-1",
        invoice_date=datetime.date(2023, 1, 1),
        agreed_credit_days=15,
        principal_amount=1000,
        due_date=datetime.date(2023, 1, 16),
        status=InvoiceStatus.open
    )
    db.add(invoice)
    db.commit()
    
    today = datetime.date(2023, 1, 20)
    
    try:
        assert check_stopping_rules(buyer.id, invoice.id, EscalationTier.nudge, db, today=today) == True
        
        action = Action(
            invoice_id=invoice.id,
            escalation_tier=EscalationTier.nudge,
            channel=Channel.whatsapp,
            drafted_message="test",
            created_at=datetime.datetime(2023, 1, 20, 10, 0, 0)
        )
        db.add(action)
        db.commit()
        
        assert check_stopping_rules(buyer.id, invoice.id, EscalationTier.nudge, db, today=today) == False
        
        log = db.query(AuditLog).filter(AuditLog.event == "stopping_rule_blocked").order_by(AuditLog.id.desc()).first()
        assert "Max one message per tier" in log.details
    finally:
        db.query(AuditLog).filter(AuditLog.entity_id.in_([buyer.id, invoice.id])).delete(synchronize_session=False)
        db.query(Action).filter(Action.invoice_id == invoice.id).delete(synchronize_session=False)
        db.query(Invoice).filter(Invoice.id == invoice.id).delete(synchronize_session=False)
        db.query(Buyer).filter(Buyer.id == buyer.id).delete(synchronize_session=False)
        db.commit()
        db.close()

def test_five_day_cooldown():
    db = SessionLocal()
    buyer = Buyer(name="Test Buyer 2", sector="IT Services")
    db.add(buyer)
    db.commit()
    
    invoice1 = Invoice(buyer_id=buyer.id, invoice_number="TEST-2", invoice_date=datetime.date(2023, 1, 1), principal_amount=100, due_date=datetime.date(2023, 1, 16), status=InvoiceStatus.open)
    invoice2 = Invoice(buyer_id=buyer.id, invoice_number="TEST-3", invoice_date=datetime.date(2023, 1, 1), principal_amount=100, due_date=datetime.date(2023, 1, 16), status=InvoiceStatus.open)
    db.add_all([invoice1, invoice2])
    db.commit()
    
    today = datetime.date(2023, 1, 20)
    try:
        action = Action(
            invoice_id=invoice1.id,
            escalation_tier=EscalationTier.nudge,
            channel=Channel.whatsapp,
            drafted_message="test",
            created_at=datetime.datetime(2023, 1, 18, 10, 0, 0) # 2 days ago
        )
        db.add(action)
        db.commit()
        
        assert check_stopping_rules(buyer.id, invoice2.id, EscalationTier.nudge, db, today=today) == False
        log = db.query(AuditLog).filter(AuditLog.event == "stopping_rule_blocked").order_by(AuditLog.id.desc()).first()
        assert "5-day cooldown" in log.details
        
        future_today = datetime.date(2023, 1, 25) # 7 days later
        assert check_stopping_rules(buyer.id, invoice2.id, EscalationTier.nudge, db, today=future_today) == True
    finally:
        db.query(AuditLog).filter(AuditLog.entity_id.in_([buyer.id, invoice1.id, invoice2.id])).delete(synchronize_session=False)
        db.query(Action).filter(Action.invoice_id.in_([invoice1.id, invoice2.id])).delete(synchronize_session=False)
        db.query(Invoice).filter(Invoice.id.in_([invoice1.id, invoice2.id])).delete(synchronize_session=False)
        db.query(Buyer).filter(Buyer.id == buyer.id).delete(synchronize_session=False)
        db.commit()
        db.close()

def test_max_four_messages_in_30_days():
    db = SessionLocal()
    buyer = Buyer(name="Test Buyer 3", sector="IT Services")
    db.add(buyer)
    db.commit()
    
    today = datetime.date(2023, 2, 1)
    
    invoices = []
    for i in range(5):
        inv = Invoice(buyer_id=buyer.id, invoice_number=f"TEST-MULTI-{i}", invoice_date=datetime.date(2023, 1, 1), principal_amount=100, due_date=datetime.date(2023, 1, 16), status=InvoiceStatus.open)
        db.add(inv)
        invoices.append(inv)
    db.commit()
    inv_ids = [inv.id for inv in invoices]
    
    try:
        # Add 4 actions spaced by 6 days in last 30 days
        for i in range(4):
            action = Action(
                invoice_id=invoices[i].id,
                escalation_tier=EscalationTier.nudge,
                channel=Channel.whatsapp,
                drafted_message="test",
                created_at=datetime.datetime(2023, 1, 5 + (i * 6), 10, 0, 0) # Jan 5, 11, 17, 23 (all < 30 days from Feb 1)
            )
            db.add(action)
        db.commit()
        
        # 5th should fail
        assert check_stopping_rules(buyer.id, invoices[4].id, EscalationTier.nudge, db, today=today) == False
        log = db.query(AuditLog).filter(AuditLog.event == "stopping_rule_blocked").order_by(AuditLog.id.desc()).first()
        assert "Max four total messages in 30 days" in log.details
    finally:
        db.query(AuditLog).filter(AuditLog.entity_id.in_([buyer.id] + inv_ids)).delete(synchronize_session=False)
        db.query(Action).filter(Action.invoice_id.in_(inv_ids)).delete(synchronize_session=False)
        db.query(Invoice).filter(Invoice.id.in_(inv_ids)).delete(synchronize_session=False)
        db.query(Buyer).filter(Buyer.id == buyer.id).delete(synchronize_session=False)
        db.commit()
        db.close()
