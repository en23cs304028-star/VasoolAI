from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from backend.db import get_db
from backend.models import AuditLog

router = APIRouter(tags=["audit_log"])

@router.get("/audit-log")
def get_audit_log(entity_type: Optional[str] = None, entity_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        query = query.filter(AuditLog.entity_id == entity_id)
        
    logs = query.order_by(AuditLog.created_at.desc()).all()
    return [{"id": l.id, "entity_type": l.entity_type, "entity_id": l.entity_id, "event": l.event, "details": l.details, "created_at": l.created_at.isoformat()} for l in logs]
