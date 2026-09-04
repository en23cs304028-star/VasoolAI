import React from 'react';
import { ShieldCheck, Lock, Clock, AlertTriangle } from 'lucide-react';

export const GuardrailsPanel: React.FC = () => {
  const guardrails = [
    {
      icon: <ShieldCheck className="w-4 h-4 text-primary" />,
      title: 'Tier Execution Cap',
      rule: 'Max 1 message per tier per invoice',
      rationale: 'Prevents repetitive spamming within the same escalation severity.',
    },
    {
      icon: <Lock className="w-4 h-4 text-[#B54708]" />,
      title: 'Buyer Volume Limit',
      rule: 'Max 4 messages per buyer / rolling 30 days',
      rationale: 'Protects long-term supplier relationship from harassment claims.',
    },
    {
      icon: <Clock className="w-4 h-4 text-ink-soft" />,
      title: 'Cooldown Interval',
      rule: '5-day minimum cooldown between touches',
      rationale: 'Allows reasonable window for commercial dispute or settlement.',
    },
    {
      icon: <AlertTriangle className="w-4 h-4 text-[#B42318]" />,
      title: 'Statutory Notice Approval Gate',
      rule: 'Mandatory human approval required',
      rationale: 'Legal notice citations must be verified before external delivery.',
    },
  ];

  return (
    <div className="bg-surface border border-border rounded-lg p-5 shadow-card">
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-border">
        <div>
          <h3 className="text-sm font-semibold text-ink">Recovery Guardrails</h3>
          <p className="text-xs text-ink-soft">Deterministic safety rules enforced by decision engine</p>
        </div>
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] bg-surface-raised border border-border text-ink-soft font-mono">
          LOCKED
        </span>
      </div>

      <div className="space-y-4">
        {guardrails.map((g, idx) => (
          <div key={idx} className="flex items-start gap-3 text-xs">
            <div className="p-1.5 rounded bg-surface-raised border border-border shrink-0 mt-0.5">
              {g.icon}
            </div>
            <div>
              <div className="font-semibold text-ink">{g.title}</div>
              <div className="font-mono text-[11px] text-ink font-medium mt-0.5">
                {g.rule}
              </div>
              <div className="text-ink-soft text-[11px] mt-0.5 leading-relaxed">
                {g.rationale}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-5 pt-3 border-t border-border-soft text-[11px] text-ink-faint leading-relaxed">
        Per PRD §5: Stopping rules are hard-coded in the deterministic core and cannot be bypassed or configured via API in this build.
      </div>
    </div>
  );
};
