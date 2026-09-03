import datetime
from sqlalchemy.orm import Session
from backend.models import Invoice, RiskScore, Action, Channel
from backend.agent.escalation import determine_tier, check_stopping_rules
from backend.risk_model.model import predict_risk
from backend.interest_engine import calculate_interest
from backend.llm.client import draft_message

def plan_action_for_invoice(invoice_id: int, db: Session, today: datetime.date = None) -> Action | None:
    if today is None:
        today = datetime.date.today()
        
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise ValueError("Invoice not found")
        
    risk_score = db.query(RiskScore).filter(RiskScore.invoice_id == invoice_id).order_by(RiskScore.id.desc()).first()
    if not risk_score:
        prediction = predict_risk(invoice_id, db, scoring_date=today)
        risk_score = RiskScore(
            invoice_id=invoice_id,
            risk_probability=prediction["risk_probability"],
            risk_tier=prediction["risk_tier"],
            shap_top_features=prediction["shap_top_features"],
            model_version=prediction["model_version"]
        )
        db.add(risk_score)
        db.flush()
        
    tier = determine_tier(invoice, risk_score, today)
    if tier is None:
        return None
        
    if not check_stopping_rules(invoice.buyer_id, invoice_id, tier, db, today):
        return None
        
    days_overdue = (today - invoice.due_date).days if today > invoice.due_date else 0
    
    interest_amount = None
    if tier.name == "statutory_notice":
        interest_amount = calculate_interest(invoice.principal_amount, invoice.due_date, today)
        
    from backend.channels.razorpay_client import generate_payment_link
    
    amount_to_pay = float(invoice.principal_amount)
    if interest_amount:
        amount_to_pay += float(interest_amount)
        
    payment_link_url = generate_payment_link(
        amount=amount_to_pay,
        reference_id=f"{invoice.invoice_number}-{int(today.strftime('%Y%m%d'))}",
        description=f"Payment for {invoice.invoice_number}"
    )
        
    facts = {
        "buyer_name": invoice.buyer.name,
        "invoice_number": invoice.invoice_number,
        "principal_amount": float(invoice.principal_amount),
        "days_overdue": days_overdue,
        "interest_amount": float(interest_amount) if interest_amount else None,
        "payment_link": payment_link_url
    }
    
    drafted_message = draft_message(tier.name, facts)
    
    # Map tier to channel
    selected_channel = Channel.email if tier.name == "statutory_notice" else Channel.whatsapp
    
    action = Action(
        invoice_id=invoice.id,
        escalation_tier=tier,
        channel=selected_channel,
        drafted_message=drafted_message,
        computed_interest_amount=interest_amount,
        payment_link_url=payment_link_url,
        requires_approval=True if tier.name == "statutory_notice" else False
    )
    db.add(action)
    db.commit()
    
    return action
