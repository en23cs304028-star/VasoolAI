import { request } from './client';
import { Invoice, InvoiceDetail } from '../types/models';

export interface GetInvoicesParams {
  status?: string;
  overdue?: boolean;
}

export async function getInvoices(params?: GetInvoicesParams): Promise<Invoice[]> {
  const query = new URLSearchParams();
  if (params?.status) query.append('status', params.status);
  if (params?.overdue !== undefined) query.append('overdue', String(params.overdue));

  const qs = query.toString();
  return request<Invoice[]>(`/invoices${qs ? `?${qs}` : ''}`);
}

export async function getInvoice(id: number): Promise<InvoiceDetail> {
  return request<InvoiceDetail>(`/invoices/${id}`);
}

export async function scoreInvoice(id: number): Promise<{
  risk_probability: number;
  risk_tier: string;
  shap_top_features: string;
  model_version: string;
}> {
  return request(`/invoices/${id}/score`, { method: 'POST' });
}

export async function planAction(id: number): Promise<{
  status: string;
  action_id?: number;
  reason?: string;
}> {
  return request(`/invoices/${id}/plan-action`, { method: 'POST' });
}
