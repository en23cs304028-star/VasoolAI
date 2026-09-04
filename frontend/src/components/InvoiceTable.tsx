import React from 'react';
import { Invoice } from '../types/models';
import { TierPill } from './TierPill';

interface InvoiceTableProps {
  invoices: Invoice[];
  selectedId?: number | null;
  onSelectRow: (invoice: Invoice) => void;
  onClearFilters?: () => void;
  isLoading?: boolean;
}

export const InvoiceTable: React.FC<InvoiceTableProps> = ({
  invoices,
  selectedId,
  onSelectRow,
  onClearFilters,
  isLoading,
}) => {
  const formatINR = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
    }).format(val);
  };

  const renderActionBadge = (status: string | null) => {
    if (!status) {
      return <span className="text-ink-faint font-mono text-xs">—</span>;
    }
    let colorClasses = 'bg-surface-raised text-ink-soft border-border';
    if (status === 'Pending approval') {
      colorClasses = 'bg-medium-bg text-medium border-medium/20 font-medium';
    } else if (status === 'Sent') {
      colorClasses = 'bg-low-bg text-low border-low/20 font-medium';
    } else if (status === 'Queued') {
      colorClasses = 'bg-primary-soft text-primary border-primary/20 font-medium';
    }

    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] border ${colorClasses}`}
      >
        {status}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="py-20 text-center text-sm text-ink-soft bg-surface">
        <div className="inline-block w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin mb-2" />
        <p>Loading invoice records...</p>
      </div>
    );
  }

  if (invoices.length === 0) {
    return (
      <div className="py-20 text-center text-sm text-ink-soft bg-surface">
        <div className="max-w-xs mx-auto space-y-3">
          <p className="font-medium text-ink">No invoices match these filters</p>
          <p className="text-xs text-ink-soft">
            Try adjusting your tier, status, or overdue filter parameters.
          </p>
          {onClearFilters && (
            <button
              onClick={onClearFilters}
              className="px-3 py-1.5 text-xs font-medium bg-surface-raised border border-border rounded-md hover:bg-surface text-ink transition-colors"
            >
              Clear filters
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto bg-surface">
      <table className="w-full text-left border-collapse text-xs">
        <thead>
          <tr className="border-b border-border bg-surface-raised/60 text-ink-soft uppercase tracking-wider font-semibold text-[11px]">
            <th className="py-3 px-4 sm:px-6">Buyer</th>
            <th className="py-3 px-4">Invoice #</th>
            <th className="py-3 px-4 text-right">Principal</th>
            <th className="py-3 px-4 text-right">Days Overdue</th>
            <th className="py-3 px-4">Risk Tier</th>
            <th className="py-3 px-4">Action Status</th>
            <th className="py-3 px-4 sm:px-6 text-right">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {invoices.map((inv) => {
            const isSelected = selectedId === inv.id;
            return (
              <tr
                key={inv.id}
                onClick={() => onSelectRow(inv)}
                className={`cursor-pointer transition-colors group ${
                  isSelected
                    ? 'bg-primary-soft'
                    : 'hover:bg-surface-raised'
                }`}
              >
                <td className="py-3 px-4 sm:px-6 font-medium text-ink">
                  <div>{inv.buyer_name}</div>
                  <div className="text-[11px] text-ink-faint font-mono mt-0.5">
                    ID #{inv.buyer_id}
                  </div>
                </td>
                <td className="py-3 px-4 font-mono font-medium text-ink">
                  {inv.invoice_number}
                </td>
                <td className="py-3 px-4 text-right font-mono font-medium text-ink">
                  {formatINR(inv.principal_amount)}
                </td>
                <td className="py-3 px-4 text-right font-mono">
                  {inv.days_overdue > 0 ? (
                    <span className="text-high font-medium">
                      +{inv.days_overdue}d
                    </span>
                  ) : (
                    <span className="text-ink-faint">Current</span>
                  )}
                </td>
                <td className="py-3 px-4">
                  <TierPill tier={inv.risk_tier} />
                </td>
                <td className="py-3 px-4">
                  {renderActionBadge(inv.action_status)}
                </td>
                <td className="py-3 px-4 sm:px-6 text-right text-primary font-medium group-hover:underline">
                  Review &rarr;
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
