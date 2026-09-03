import datetime
from sqlalchemy.orm import Session
from backend.models import Invoice, RiskScore, EscalationTier, BacktestRun
from backend.agent.escalation import determine_tier

class MockAction:
    def __init__(self, invoice_id: int, tier: EscalationTier, created_at: datetime.date):
        self.invoice_id = invoice_id
        self.escalation_tier = tier
        self.created_at = created_at

def simulate_stopping_rules(buyer_invoices: list[int], invoice_id: int, tier: EscalationTier, current_day: datetime.date, all_simulated_actions: list[MockAction]) -> bool:
    buyer_actions = [a for a in all_simulated_actions if a.invoice_id in buyer_invoices]
    
    for a in buyer_actions:
        if a.invoice_id == invoice_id and a.escalation_tier == tier:
            return False
            
    actions_last_30_days = []
    actions_last_5_days = []
    for a in buyer_actions:
        days_ago = (current_day - a.created_at).days
        if 0 <= days_ago <= 30:
            actions_last_30_days.append(a)
        if 0 <= days_ago < 5:
            actions_last_5_days.append(a)
            
    if len(actions_last_30_days) >= 4:
        return False
        
    if len(actions_last_5_days) > 0:
        return False
        
    return True

def run_simulation(db: Session) -> BacktestRun:
    invoices = db.query(Invoice).filter(Invoice.status == 'paid', Invoice.actual_payment_date > Invoice.due_date).all()
    
    if not invoices:
        run = BacktestRun(
            run_at=datetime.datetime.utcnow(),
            baseline_metric_recovery_days=0.0,
            agent_metric_recovery_days=0.0,
            baseline_metric_recovery_rate=0.0,
            agent_metric_recovery_rate=0.0,
            notes="No late paid invoices found for backtest."
        )
        db.add(run)
        db.commit()
        return run
        
    # Pre-fetch risk scores
    risk_scores = {}
    for rs in db.query(RiskScore).all():
        if rs.invoice_id not in risk_scores or rs.scored_at > risk_scores[rs.invoice_id].scored_at:
            risk_scores[rs.invoice_id] = rs
            
    # Group invoices by buyer
    buyer_invoices_map = {}
    for inv in invoices:
        if inv.buyer_id not in buyer_invoices_map:
            buyer_invoices_map[inv.buyer_id] = []
        buyer_invoices_map[inv.buyer_id].append(inv.id)
        
    # Find min and max dates for simulation loop
    min_date = min(inv.due_date for inv in invoices)
    max_date = max(inv.actual_payment_date for inv in invoices)
    
    agent_first_contact = {} # invoice_id -> date
    simulated_actions = []
    
    current_day = min_date
    while current_day <= max_date:
        for inv in invoices:
            if inv.due_date < current_day <= inv.actual_payment_date:
                if inv.id not in agent_first_contact:
                    rs = risk_scores.get(inv.id)
                    tier = determine_tier(inv, rs, current_day)
                    if tier:
                        buyer_invs = buyer_invoices_map[inv.buyer_id]
                        if simulate_stopping_rules(buyer_invs, inv.id, tier, current_day, simulated_actions):
                            agent_first_contact[inv.id] = current_day
                            simulated_actions.append(MockAction(inv.id, tier, current_day))
        current_day += datetime.timedelta(days=1)
        
    baseline_adv_notice = []
    agent_adv_notice = []
    ablation_adv_notice = []
    
    for inv in invoices:
        baseline_contact = inv.due_date + datetime.timedelta(days=45)
        b_adv = (inv.actual_payment_date - baseline_contact).days
        baseline_adv_notice.append(b_adv)
        
        a_contact = agent_first_contact.get(inv.id)
        if a_contact:
            a_adv = (inv.actual_payment_date - a_contact).days
            agent_adv_notice.append(a_adv)
        else:
            agent_adv_notice.append(-1)
            
        ablation_contact = inv.due_date + datetime.timedelta(days=1)
        ab_adv = (inv.actual_payment_date - ablation_contact).days
        ablation_adv_notice.append(ab_adv)
            
    pop_size = len(invoices)
    
    b_recovered = sum(1 for adv in baseline_adv_notice if adv >= 0)
    b_rec_rate = b_recovered / pop_size if pop_size > 0 else 0
    
    a_recovered = sum(1 for adv in agent_adv_notice if adv >= 0)
    a_rec_rate = a_recovered / pop_size if pop_size > 0 else 0
    
    ab_recovered = sum(1 for adv in ablation_adv_notice if adv >= 0)
    ab_rec_rate = ab_recovered / pop_size if pop_size > 0 else 0
    
    b_mean_adv = sum(baseline_adv_notice) / len(baseline_adv_notice) if baseline_adv_notice else 0
    a_mean_adv = sum(agent_adv_notice) / len(agent_adv_notice) if agent_adv_notice else 0
    ab_mean_adv = sum(ablation_adv_notice) / len(ablation_adv_notice) if ablation_adv_notice else 0
    
    run = BacktestRun(
        run_at=datetime.datetime.utcnow(),
        baseline_metric_recovery_days=b_mean_adv,
        agent_metric_recovery_days=a_mean_adv,
        baseline_metric_recovery_rate=b_rec_rate,
        agent_metric_recovery_rate=a_rec_rate,
        ablation_metric_recovery_days=ab_mean_adv,
        ablation_metric_recovery_rate=ab_rec_rate,
        notes="Evaluated late paid invoices. Metric is Days of Advance Notice (higher is better)."
    )
    db.add(run)
    db.commit()
    
    return run
