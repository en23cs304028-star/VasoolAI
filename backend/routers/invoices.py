from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from backend.db import get_db
from backend.models import Invoice, InvoiceStatus, RiskScore, AuditLog, Action
from backend.interest_engine import calculate_interest
from backend.risk_model.model import predict_risk
import datetime

router = APIRouter(prefix="/invoices", tags=["invoices"])

@router.get("")
def list_invoices(
    status: Optional[InvoiceStatus] = None,
    overdue: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Invoice)
    if status:
        query = query.filter(Invoice.status == status)
        
    invoices = query.all()
    today = datetime.date.today()
    
    results = []
    for inv in invoices:
        if inv.status == InvoiceStatus.open:
            payment_date_to_use = today
        else:
            payment_date_to_use = inv.actual_payment_date or today
            
        interest = calculate_interest(inv.principal_amount, inv.due_date, payment_date_to_use)
        is_overdue = (payment_date_to_use > inv.due_date)
        
        if overdue is True and not is_overdue:
            continue
        if overdue is False and is_overdue:
            continue
            
        latest_risk = db.query(RiskScore).filter(RiskScore.invoice_id == inv.id).order_by(RiskScore.id.desc()).first()
        risk_tier = latest_risk.risk_tier.name if latest_risk else "unscored"
        latest_action = db.query(Action).filter(Action.invoice_id == inv.id).order_by(Action.id.desc()).first()

        action_status = None
        if latest_action:
            if latest_action.sent:
                action_status = "Sent"
            elif latest_action.requires_approval and not latest_action.approved:
                action_status = "Pending approval"
            else:
                action_status = "Queued"

        days_overdue = max(0, (payment_date_to_use - inv.due_date).days) if is_overdue else 0

        results.append({
            "id": inv.id,
            "buyer_id": inv.buyer_id,
            "buyer_name": inv.buyer.name if inv.buyer else f"Buyer #{inv.buyer_id}",
            "invoice_number": inv.invoice_number,
            "invoice_date": inv.invoice_date,
            "due_date": inv.due_date,
            "principal_amount": float(inv.principal_amount) if inv.principal_amount else 0.0,
            "status": inv.status.name if hasattr(inv.status, 'name') else inv.status,
            "actual_payment_date": inv.actual_payment_date,
            "interest_owed": interest,
            "is_overdue": is_overdue,
            "days_overdue": days_overdue,
            "risk_tier": risk_tier,
            "risk_probability": latest_risk.risk_probability if latest_risk else None,
            "action_status": action_status,
            "action_tier": latest_action.escalation_tier.name if (latest_action and hasattr(latest_action.escalation_tier, 'name')) else (str(latest_action.escalation_tier) if latest_action else None),
            "latest_action_id": latest_action.id if latest_action else None
        })
        
    return results

@router.get("/{id}")
def get_invoice(id: int, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.id == id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    latest_risk = db.query(RiskScore).filter(RiskScore.invoice_id == inv.id).order_by(RiskScore.id.desc()).first()
    actions = db.query(Action).filter(Action.invoice_id == inv.id).order_by(Action.id.desc()).all()
    latest_action = actions[0] if actions else None
    
    promised_payment_date = None
    for a in actions:
        if a.promised_payment_date:
            promised_payment_date = a.promised_payment_date
            break
            
    today = datetime.date.today()
    if inv.status == InvoiceStatus.open:
        payment_date_to_use = today
    else:
        payment_date_to_use = inv.actual_payment_date or today
    interest = calculate_interest(inv.principal_amount, inv.due_date, payment_date_to_use)
    is_overdue = (payment_date_to_use > inv.due_date)
    days_overdue = max(0, (payment_date_to_use - inv.due_date).days) if is_overdue else 0

    return {
        "id": inv.id,
        "buyer_id": inv.buyer_id,
        "buyer_name": inv.buyer.name if inv.buyer else f"Buyer #{inv.buyer_id}",
        "supplier_name": inv.supplier_name,
        "invoice_number": inv.invoice_number,
        "invoice_date": inv.invoice_date.isoformat() if inv.invoice_date else None,
        "agreed_credit_days": inv.agreed_credit_days,
        "due_date": inv.due_date.isoformat() if inv.due_date else None,
        "principal_amount": float(inv.principal_amount) if inv.principal_amount else 0.0,
        "status": inv.status.name if hasattr(inv.status, 'name') else str(inv.status),
        "actual_payment_date": inv.actual_payment_date.isoformat() if inv.actual_payment_date else None,
        "actual_payment_amount": float(inv.actual_payment_amount) if inv.actual_payment_amount else None,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "interest_owed": interest,
        "is_overdue": is_overdue,
        "days_overdue": days_overdue,
        "risk_tier": latest_risk.risk_tier.name if latest_risk else None,
        "risk_probability": latest_risk.risk_probability if latest_risk else None,
        "model_version": latest_risk.model_version if latest_risk else None,
        "shap_top_features": latest_risk.shap_top_features if latest_risk else None,
        "latest_action_id": latest_action.id if latest_action else None,
        "promised_payment_date": promised_payment_date.isoformat() if promised_payment_date else None,
        "actions": [
            {
                "id": a.id,
                "escalation_tier": a.escalation_tier.name if hasattr(a.escalation_tier, 'name') else str(a.escalation_tier),
                "channel": a.channel.name if hasattr(a.channel, 'name') else str(a.channel),
                "drafted_message": a.drafted_message,
                "computed_interest_amount": float(a.computed_interest_amount) if a.computed_interest_amount else None,
                "payment_link_url": a.payment_link_url,
                "requires_approval": a.requires_approval,
                "approved": a.approved,
                "approved_by": a.approved_by,
                "sent": a.sent,
                "sent_at": a.sent_at.isoformat() if a.sent_at else None,
                "promised_payment_date": a.promised_payment_date.isoformat() if a.promised_payment_date else None,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in actions
        ]
    }

@router.post("/{id}/score")
def score_invoice(id: int, db: Session = Depends(get_db)):
    try:
        prediction = predict_risk(id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    risk_score = RiskScore(
        invoice_id=id,
        risk_probability=prediction["risk_probability"],
        risk_tier=prediction["risk_tier"],
        shap_top_features=prediction["shap_top_features"],
        model_version=prediction["model_version"]
    )
    db.add(risk_score)
    
    audit_log = AuditLog(
        entity_type="invoice",
        entity_id=id,
        event="risk_scored",
        details=prediction["shap_top_features"]
    )
    db.add(audit_log)
    db.commit()
    
    return prediction

batch_router = APIRouter(prefix="/batch", tags=["batch"])

@batch_router.post("/score")
def score_batch(db: Session = Depends(get_db)):
    open_invoices = db.query(Invoice).filter(Invoice.status == InvoiceStatus.open).all()
    
    results = []
    for inv in open_invoices:
        try:
            prediction = predict_risk(inv.id, db)
            
            risk_score = RiskScore(
                invoice_id=inv.id,
                risk_probability=prediction["risk_probability"],
                risk_tier=prediction["risk_tier"],
                shap_top_features=prediction["shap_top_features"],
                model_version=prediction["model_version"]
            )
            db.add(risk_score)
            
            audit_log = AuditLog(
                entity_type="invoice",
                entity_id=inv.id,
                event="risk_scored",
                details=prediction["shap_top_features"]
            )
            db.add(audit_log)
            
            results.append({"invoice_id": inv.id, "status": "success", "prediction": prediction})
        except Exception as e:
            results.append({"invoice_id": inv.id, "status": "error", "message": str(e)})
            
    db.commit()
    return {"scored": len(results), "results": results}
