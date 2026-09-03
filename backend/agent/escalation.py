import datetime
from sqlalchemy.orm import Session
from backend.models import Invoice, RiskScore, EscalationTier, Action, AuditLog

def determine_tier(invoice: Invoice, risk_score: RiskScore, today: datetime.date = None) -> EscalationTier | None:
    if today is None:
        today = datetime.date.today()
        
    if today <= invoice.due_date:
        return None
        
    days_overdue = (today - invoice.due_date).days
    
    if 1 <= days_overdue <= 15:
        return EscalationTier.nudge
    elif 16 <= days_overdue <= 30:
        return EscalationTier.firm_reminder
    elif days_overdue >= 31:
        if risk_score and risk_score.risk_probability >= 0.6:
            return EscalationTier.statutory_notice
        # Fallback to firm_reminder if risk is < 0.6.
        # Reasoning: An invoice this overdue shouldn't be fully unescalated. 
        # A firm reminder maintains collection pressure without unwarranted legal escalation.
        return EscalationTier.firm_reminder
        
    return None

def check_stopping_rules(buyer_id: int, invoice_id: int, tier: EscalationTier, db: Session, today: datetime.date = None) -> bool:
    if today is None:
        today = datetime.date.today()
        
    buyer_invoices = [inv.id for inv in db.query(Invoice).filter(Invoice.buyer_id == buyer_id).all()]
    if not buyer_invoices:
        return True
        
    buyer_actions = db.query(Action).filter(Action.invoice_id.in_(buyer_invoices)).all()
    
    for a in buyer_actions:
        if a.invoice_id == invoice_id and a.escalation_tier == tier:
            _log_violation(buyer_id, invoice_id, "Max one message per tier per invoice", db)
            return False
            
    actions_last_30_days = []
    actions_last_5_days = []
    for a in buyer_actions:
        a_date = a.created_at.date()
        days_ago = (today - a_date).days
        if 0 <= days_ago <= 30:
            actions_last_30_days.append(a)
        if 0 <= days_ago < 5:
            actions_last_5_days.append(a)
            
    if len(actions_last_30_days) >= 4:
        _log_violation(buyer_id, invoice_id, "Max four total messages in 30 days", db)
        return False
        
    if len(actions_last_5_days) > 0:
        _log_violation(buyer_id, invoice_id, "5-day cooldown between messages", db)
        return False
        
    return True
    
def _log_violation(buyer_id: int, invoice_id: int, reason: str, db: Session):
    log = AuditLog(
        entity_type="buyer",
        entity_id=buyer_id,
        event="stopping_rule_blocked",
        details=f"Blocked invoice {invoice_id}: {reason}"
    )
    db.add(log)
    db.commit()
