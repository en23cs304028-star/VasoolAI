import React from 'react';
import { RiskTier, InvoiceStatus } from '../types/models';

export interface FilterState {
  tier: RiskTier | 'all';
  statuses: InvoiceStatus[];
  overdueOnly: boolean;
}

interface FilterChipsProps {
  filters: FilterState;
  onChange: (updated: FilterState) => void;
  onReset?: () => void;
  hasActiveFilters?: boolean;
}

export const FilterChips: React.FC<FilterChipsProps> = ({
  filters,
  onChange,
  onReset,
  hasActiveFilters,
}) => {
  const tiers: { id: RiskTier | 'all'; label: string }[] = [
    { id: 'all', label: 'All Tiers' },
    { id: 'high', label: 'High Risk' },
    { id: 'medium', label: 'Medium Risk' },
    { id: 'low', label: 'Low Risk' },
  ];

  const statuses: { id: InvoiceStatus; label: string }[] = [
    { id: 'open', label: 'Open' },
    { id: 'partially_paid', label: 'Partially Paid' },
    { id: 'paid', label: 'Paid' },
  ];

  const handleTierSelect = (tier: RiskTier | 'all') => {
    onChange({ ...filters, tier });
  };

  const handleStatusToggle = (status: InvoiceStatus) => {
    const exists = filters.statuses.includes(status);
    let newStatuses: InvoiceStatus[];
    if (exists) {
      newStatuses = filters.statuses.filter((s) => s !== status);
    } else {
      newStatuses = [...filters.statuses, status];
    }
    onChange({ ...filters, statuses: newStatuses });
  };

  const handleOverdueToggle = () => {
    onChange({ ...filters, overdueOnly: !filters.overdueOnly });
  };

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 py-3 border-b border-border bg-surface px-4 sm:px-6">
      <div className="flex flex-wrap items-center gap-3">
        {/* Tier single-select */}
        <div className="flex items-center gap-1 bg-surface-raised p-1 rounded-md border border-border">
          {tiers.map((t) => {
            const active = filters.tier === t.id;
            return (
              <button
                key={t.id}
                onClick={() => handleTierSelect(t.id)}
                className={`px-2.5 py-1 text-xs font-medium rounded transition-all ${
                  active
                    ? 'bg-surface text-ink shadow-sm border border-border/80'
                    : 'text-ink-soft hover:text-ink hover:bg-surface/50'
                }`}
              >
                {t.label}
              </button>
            );
          })}
        </div>

        <div className="h-4 w-px bg-border hidden sm:block" />

        {/* Status multi-select chips */}
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-ink-faint mr-0.5">Status:</span>
          {statuses.map((s) => {
            const active = filters.statuses.includes(s.id);
            return (
              <button
                key={s.id}
                onClick={() => handleStatusToggle(s.id)}
                className={`px-2.5 py-1 text-xs rounded-full border transition-all ${
                  active
                    ? 'bg-primary-soft text-primary border-primary/30 font-medium'
                    : 'bg-surface-raised text-ink-soft border-border hover:border-ink-faint'
                }`}
              >
                {s.label}
              </button>
            );
          })}
        </div>

        <div className="h-4 w-px bg-border hidden sm:block" />

        {/* Overdue-only toggle button */}
        <button
          onClick={handleOverdueToggle}
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-full border transition-all ${
            filters.overdueOnly
              ? 'bg-high-bg text-high border-high/30 font-medium'
              : 'bg-surface-raised text-ink-soft border-border hover:border-ink-faint'
          }`}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              filters.overdueOnly ? 'bg-high' : 'bg-ink-faint'
            }`}
          />
          Overdue Only
        </button>
      </div>

      {/* Clear filters button */}
      {hasActiveFilters && onReset && (
        <button
          onClick={onReset}
          className="text-xs text-ink-soft hover:text-ink underline decoration-dotted font-medium transition-colors"
        >
          Clear filters
        </button>
      )}
    </div>
  );
};
