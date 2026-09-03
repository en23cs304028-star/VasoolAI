import datetime
import os
import json
import pytest
import time
from fastapi.testclient import TestClient
from backend.main import app
from backend.db import SessionLocal
from backend.risk_model.train import train_model

@pytest.fixture(scope="module")
def setup_data():
    client = TestClient(app)
    # Generate larger batch for training
    res = client.post("/admin/generate-batch?n=1000&seed=42")
    assert res.status_code == 200
    
    # Train model
    train_model()
    
    yield client

def test_score_invoice(setup_data):
    client = setup_data
    # get an invoice
    res = client.get("/invoices")
    invoices = res.json()
    assert len(invoices) > 0
    
    inv_id = invoices[0]["id"]
    
    # Score it
    start_time = time.time()
    res = client.post(f"/invoices/{inv_id}/score")
    elapsed = time.time() - start_time
    
    assert res.status_code == 200
    assert elapsed < 0.500 # Ensure under 500ms
    
    data = res.json()
    assert "risk_probability" in data
    assert "risk_tier" in data
    assert "shap_top_features" in data
    
    # Check shape of shap
    shap_features = json.loads(data["shap_top_features"])
    assert len(shap_features) <= 3

def test_batch_score(setup_data):
    client = setup_data
    res = client.post("/batch/score")
    assert res.status_code == 200
    data = res.json()
    assert "scored" in data
    assert data["scored"] > 0
