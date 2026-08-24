from fastapi import FastAPI
from backend.db import engine, Base
import backend.models as models

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="VasoolAI API")

@app.get("/health")
def health_check():
    return {"status": "ok"}
