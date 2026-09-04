import React, { useEffect, useState } from 'react';
import { getAuditLog } from '../../api/auditLog';
import { AuditLogEntry } from '../../types/models';
import { AlertOctagon, CheckCircle, Send, FileText, ShieldAlert } from 'lucide-react';

interface TimelineTabProps {
  invoiceId: number;
  buyerId: number;
}

export const TimelineTab: React.FC<TimelineTabProps> = ({ invoiceId, buyerId }) => {
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function fetchTimeline() {
      try {
        setLoading(true);
        // Fetch audit logs for invoice and buyer
        const [invoiceLogs, buyerLogs] = await Promise.all([
          getAuditLog({ entity_id: invoiceId }),
          getAuditLog({ entity_id: buyerId }),
        ]);

        // Merge, de-duplicate by id, and sort chronologically (oldest to newest for timeline)
        const combined = [...invoiceLogs, ...buyerLogs];
        const uniqueMap = new Map<number, AuditLogEntry>();
        combined.forEach((item) => uniqueMap.set(item.id, item));
        const sorted = Array.from(uniqueMap.values()).sort(
          (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        );

        if (isMounted) {
          setEntries(sorted);
        }
      } catch (err) {
        console.error('Failed to load timeline audit log', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    fetchTimeline();
    return () => {
      isMounted = false;
    };
  }, [invoiceId, buyerId]);

  const formatTimestamp = (iso: string) => {
    try {
      const d = new Date(iso);
      return `${d.toLocaleDateString('en-IN', {
        month: 'short',
        day: '2-digit',
      })} ${d.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      })}`;
    } catch {
      return iso;
    }
  };

  const getEventIcon = (event: string) => {
    if (event.includes('stopping_rule_blocked')) {
      return <AlertOctagon className="w-3.5 h-3.5 text-high" />;
    }
    if (event.includes('sent')) {
      return <Send className="w-3.5 h-3.5 text-low" />;
    }
    if (event.includes('approved')) {
      return <CheckCircle className="w-3.5 h-3.5 text-primary" />;
    }
    if (event.includes('scored')) {
      return <ShieldAlert className="w-3.5 h-3.5 text-[#B54708]" />;
    }
    return <FileText className="w-3.5 h-3.5 text-ink-soft" />;
  };

  if (loading) {
    return (
      <div className="py-12 text-center text-xs text-ink-soft">
        <div className="inline-block w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin mb-2" />
        <p>Loading lifecycle audit trail...</p>
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className="py-12 text-center text-xs text-ink-faint">
        No audit log events recorded for this invoice yet.
      </div>
    );
  }

  return (
    <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-px before:bg-border">
      {entries.map((item) => {
        const isBlocked = item.event === 'stopping_rule_blocked';

        return (
          <div key={item.id} className="relative group text-xs">
            {/* Timeline bullet dot */}
            <div
              className={`absolute -left-6 top-0.5 w-5 h-5 rounded-full border flex items-center justify-center ${
                isBlocked
                  ? 'bg-high-bg border-high/40'
                  : 'bg-surface border-border'
              }`}
            >
              {getEventIcon(item.event)}
            </div>

            {/* Event content */}
            <div
              className={`p-3 rounded-lg border transition-all ${
                isBlocked
                  ? 'bg-high-bg border-high/30'
                  : 'bg-surface border-border shadow-card'
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-1">
                <span
                  className={`font-mono text-[11px] font-semibold ${
                    isBlocked ? 'text-high' : 'text-ink'
                  }`}
                >
                  {item.event}
                </span>
                <span className="font-mono text-[11px] text-ink-faint">
                  {formatTimestamp(item.created_at)}
                </span>
              </div>

              <div className="text-ink-soft text-xs leading-relaxed font-sans mt-0.5">
                {item.details || 'No additional details logged'}
              </div>

              <div className="text-[10px] text-ink-faint font-mono mt-2 flex items-center gap-2">
                <span>Entity: {item.entity_type}</span>
                <span>&bull;</span>
                <span>ID #{item.entity_id}</span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
