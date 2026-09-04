import React from 'react';
import { RiskTier } from '../types/models';

interface TierPillProps {
  tier: RiskTier | string;
  className?: string;
}

export const TierPill: React.FC<TierPillProps> = ({ tier, className = '' }) => {
  const normalized = (tier || 'unscored').toLowerCase();

  let dotColor = 'bg-ink-faint';
  let bgColor = 'bg-surface-raised border-border';
  let textColor = 'text-ink-soft';
  let label = 'Unscored';

  if (normalized === 'low') {
    dotColor = 'bg-[#16794E]';
    bgColor = 'bg-[#E7F6EE] border-[#16794E]/20';
    textColor = 'text-[#16794E]';
    label = 'Low Risk';
  } else if (normalized === 'medium') {
    dotColor = 'bg-[#B54708]';
    bgColor = 'bg-[#FFF6ED] border-[#B54708]/20';
    textColor = 'text-[#B54708]';
    label = 'Medium Risk';
  } else if (normalized === 'high') {
    dotColor = 'bg-[#B42318]';
    bgColor = 'bg-[#FEF3F2] border-[#B42318]/20';
    textColor = 'text-[#B42318]';
    label = 'High Risk';
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${bgColor} ${textColor} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
      <span>{label}</span>
    </span>
  );
};
