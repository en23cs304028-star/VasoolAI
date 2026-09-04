import { request } from './client';
import { BacktestRun } from '../types/models';

export async function getLatestBacktest(): Promise<BacktestRun> {
  return request<BacktestRun>('/backtest/latest');
}

export async function runBacktest(): Promise<BacktestRun> {
  return request<BacktestRun>('/backtest/run', {
    method: 'POST',
  });
}
