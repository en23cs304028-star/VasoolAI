import React, { useEffect, useState } from 'react';
import { getLatestBacktest, runBacktest } from '../api/backtest';
import { BacktestRun } from '../types/models';
import { Play, AlertTriangle } from 'lucide-react';

export const BacktestPage: React.FC = () => {
  const [backtest, setBacktest] = useState<BacktestRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBacktest = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getLatestBacktest();
      setBacktest(data);
    } catch (err: any) {
      setError(err.message || 'No backtest runs found yet.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBacktest();
  }, []);

  const handleRunBacktest = async () => {
    try {
      setRunning(true);
      setError(null);
      const newRun = await runBacktest();
      setBacktest(newRun);
    } catch (err: any) {
      setError(err.message || 'Failed to execute backtest simulation.');
    } finally {
      setRunning(false);
    }
  };

  const formatTimestamp = (iso: string) => {
    try {
      const d = new Date(iso);
      return `${d.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
      })} at ${d.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
      })}`;
    } catch {
      return iso;
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Mandatory Persistent Banner (exact phrasing per PRD §9 & Master Plan §6) */}
      <div className="p-4 bg-primary-soft border border-primary/20 rounded-lg flex items-start gap-3 shadow-card">
        <AlertTriangle className="w-5 h-5 text-primary shrink-0 mt-0.5" />
        <div className="text-xs leading-relaxed text-ink">
          <span className="font-semibold text-primary">
            Synthetic backtest &mdash; simulated on generated data, not real-world recovered money.
          </span>
          <p className="text-ink-soft mt-0.5">
            Evaluates VasoolAI&apos;s tiered escalation vs. naive baseline (messaging every invoice only at 45 days overdue) across ground-truth repayment outcomes.
          </p>
        </div>
      </div>

      {/* Page Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-ink">Evaluation &amp; Backtest Results</h1>
          <p className="text-xs text-ink-soft mt-0.5">
            Side-by-side benchmark comparing autonomous early intervention against standard recovery delay.
          </p>
        </div>

        <button
          onClick={handleRunBacktest}
          disabled={running}
          className="px-4 py-2 text-xs font-semibold bg-primary text-white hover:bg-primary-hover rounded-md shadow-sm transition-all flex items-center gap-2 disabled:opacity-50"
        >
          <Play className={`w-3.5 h-3.5 ${running ? 'animate-spin' : 'fill-white'}`} />
          {running ? 'Simulating Full Batch...' : 'Run New Backtest'}
        </button>
      </div>

      {error && (
        <div className="p-3 bg-high-bg border border-high/30 rounded-md text-xs text-high">
          {error}
        </div>
      )}

      {loading && !backtest ? (
        <div className="py-20 text-center text-sm text-ink-soft bg-surface border border-border rounded-lg shadow-card">
          <div className="inline-block w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mb-2" />
          <p>Loading latest simulation results...</p>
        </div>
      ) : backtest ? (
        <div className="space-y-6">
          {/* 2. Metric Compare Cards: Exact PRD §4 fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Metric 1: Recovery Days */}
            <div className="bg-surface border border-border rounded-lg p-6 shadow-card space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-ink">Days to Recovery / Advance Notice</h3>
                  <p className="text-xs text-ink-soft">Average days recovered before default</p>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-surface-raised border border-border text-ink-soft">
                  baseline vs agent
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4 pt-2">
                {/* Baseline Metric */}
                <div className="p-4 rounded-md bg-surface-raised border border-border">
                  <span className="text-[11px] uppercase tracking-wider text-ink-soft font-medium">
                    Naive Baseline
                  </span>
                  <div className="font-mono text-2xl font-semibold text-ink mt-1">
                    {backtest.baseline_metric_recovery_days.toFixed(1)}d
                  </div>
                  <div className="text-[11px] text-ink-faint mt-1">
                    Contact delayed to day 45
                  </div>
                </div>

                {/* Agent Metric */}
                <div className="p-4 rounded-md bg-low-bg border border-low/20">
                  <span className="text-[11px] uppercase tracking-wider text-low font-medium">
                    VasoolAI Agent
                  </span>
                  <div className="font-mono text-2xl font-semibold text-low mt-1">
                    +{backtest.agent_metric_recovery_days.toFixed(1)}d
                  </div>
                  <div className="text-[11px] text-low/80 mt-1 font-medium">
                    {(backtest.agent_metric_recovery_days - backtest.baseline_metric_recovery_days).toFixed(1)}d advance lift
                  </div>
                </div>
              </div>
            </div>

            {/* Metric 2: Recovery Rate */}
            <div className="bg-surface border border-border rounded-lg p-6 shadow-card space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-ink">Overall Recovery Rate</h3>
                  <p className="text-xs text-ink-soft">Share of late invoices settled within target window</p>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-surface-raised border border-border text-ink-soft">
                  target window
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4 pt-2">
                {/* Baseline Metric */}
                <div className="p-4 rounded-md bg-surface-raised border border-border">
                  <span className="text-[11px] uppercase tracking-wider text-ink-soft font-medium">
                    Naive Baseline
                  </span>
                  <div className="font-mono text-2xl font-semibold text-ink mt-1">
                    {(backtest.baseline_metric_recovery_rate * 100).toFixed(1)}%
                  </div>
                  <div className="text-[11px] text-ink-faint mt-1">
                    Single generic reminder
                  </div>
                </div>

                {/* Agent Metric */}
                <div className="p-4 rounded-md bg-low-bg border border-low/20">
                  <span className="text-[11px] uppercase tracking-wider text-low font-medium">
                    VasoolAI Agent
                  </span>
                  <div className="font-mono text-2xl font-semibold text-low mt-1">
                    {(backtest.agent_metric_recovery_rate * 100).toFixed(1)}%
                  </div>
                  <div className="text-[11px] text-low/80 mt-1 font-medium">
                    +{((backtest.agent_metric_recovery_rate - backtest.baseline_metric_recovery_rate) * 100).toFixed(1)}% recovery lift
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 3. Run Details Row */}
          <div className="bg-surface border border-border rounded-lg p-5 shadow-card">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-soft mb-3">
              Simulation Run Details
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
              <div>
                <span className="text-ink-faint text-[11px] block">Run ID</span>
                <span className="text-ink font-semibold">#{backtest.id}</span>
              </div>
              <div>
                <span className="text-ink-faint text-[11px] block">Run Timestamp</span>
                <span className="text-ink font-semibold">{formatTimestamp(backtest.run_at)}</span>
              </div>
              <div>
                <span className="text-ink-faint text-[11px] block">Evaluated Cohort</span>
                <span className="text-ink font-semibold">Overdue Invoices Cohort</span>
              </div>
              <div>
                <span className="text-ink-faint text-[11px] block">Simulation Seed</span>
                <span className="text-ink font-semibold">seed=42 (Deterministic)</span>
              </div>
            </div>

            {backtest.notes && (
              <div className="mt-4 pt-3 border-t border-border text-xs text-ink-soft leading-relaxed">
                <strong className="text-ink font-sans">Methodology Note: </strong>
                {backtest.notes}
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
};
