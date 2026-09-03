from fastapi import FastAPI
from backend.db import engine, Base
import backend.models as models
from backend.routers import admin, invoices, actions, audit_log, backtest

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="VasoolAI API")

app.include_router(admin.router)
app.include_router(invoices.router)
app.include_router(invoices.batch_router)
app.include_router(actions.router)
app.include_router(audit_log.router)
app.include_router(backtest.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
