import { request } from './client';
import { AuditLogEntry } from '../types/models';

export interface GetAuditLogParams {
  entity_type?: string;
  entity_id?: number;
}

export async function getAuditLog(params?: GetAuditLogParams): Promise<AuditLogEntry[]> {
  const query = new URLSearchParams();
  if (params?.entity_type) query.append('entity_type', params.entity_type);
  if (params?.entity_id !== undefined) query.append('entity_id', String(params.entity_id));

  const qs = query.toString();
  return request<AuditLogEntry[]>(`/audit-log${qs ? `?${qs}` : ''}`);
}
