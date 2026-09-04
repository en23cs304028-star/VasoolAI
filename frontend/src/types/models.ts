export type RiskTier = 'low' | 'medium' | 'high' | 'unscored';
export type InvoiceStatus = 'open' | 'paid' | 'partially_paid';
export type EscalationTier = 'nudge' | 'firm_reminder' | 'statutory_notice';
export type Channel = 'whatsapp' | 'email';
export type ActionStatus = 'Queued' | 'Pending approval' | 'Sent';

export interface Invoice {
  id: number;
  buyer_id: number;
  buyer_name: string;
  invoice_number: string;
  invoice_date: string;
  due_date: string;
  principal_amount: number;
  status: InvoiceStatus;
  actual_payment_date: string | null;
  interest_owed: number;
  is_overdue: boolean;
  days_overdue: number;
  risk_tier: RiskTier;
  risk_probability: number | null;
  action_status: ActionStatus | null;
  action_tier: EscalationTier | null;
  latest_action_id: number | null;
}

export interface Action {
  id: number;
  escalation_tier: EscalationTier;
  channel: Channel;
  drafted_message: string;
  requires_approval: boolean;
  approved: boolean;
  approved_by: string | null;
  sent: boolean;
  sent_at: string | null;
  promised_payment_date: string | null;
  created_at: string;
}

export interface ShapFeature {
  feature: string;
  importance?: number;
  value?: number | string;
}

export interface InvoiceDetail extends Invoice {
  supplier_name: string;
  agreed_credit_days: number | null;
  actual_payment_amount: number | null;
  created_at: string;
  model_version: string | null;
  shap_top_features: string | null;
  promised_payment_date: string | null;
  actions: Action[];
}

export interface AuditLogEntry {
  id: number;
  entity_type: 'invoice' | 'buyer' | 'action' | string;
  entity_id: number;
  event: string;
  details: string;
  created_at: string;
}

export interface BacktestRun {
  id: number;
  run_at: string;
  baseline_metric_recovery_days: number;
  agent_metric_recovery_days: number;
  baseline_metric_recovery_rate: number;
  agent_metric_recovery_rate: number;
  ablation_metric_recovery_days?: number;
  ablation_metric_recovery_rate?: number;
  notes?: string | null;
}
