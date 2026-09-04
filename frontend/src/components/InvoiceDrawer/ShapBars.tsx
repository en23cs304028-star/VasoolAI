import React from 'react';

interface ShapBarsProps {
  shapJson: string | null;
}

interface FeatureItem {
  name: string;
  value: number;
}

export const ShapBars: React.FC<ShapBarsProps> = ({ shapJson }) => {
  if (!shapJson) {
    return (
      <div className="text-xs text-ink-faint italic py-2">
        No SHAP attribution calculated for this score.
      </div>
    );
  }

  let features: FeatureItem[] = [];
  try {
    const parsed = JSON.parse(shapJson);
    if (Array.isArray(parsed)) {
      features = parsed.map((item: any) => {
        if (typeof item === 'object' && item !== null) {
          const name = item.feature || item.name || Object.keys(item)[0] || 'Feature';
          const val = typeof item.importance === 'number' ? item.importance : (typeof item.value === 'number' ? item.value : (typeof item[name] === 'number' ? item[name] : 0));
          return { name, value: val };
        }
        return { name: String(item), value: 0 };
      });
    } else if (typeof parsed === 'object') {
      features = Object.entries(parsed).map(([name, val]) => ({
        name,
        value: typeof val === 'number' ? val : 0,
      }));
    }
  } catch {
    return (
      <div className="text-xs text-ink-faint italic py-2">
        Attribution data unavailable.
      </div>
    );
  }

  // Pick top 3 features by absolute impact or value
  const sorted = [...features]
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, 3);

  if (sorted.length === 0) {
    return <div className="text-xs text-ink-faint italic py-2">No key drivers recorded.</div>;
  }

  const maxVal = Math.max(...sorted.map((f) => Math.abs(f.value)), 0.01);

  return (
    <div className="space-y-2 pt-1">
      {sorted.map((item, idx) => {
        const pct = Math.min(100, Math.round((Math.abs(item.value) / maxVal) * 100));
        const isPositive = item.value >= 0;

        return (
          <div key={idx} className="space-y-1">
            <div className="flex justify-between items-center text-xs">
              <span className="text-ink font-medium truncate max-w-[240px]">
                {item.name.replace(/_/g, ' ')}
              </span>
              <span className="font-mono text-[11px] text-ink-soft">
                {isPositive ? `+${item.value.toFixed(3)}` : item.value.toFixed(3)}
              </span>
            </div>
            <div className="w-full bg-surface-raised h-1.5 rounded-full overflow-hidden border border-border-soft">
              <div
                className={`h-full rounded-full ${
                  isPositive ? 'bg-high' : 'bg-primary'
                }`}
                style={{ width: `${Math.max(pct, 6)}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};
