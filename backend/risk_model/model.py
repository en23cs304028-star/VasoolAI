import os
import joblib
import pandas as pd
import shap
import json
import datetime
from sqlalchemy.orm import Session
from backend.models import Invoice, Buyer, RiskTier
from backend.risk_model.features import build_features

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")
_model_cache = None

def get_model():
    global _model_cache
    if _model_cache is None:
        if not os.path.exists(MODEL_PATH):
            raise RuntimeError("Model not trained yet.")
        _model_cache = joblib.load(MODEL_PATH)
    return _model_cache

def predict_risk(invoice_id: int, db: Session, scoring_date: datetime.date = None):
    if scoring_date is None:
        scoring_date = datetime.date.today()
        
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise ValueError("Invoice not found")
        
    buyer = db.query(Buyer).filter(Buyer.id == invoice.buyer_id).first()
    
    df = build_features([invoice], [buyer], scoring_date=scoring_date)
    df = df.drop(columns=['is_late'], errors='ignore')
    
    model_data = get_model()
    model = model_data['model']
    expected_features = model_data['features']
    
    df = df[expected_features]
    
    prob = float(model.predict_proba(df)[0, 1])
    
    if prob < 0.35:
        tier = RiskTier.low
    elif prob <= 0.6:
        tier = RiskTier.medium
    else:
        tier = RiskTier.high
        
    # SHAP explanations
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(df)
    
    feature_names = df.columns
    # Check if shap_values is a list (multiclass) or 2d array (binary)
    if isinstance(shap_values, list):
        # usually shap_values[1] for positive class
        vals = shap_values[1][0]
    else:
        vals = shap_values[0]
        
    abs_shap = [abs(x) for x in vals]
    top_indices = sorted(range(len(abs_shap)), key=lambda i: abs_shap[i], reverse=True)[:3]
    top_features = {feature_names[i]: float(vals[i]) for i in top_indices}
    
    return {
        "risk_probability": prob,
        "risk_tier": tier,
        "shap_top_features": json.dumps(top_features),
        "model_version": "v1.0"
    }
