import os
import joblib
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, roc_auc_score
from backend.db import SessionLocal
from backend.models import Invoice, Buyer
from backend.risk_model.features import build_features

def train_model():
    db = SessionLocal()
    invoices = db.query(Invoice).filter(Invoice.status == "paid").all()
    buyers = db.query(Buyer).all()
    
    if not invoices:
        print("No training data found.")
        return
        
    df = build_features(invoices, buyers, scoring_date=None)
    df = df.dropna(subset=['is_late'])
    
    if len(df) < 10:
        print("Not enough data to train.")
        return
    
    y = df['is_late'].astype(int)
    X = df.drop(columns=['is_late'])
    
    # Train test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    model = XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    auc = roc_auc_score(y_test, y_prob)
    
    print(f"Test Precision: {precision:.4f}")
    print(f"Test Recall: {recall:.4f}")
    print(f"Test AUC: {auc:.4f}")
    
    model_dir = os.path.dirname(os.path.abspath(__file__))
    joblib.dump({"model": model, "features": X.columns.tolist()}, os.path.join(model_dir, "model.joblib"))
    print("Model saved to model.joblib")
    
if __name__ == "__main__":
    train_model()
