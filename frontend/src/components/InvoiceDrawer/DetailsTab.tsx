import React, { useState } from 'react';
import { InvoiceDetail, Action } from '../../types/models';
import { TierPill } from '../TierPill';
import { ShapBars } from './ShapBars';
import { approveAction, sendAction, recordPromise } from '../../api/actions';
import { planAction, scoreInvoice } from '../../api/invoices';
import { CheckCircle2, AlertCircle, Send, ShieldAlert, Calendar, ExternalLink, Copy, Check } from 'lucide-react';

interface DetailsTabProps {
  invoice: InvoiceDetail;
  onRefresh: () => void;
}

export const DetailsTab: React.FC<DetailsTabProps> = ({ invoice, onRefresh }) => {
  const [isApproving, setIsApproving] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isPlanning, setIsPlanning] = useState(false);
  const [isScoring, setIsScoring] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);

  // Promise to pay states
  const [showPromiseInput, setShowPromiseInput] = useState(false);
  const [promiseDate, setPromiseDate] = useState(
    new Date(Date.now() + 7 * 86400000).toISOString().split('T')[0]
  );
  const [isSavingPromise, setIsSavingPromise] = useState(false);

  const formatINR = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
    }).format(val);
  };

  // Find latest action
  const latestAction: Action | undefined = invoice.actions && invoice.actions.length > 0 ? invoice.actions[0] : undefined;

  // Determine promise-to-pay state
  const activePromiseDate = invoice.promised_payment_date || (latestAction && latestAction.promised_payment_date);
  const todayStr = new Date().toISOString().split('T')[0];
  const isPromiseBroken =
    activePromiseDate &&
    todayStr > activePromiseDate &&
    invoice.status !== 'paid';
  const isPromiseKept = activePromiseDate && invoice.status === 'paid';

  const handleScore = async () => {
    try {
      setIsScoring(true);
      setActionError(null);
      await scoreInvoice(invoice.id);
      onRefresh();
    } catch (err: any) {
      setActionError(err.message || 'Failed to calculate risk score');
    } finally {
      setIsScoring(false);
    }
  };

  const handlePlanAction = async () => {
    try {
      setIsPlanning(true);
      setActionError(null);
      const res = await planAction(invoice.id);
      if (res.status === 'skipped') {
        setActionError(`Engine notice: ${res.reason || 'No action planned'}`);
      }
      onRefresh();
    } catch (err: any) {
      setActionError(err.message || 'Failed to plan recovery action');
    } finally {
      setIsPlanning(false);
    }
  };

  const handleApprove = async () => {
    if (!latestAction) return;
    try {
      setIsApproving(true);
      setActionError(null);
      await approveAction(latestAction.id, 'Finance Operations');
      onRefresh();
    } catch (err: any) {
      setActionError(err.message || 'Failed to approve action');
    } finally {
      setIsApproving(false);
    }
  };

  const handleSend = async () => {
    if (!latestAction) return;
    try {
      setIsSending(true);
      setActionError(null);
      await sendAction(latestAction.id);
      onRefresh();
    } catch (err: any) {
      setActionError(err.message || 'Failed to send message via channel adapter');
    } finally {
      setIsSending(false);
    }
  };

  const handleSavePromise = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!latestAction) {
      setActionError('Plan an escalation action first before attaching a promise date.');
      return;
    }
    try {
      setIsSavingPromise(true);
      setActionError(null);
      await recordPromise(latestAction.id, promiseDate);
      setShowPromiseInput(false);
      onRefresh();
    } catch (err: any) {
      setActionError(err.message || 'Failed to record promise-to-pay date');
    } finally {
      setIsSavingPromise(false);
    }
  };

  const requiresApproval = latestAction?.requires_approval ?? false;
  const isApproved = latestAction?.approved ?? false;
  const isSent = latestAction?.sent ?? false;

  return (
    <div className="space-y-6">
      {/* 1. Stat row: Days overdue · Risk tier (pill) · Interest owed · Model version tag */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 bg-surface-raised p-3.5 rounded-lg border border-border">
        <div>
          <div className="text-[11px] text-ink-soft uppercase font-medium">Days Overdue</div>
          <div className="font-mono text-base font-semibold text-ink mt-0.5">
            {invoice.days_overdue > 0 ? (
              <span className="text-high">+{invoice.days_overdue}d</span>
            ) : (
              <span className="text-low">0d (Current)</span>
            )}
          </div>
        </div>

        <div>
          <div className="text-[11px] text-ink-soft uppercase font-medium">Risk Tier</div>
          <div className="mt-1">
            <TierPill tier={invoice.risk_tier} />
          </div>
        </div>

        <div>
          <div className="text-[11px] text-ink-soft uppercase font-medium">Interest Owed</div>
          <div
            className={`font-mono text-base font-semibold mt-0.5 ${
              invoice.interest_owed > 0 ? 'text-high' : 'text-ink'
            }`}
          >
            {formatINR(invoice.interest_owed)}
          </div>
        </div>

        <div>
          <div className="text-[11px] text-ink-soft uppercase font-medium">Model Version</div>
          <div className="mt-1">
            <span className="font-mono text-xs px-2 py-0.5 rounded bg-surface border border-border text-ink-soft inline-block truncate max-w-full">
              {invoice.model_version || 'v1.0.0-prod'}
            </span>
          </div>
        </div>
      </div>

      {/* 2. "Why this score" SHAP Attribution */}
      <div className="border border-border rounded-lg p-4 bg-surface shadow-card">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-soft">
            Why this score (SHAP Attribution)
          </h4>
          {invoice.risk_probability !== null && invoice.risk_probability !== undefined && (
            <span className="font-mono text-xs text-ink-soft">
              Risk Prob: <strong className="text-ink">{(invoice.risk_probability * 100).toFixed(1)}%</strong>
            </span>
          )}
        </div>
        {invoice.risk_tier === 'unscored' ? (
          <div className="py-2 text-center">
            <p className="text-xs text-ink-soft mb-2">This invoice has not been scored by the XGBoost risk model yet.</p>
            <button
              onClick={handleScore}
              disabled={isScoring}
              className="px-3 py-1.5 text-xs font-medium bg-primary text-white rounded-md hover:bg-primary-hover disabled:opacity-50"
            >
              {isScoring ? 'Scoring...' : 'Run Risk Model & SHAP'}
            </button>
          </div>
        ) : (
          <ShapBars shapJson={invoice.shap_top_features} />
        )}
      </div>

      {/* 3. Drafted Recovery Action */}
      <div className="border border-border rounded-lg p-4 bg-surface shadow-card space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-soft">
              Recovery Action
            </h4>
            {latestAction && (
              <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-surface-raised border border-border text-ink capitalize">
                {latestAction.escalation_tier.replace('_', ' ')} &middot; {latestAction.channel}
              </span>
            )}
          </div>
          {isSent && (
            <span className="inline-flex items-center gap-1 text-xs text-low font-medium bg-low-bg px-2 py-0.5 rounded border border-low/20">
              <CheckCircle2 className="w-3.5 h-3.5" /> Sent
            </span>
          )}
        </div>

        {latestAction ? (
          <>
            <div className="p-3 bg-surface-raised rounded-md border border-border text-xs leading-relaxed text-ink font-sans whitespace-pre-wrap selection:bg-primary-soft">
              {latestAction.drafted_message}
            </div>

            {/* Dedicated Razorpay Payment Link Banner */}
            {(latestAction.payment_link_url || latestAction.drafted_message.match(/https?:\/\/[^\s]+/)?.[0]) && (() => {
              const paymentUrl = latestAction.payment_link_url || latestAction.drafted_message.match(/https?:\/\/[^\s]+/)?.[0]!;
              return (
                <div className="p-3 bg-surface-raised rounded-md border border-primary/25 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 shadow-sm">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-primary shrink-0">
                      Razorpay Link:
                    </span>
                    <a
                      href={paymentUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-primary font-mono truncate hover:underline"
                      title={paymentUrl}
                    >
                      {paymentUrl}
                    </a>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(paymentUrl);
                        setCopiedLink(true);
                        setTimeout(() => setCopiedLink(false), 2000);
                      }}
                      className="px-2.5 py-1 text-[11px] font-medium text-ink-soft hover:text-ink bg-surface border border-border rounded flex items-center gap-1 transition-colors"
                    >
                      {copiedLink ? <Check className="w-3 h-3 text-low" /> : <Copy className="w-3 h-3" />}
                      {copiedLink ? 'Copied' : 'Copy'}
                    </button>
                    <a
                      href={paymentUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="px-2.5 py-1 text-[11px] font-medium bg-primary text-white hover:bg-primary-hover rounded flex items-center gap-1 transition-colors shadow-sm"
                    >
                      Pay Now <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              );
            })()}

            {/* In-product pipeline caption */}
            <p className="text-[11px] text-ink-faint italic">
              Risk detection &rarr; root-cause explanation &rarr; recovery action &mdash; one pipeline, shown end to end.
            </p>
          </>
        ) : (
          <div className="py-6 text-center text-xs text-ink-soft space-y-3">
            <p>No action has been queued for this invoice yet.</p>
            <button
              onClick={handlePlanAction}
              disabled={isPlanning}
              className="px-3.5 py-1.5 text-xs font-medium bg-primary text-white rounded-md hover:bg-primary-hover disabled:opacity-50"
            >
              {isPlanning ? 'Planning Action...' : 'Draft Recovery Action with Nemotron LLM'}
            </button>
          </div>
        )}
      </div>

      {/* 4. Promise to Pay Tracker (FEATURE_LEDGER specification) */}
      <div className="border border-border rounded-lg p-4 bg-surface shadow-card space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-soft flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5" /> Promise-to-Pay Tracker
          </h4>
          {!showPromiseInput && (
            <button
              onClick={() => setShowPromiseInput(true)}
              className="text-xs text-primary font-medium hover:underline"
            >
              {activePromiseDate ? 'Update promise' : 'Log a promise'}
            </button>
          )}
        </div>

        {activePromiseDate ? (
          <div className="flex items-center justify-between p-2.5 bg-surface-raised rounded border border-border text-xs">
            <div className="flex items-center gap-2">
              <span className="text-ink">
                Buyer promised payment by <strong className="font-mono text-ink">{activePromiseDate}</strong>
              </span>
              {isPromiseBroken && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] bg-high-bg text-high border border-high/20 font-medium">
                  Broken promise
                </span>
              )}
              {isPromiseKept && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] bg-low-bg text-low border border-low/20 font-medium">
                  Promise Kept
                </span>
              )}
            </div>
          </div>
        ) : !showPromiseInput ? (
          <div className="text-xs text-ink-faint italic">
            No stated promise-to-pay date recorded for this invoice yet.
          </div>
        ) : null}

        {showPromiseInput && (
          <form onSubmit={handleSavePromise} className="p-3 bg-surface-raised rounded border border-border space-y-3">
            <label className="block text-xs font-medium text-ink">
              Enter buyer promised payment date:
            </label>
            <div className="flex items-center gap-2">
              <input
                type="date"
                required
                value={promiseDate}
                onChange={(e) => setPromiseDate(e.target.value)}
                className="px-2.5 py-1.5 text-xs font-mono border border-border rounded bg-surface text-ink focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <button
                type="submit"
                disabled={isSavingPromise}
                className="px-3 py-1.5 text-xs font-medium bg-primary text-white rounded hover:bg-primary-hover disabled:opacity-50"
              >
                {isSavingPromise ? 'Saving...' : 'Save Promise'}
              </button>
              <button
                type="button"
                onClick={() => setShowPromiseInput(false)}
                className="px-2 py-1.5 text-xs text-ink-soft hover:text-ink"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Error alert if any */}
      {actionError && (
        <div className="p-3 bg-high-bg border border-high/30 rounded text-xs text-high flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{actionError}</span>
        </div>
      )}

      {/* 5. Approve & Send Action Footer Gate */}
      {latestAction && (
        <div className="p-4 bg-surface border border-border rounded-lg shadow-card space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-xs">
              <div className="font-semibold text-ink">Action Dispatch Controls</div>
              <div className="text-ink-soft text-[11px]">
                {requiresApproval
                  ? 'Statutory notices require approval before sending.'
                  : 'Automated channel delivery ready.'}
              </div>
            </div>

            <div className="flex items-center gap-2">
              {requiresApproval && (
                <button
                  onClick={handleApprove}
                  disabled={isApproved || isApproving || isSent}
                  className={`px-3 py-1.5 text-xs font-medium rounded transition-all flex items-center gap-1.5 ${
                    isApproved
                      ? 'bg-low-bg text-low border border-low/20 cursor-default'
                      : 'bg-primary text-white hover:bg-primary-hover shadow-sm disabled:opacity-50'
                  }`}
                >
                  <ShieldAlert className="w-3.5 h-3.5" />
                  {isApproving ? 'Approving...' : isApproved ? 'Notice Approved' : 'Approve Notice'}
                </button>
              )}

              <button
                onClick={handleSend}
                disabled={isSent || isSending || (requiresApproval && !isApproved)}
                title={
                  requiresApproval && !isApproved
                    ? 'Statutory notices require approval before sending.'
                    : 'Dispatch message via real channel adapter'
                }
                className={`px-3 py-1.5 text-xs font-medium rounded transition-all flex items-center gap-1.5 ${
                  isSent
                    ? 'bg-surface-raised text-ink-soft border border-border cursor-default'
                    : requiresApproval && !isApproved
                    ? 'bg-surface-raised text-ink-faint border border-border cursor-not-allowed opacity-60'
                    : 'bg-primary text-white hover:bg-primary-hover shadow-sm'
                }`}
              >
                <Send className="w-3.5 h-3.5" />
                {isSending ? 'Sending...' : isSent ? 'Sent' : 'Send'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Legal disclaimer */}
      <div className="text-[11px] text-ink-faint text-center leading-relaxed">
        This message cites statutory provisions for information purposes and is not legal advice.
      </div>
    </div>
  );
};
