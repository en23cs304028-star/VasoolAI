from sqlalchemy import Column, Integer, String, DateTime, Date, Numeric, ForeignKey, Boolean, Float, Text, Enum
from sqlalchemy.orm import relationship
import datetime
import enum
from backend.db import Base

BUYER_SECTORS = ["Manufacturing", "IT Services", "Logistics", "Retail", "Healthcare"]

class InvoiceStatus(enum.Enum):
    open = "open"
    paid = "paid"
    partially_paid = "partially_paid"

class RiskTier(enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

class EscalationTier(enum.Enum):
    nudge = "nudge"
    firm_reminder = "firm_reminder"
    statutory_notice = "statutory_notice"

class Channel(enum.Enum):
    whatsapp = "whatsapp"
    email = "email"

class Buyer(Base):
    __tablename__ = "buyers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    sector = Column(String)
    phone_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    invoices = relationship("Invoice", back_populates="buyer")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("buyers.id"))
    supplier_name = Column(String, default="Demo Supplier")
    invoice_number = Column(String, index=True)
    invoice_date = Column(Date)
    agreed_credit_days = Column(Integer, nullable=True)
    due_date = Column(Date)
    principal_amount = Column(Numeric(12, 2))
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.open)
    actual_payment_date = Column(Date, nullable=True)
    actual_payment_amount = Column(Numeric(12, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    buyer = relationship("Buyer", back_populates="invoices")


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    scored_at = Column(DateTime, default=datetime.datetime.utcnow)
    risk_probability = Column(Float)
    risk_tier = Column(Enum(RiskTier))
    shap_top_features = Column(Text) # JSON stored as text
    model_version = Column(String)


class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    escalation_tier = Column(Enum(EscalationTier))
    channel = Column(Enum(Channel))
    drafted_message = Column(Text)
    computed_interest_amount = Column(Numeric(12, 2), nullable=True)
    payment_link_url = Column(Text, nullable=True)
    requires_approval = Column(Boolean)
    approved = Column(Boolean, default=False)
    approved_by = Column(String, nullable=True)
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    promised_payment_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String)
    entity_id = Column(Integer)
    event = Column(String)
    details = Column(Text) # JSON stored as text
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_at = Column(DateTime, default=datetime.datetime.utcnow)
    baseline_metric_recovery_days = Column(Float)
    agent_metric_recovery_days = Column(Float)
    baseline_metric_recovery_rate = Column(Float)
    agent_metric_recovery_rate = Column(Float)
    ablation_metric_recovery_days = Column(Float)
    ablation_metric_recovery_rate = Column(Float)
    notes = Column(Text)
