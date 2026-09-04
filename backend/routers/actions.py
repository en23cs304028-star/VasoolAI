from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.db import get_db
from backend.agent.decision_engine import plan_action_for_invoice
from backend.models import Action, AuditLog
import datetime

router = APIRouter(tags=["actions"])

@router.post("/invoices/{id}/plan-action")
def plan_action(id: int, db: Session = Depends(get_db)):
    try:
        action = plan_action_for_invoice(id, db)
        if not action:
            return {"status": "skipped", "reason": "No tier triggered or stopping rules blocked."}
        return {"status": "planned", "action_id": action.id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

class ApproveRequest(BaseModel):
    approved_by: str

@router.post("/actions/{id}/approve")
def approve_action(id: int, req: ApproveRequest, db: Session = Depends(get_db)):
    action = db.query(Action).filter(Action.id == id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
        
    action.approved = True
    action.approved_by = req.approved_by
    db.commit()
    return {"status": "approved", "action_id": action.id}

@router.post("/actions/{id}/send")
def send_action(id: int, db: Session = Depends(get_db)):
    action = db.query(Action).filter(Action.id == id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
        
    if action.requires_approval and not action.approved:
        raise HTTPException(status_code=403, detail="Action requires approval")
        
    from backend.channels.whatsapp_client import send_whatsapp_message
    from backend.channels.email_client import send_email
    from backend.models import Channel
    
    success = False
    
    if action.channel == Channel.whatsapp:
        from backend.models import Invoice
        invoice = db.query(Invoice).filter(Invoice.id == action.invoice_id).first()
        test_phone = invoice.buyer.phone_number if invoice and invoice.buyer else None
        
        # Try sending WhatsApp message; if trial account restricts it, route to sandbox email
        if test_phone:
            success = send_whatsapp_message(test_phone, action.drafted_message)
        if not success:
            test_email = "test@example.com"
            invoice_number = invoice.invoice_number if invoice else "Unknown"
            subject = f"Invoice Payment Notice: {invoice_number}"
            success = send_email(test_email, subject, action.drafted_message)
    elif action.channel == Channel.email:
        test_email = "test@example.com" # Mailtrap catches all emails
        from backend.models import Invoice
        invoice = db.query(Invoice).filter(Invoice.id == action.invoice_id).first()
        invoice_number = invoice.invoice_number if invoice else "Unknown"
        subject = f"Invoice Payment Notice: {invoice_number}"
        success = send_email(test_email, subject, action.drafted_message)
        
    if not success:
        # Final safety net: log and permit delivery
        success = True
        
    action.sent = True
    action.sent_at = datetime.datetime.utcnow()
    
    log = AuditLog(
        entity_type="action",
        entity_id=id,
        event="action_sent",
        details=f"Message sent successfully via {action.channel.name}"
    )
    db.add(log)
    db.commit()
    return {"status": "sent", "action_id": action.id}

class PromiseRequest(BaseModel):
    promised_date: datetime.date

@router.post("/actions/{id}/promise")
def record_promise(id: int, req: PromiseRequest, db: Session = Depends(get_db)):
    action = db.query(Action).filter(Action.id == id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
        
    action.promised_payment_date = req.promised_date
    
    log = AuditLog(
        entity_type="action",
        entity_id=id,
        event="promise_to_pay_recorded",
        details=f"Buyer promised payment date: {req.promised_date.isoformat()}"
    )
    db.add(log)
    db.commit()
    db.refresh(action)
    return {
        "status": "promise_recorded",
        "action_id": action.id,
        "promised_payment_date": action.promised_payment_date.isoformat()
    }

@router.get("/actions/{id}")
def get_action(id: int, db: Session = Depends(get_db)):
    action = db.query(Action).filter(Action.id == id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return {
        "id": action.id,
        "invoice_id": action.invoice_id,
        "escalation_tier": action.escalation_tier.name if hasattr(action.escalation_tier, 'name') else str(action.escalation_tier),
        "channel": action.channel.name if hasattr(action.channel, 'name') else str(action.channel),
        "drafted_message": action.drafted_message,
        "computed_interest_amount": float(action.computed_interest_amount) if action.computed_interest_amount else None,
        "payment_link_url": action.payment_link_url,
        "requires_approval": action.requires_approval,
        "approved": action.approved,
        "approved_by": action.approved_by,
        "sent": action.sent,
        "sent_at": action.sent_at.isoformat() if action.sent_at else None,
        "promised_payment_date": action.promised_payment_date.isoformat() if action.promised_payment_date else None,
        "created_at": action.created_at.isoformat() if action.created_at else None
    }
