from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db import get_db
from backend.models import BacktestRun
from backend.backtest import run_simulation

router = APIRouter(tags=["backtest"])

@router.post("/backtest/run")
def run_backtest(db: Session = Depends(get_db)):
    try:
        run = run_simulation(db)
        return {
            "id": run.id,
            "run_at": run.run_at.isoformat(),
            "baseline_metric_recovery_days": run.baseline_metric_recovery_days,
            "agent_metric_recovery_days": run.agent_metric_recovery_days,
            "baseline_metric_recovery_rate": run.baseline_metric_recovery_rate,
            "agent_metric_recovery_rate": run.agent_metric_recovery_rate,
            "ablation_metric_recovery_days": run.ablation_metric_recovery_days,
            "ablation_metric_recovery_rate": run.ablation_metric_recovery_rate,
            "notes": run.notes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backtest/latest")
def get_latest_backtest(db: Session = Depends(get_db)):
    run = db.query(BacktestRun).order_by(BacktestRun.run_at.desc()).first()
    if not run:
        raise HTTPException(status_code=404, detail="No backtest runs found")
    return {
        "id": run.id,
        "run_at": run.run_at.isoformat(),
        "baseline_metric_recovery_days": run.baseline_metric_recovery_days,
        "agent_metric_recovery_days": run.agent_metric_recovery_days,
        "baseline_metric_recovery_rate": run.baseline_metric_recovery_rate,
        "agent_metric_recovery_rate": run.agent_metric_recovery_rate,
        "ablation_metric_recovery_days": run.ablation_metric_recovery_days,
        "ablation_metric_recovery_rate": run.ablation_metric_recovery_rate,
        "notes": run.notes
    }
