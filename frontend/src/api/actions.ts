import { request } from './client';

export async function approveAction(id: number, approvedBy: string = 'Finance Operations'): Promise<{
  status: string;
  action_id: number;
}> {
  return request(`/actions/${id}/approve`, {
    method: 'POST',
    body: JSON.stringify({ approved_by: approvedBy }),
  });
}

export async function sendAction(id: number): Promise<{
  status: string;
  action_id: number;
}> {
  return request(`/actions/${id}/send`, {
    method: 'POST',
  });
}

export async function recordPromise(id: number, promisedDate: string): Promise<{
  status: string;
  action_id: number;
  promised_payment_date: string;
}> {
  return request(`/actions/${id}/promise`, {
    method: 'POST',
    body: JSON.stringify({ promised_date: promisedDate }),
  });
}
