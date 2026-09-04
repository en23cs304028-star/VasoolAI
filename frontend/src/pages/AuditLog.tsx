import React, { useEffect, useState } from 'react';
import { getAuditLog } from '../api/auditLog';
import { AuditLogEntry } from '../types/models';
import { GuardrailsPanel } from '../components/GuardrailsPanel';
import { RefreshCw, Filter, AlertOctagon } from 'lucide-react';

export const AuditLogPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [entityFilter, setEntityFilter] = useState<'all' | 'invoice' | 'buyer' | 'action'>('all');
  const [onlyBlocked, setOnlyBlocked] = useState(false);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = entityFilter !== 'all' ? { entity_type: entityFilter } : undefined;
      const data = await getAuditLog(params);
      setLogs(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch audit log entries');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [entityFilter]);

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

  const filteredLogs = onlyBlocked
    ? logs.filter((l) => l.event === 'stopping_rule_blocked')
    : logs;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-ink">System Audit Trail</h1>
          <p className="text-xs text-ink-soft mt-0.5">
            Immutable log of state transitions, model score runs, message dispatches, and blocked stopping rules.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchLogs}
            disabled={loading}
            className="px-3 py-1.5 text-xs font-medium bg-surface border border-border rounded-md text-ink hover:bg-surface-raised transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-high-bg border border-high/30 rounded-md text-xs text-high">
          {error}
        </div>
      )}

      {/* Main Grid: Audit Log Table (left 2/3) + Guardrails Panel (right 1/3) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <div className="lg:col-span-2 space-y-3">
          {/* Filter Bar */}
          <div className="flex flex-wrap items-center justify-between gap-2 p-3 bg-surface border border-border rounded-lg shadow-card">
            <div className="flex items-center gap-1">
              <span className="text-xs text-ink-faint mr-1 flex items-center gap-1">
                <Filter className="w-3 h-3" /> Entity:
              </span>
              {(['all', 'invoice', 'buyer', 'action'] as const).map((type) => (
                <button
                  key={type}
                  onClick={() => setEntityFilter(type)}
                  className={`px-2.5 py-1 text-xs rounded font-medium transition-all capitalize ${
                    entityFilter === type
                      ? 'bg-surface-raised text-ink border border-border shadow-xs'
                      : 'text-ink-soft hover:text-ink'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>

            {/* Quick toggle for stopping_rule_blocked */}
            <button
              onClick={() => setOnlyBlocked(!onlyBlocked)}
              className={`inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded-full border transition-all ${
                onlyBlocked
                  ? 'bg-high-bg text-high border-high/30 font-medium'
                  : 'bg-surface-raised text-ink-soft border-border hover:border-ink-faint'
              }`}
            >
              <AlertOctagon className="w-3 h-3 text-high" />
              Violations Only
            </button>
          </div>

          {/* Table */}
          <div className="bg-surface border border-border rounded-lg shadow-card overflow-hidden">
            {loading ? (
              <div className="py-20 text-center text-sm text-ink-soft">
                <div className="inline-block w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin mb-2" />
                <p>Loading audit entries...</p>
              </div>
            ) : filteredLogs.length === 0 ? (
              <div className="py-20 text-center text-sm text-ink-soft">
                No audit log records match the current entity filter.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-border bg-surface-raised/60 text-ink-soft uppercase tracking-wider font-semibold text-[11px]">
                      <th className="py-3 px-4 sm:px-6">Timestamp</th>
                      <th className="py-3 px-4">Entity</th>
                      <th className="py-3 px-4">Event</th>
                      <th className="py-3 px-4 sm:px-6">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {filteredLogs.map((log) => {
                      const isBlocked = log.event === 'stopping_rule_blocked';

                      return (
                        <tr
                          key={log.id}
                          className={`transition-colors ${
                            isBlocked
                              ? 'bg-high-bg hover:bg-[#FEE4E2]'
                              : 'hover:bg-surface-raised'
                          }`}
                        >
                          <td className="py-3 px-4 sm:px-6 font-mono text-ink-soft whitespace-nowrap">
                            {formatTimestamp(log.created_at)}
                          </td>
                          <td className="py-3 px-4 font-mono">
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] bg-surface border border-border text-ink capitalize">
                              {log.entity_type} #{log.entity_id}
                            </span>
                          </td>
                          <td className="py-3 px-4 font-mono font-medium">
                            <span
                              className={`inline-flex items-center gap-1 ${
                                isBlocked ? 'text-high font-semibold' : 'text-ink'
                              }`}
                            >
                              {isBlocked && <AlertOctagon className="w-3.5 h-3.5 text-high" />}
                              {log.event}
                            </span>
                          </td>
                          <td className="py-3 px-4 sm:px-6 text-ink leading-relaxed font-sans max-w-md break-words">
                            {log.details}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Right 1/3: Hard-coded Recovery Guardrails Panel */}
        <div className="lg:col-span-1">
          <GuardrailsPanel />
        </div>
      </div>
    </div>
  );
};
