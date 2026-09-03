import pandas as pd
import datetime
from typing import List
from backend.models import Invoice, Buyer, BUYER_SECTORS

def build_features(invoices: List[Invoice], buyers: List[Buyer], scoring_date: datetime.date = None) -> pd.DataFrame:
    buyers_dict = {b.id: b for b in buyers}
    data = []
    
    for inv in invoices:
        buyer = buyers_dict[inv.buyer_id]
        eff_scoring_date = scoring_date if scoring_date else inv.due_date
        
        invoice_amount = float(inv.principal_amount)
        agreed_credit_days = inv.agreed_credit_days if inv.agreed_credit_days is not None else 15
        days_since_invoice_raised = (eff_scoring_date - inv.invoice_date).days
        
        prior_paid = [
            i for i in buyer.invoices 
            if i.id != inv.id 
            and i.status.name == "paid" 
            and i.actual_payment_date is not None
            and i.actual_payment_date <= eff_scoring_date
        ]
        
        buyer_invoice_count_so_far = len(prior_paid)
        
        late_days = []
        prior_amounts = []
        for p_inv in prior_paid:
            delay = (p_inv.actual_payment_date - p_inv.due_date).days
            late_days.append(max(0, delay))
            prior_amounts.append(float(p_inv.principal_amount))
            
        buyer_historical_avg_days_late = sum(late_days) / len(late_days) if late_days else 0.0
        late_count = sum(1 for d in late_days if d > 0)
        buyer_historical_pct_late = late_count / len(late_days) if late_days else 0.0
        
        avg_order = sum(prior_amounts) / len(prior_amounts) if prior_amounts else invoice_amount
        invoice_amount_pct_of_buyer_avg_order = invoice_amount / avg_order if avg_order > 0 else 1.0
        
        month_of_year = inv.invoice_date.month
        
        row = {
            "invoice_id": inv.id,
            "invoice_amount": invoice_amount,
            "agreed_credit_days": agreed_credit_days,
            "days_since_invoice_raised": days_since_invoice_raised,
            "buyer_historical_avg_days_late": buyer_historical_avg_days_late,
            "buyer_historical_pct_late": buyer_historical_pct_late,
            "buyer_invoice_count_so_far": buyer_invoice_count_so_far,
            "invoice_amount_pct_of_buyer_avg_order": invoice_amount_pct_of_buyer_avg_order,
            "month_of_year": month_of_year,
        }
        
        for sector in BUYER_SECTORS:
            row[f"sector_{sector}"] = 1 if buyer.sector == sector else 0
            
        if inv.status.name == "paid" and inv.actual_payment_date:
            row["is_late"] = 1 if inv.actual_payment_date > inv.due_date else 0
        else:
            row["is_late"] = None
            
        data.append(row)
        
    df = pd.DataFrame(data)
    if not df.empty:
        df.set_index("invoice_id", inplace=True)
    return df
