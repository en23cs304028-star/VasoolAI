import React from 'react';

interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  badge?: string;
  badgeType?: 'default' | 'highlight' | 'warning' | 'synthetic';
  className?: string;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  subtitle,
  badge,
  badgeType = 'default',
  className = '',
}) => {
  let badgeClasses = 'bg-surface-raised text-ink-soft border-border';
  if (badgeType === 'synthetic') {
    badgeClasses = 'bg-primary-soft text-primary border-primary/20 font-medium';
  } else if (badgeType === 'warning') {
    badgeClasses = 'bg-high-bg text-high border-high/20 font-medium';
  } else if (badgeType === 'highlight') {
    badgeClasses = 'bg-low-bg text-low border-low/20 font-medium';
  }

  return (
    <div
      className={`bg-surface border border-border rounded-lg p-5 shadow-card transition-all ${className}`}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-xs font-medium uppercase tracking-wider text-ink-soft">
          {title}
        </span>
        {badge && (
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] border ${badgeClasses}`}
          >
            {badge}
          </span>
        )}
      </div>
      <div className="text-2xl font-semibold text-ink font-mono tracking-tight my-1">
        {value}
      </div>
      {subtitle && (
        <div className="text-xs text-ink-soft flex items-center gap-1.5 mt-1">
          {subtitle}
        </div>
      )}
    </div>
  );
};
