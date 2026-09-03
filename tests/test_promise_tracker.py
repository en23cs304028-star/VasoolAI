import datetime
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db import SessionLocal
from backend.models import Buyer, Invoice, InvoiceStatus, Action, EscalationTier, Channel, AuditLog

@pytest.fixture
def client():
    return TestClient(app)

def test_promise_to_pay_workflow(client):
    db = SessionLocal()
    # Create test buyer and invoice
    buyer = Buyer(name="Promise Test Buyer", sector="Retail")
    db.add(buyer)
    db.commit()

    invoice = Invoice(
        buyer_id=buyer.id,
        invoice_number="PROMISE-TEST-1",
        invoice_date=datetime.date(2026, 7, 1),
        agreed_credit_days=15,
        principal_amount=50000.0,
        due_date=datetime.date(2026, 7, 16),
        status=InvoiceStatus.open
    )
    db.add(invoice)
    db.commit()

    # Create an action for this invoice
    action = Action(
        invoice_id=invoice.id,
        escalation_tier=EscalationTier.nudge,
        channel=Channel.whatsapp,
        drafted_message="Friendly payment reminder",
        requires_approval=False,
        approved=True,
        sent=False
    )
    db.add(action)
    db.commit()
    db.refresh(action)

    assert action.promised_payment_date is None

    # Call POST /actions/{id}/promise
    promised_date = "2026-08-10"
    res = client.post(f"/actions/{action.id}/promise", json={"promised_date": promised_date})
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "promise_recorded"
    assert data["action_id"] == action.id
    assert data["promised_payment_date"] == promised_date

    # Verify action in DB
    db.refresh(action)
    assert action.promised_payment_date == datetime.date(2026, 8, 10)

    # Verify audit log entry
    audit_entry = db.query(AuditLog).filter(
        AuditLog.entity_type == "action",
        AuditLog.entity_id == action.id,
        AuditLog.event == "promise_to_pay_recorded"
    ).order_by(AuditLog.id.desc()).first()
    assert audit_entry is not None
    assert "2026-08-10" in audit_entry.details

    # Verify GET /actions/{id}
    res_act = client.get(f"/actions/{action.id}")
    assert res_act.status_code == 200
    assert res_act.json()["promised_payment_date"] == promised_date

    # Verify GET /invoices/{id} returns promised_payment_date
    res_inv = client.get(f"/invoices/{invoice.id}")
    assert res_inv.status_code == 200
    assert res_inv.json()["promised_payment_date"] == promised_date
    assert len(res_inv.json()["actions"]) >= 1

    # Clean up test records
    db.query(AuditLog).filter(AuditLog.entity_type == "action", AuditLog.entity_id == action.id).delete()
    db.query(Action).filter(Action.id == action.id).delete()
    db.query(Invoice).filter(Invoice.id == invoice.id).delete()
    db.query(Buyer).filter(Buyer.id == buyer.id).delete()
    db.commit()
    db.close()
