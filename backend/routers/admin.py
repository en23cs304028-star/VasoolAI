from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db import get_db
from backend.data_gen import generate_synthetic_batch

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/generate-batch")
def generate_batch(n: int = 250, seed: int = 42, db: Session = Depends(get_db)):
    return generate_synthetic_batch(db, n=n, seed=seed)
