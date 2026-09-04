import React, { useEffect, useState, useMemo } from 'react';
import { getInvoices } from '../api/invoices';
import { Invoice } from '../types/models';
import { FilterChips, FilterState } from '../components/FilterChips';
import { InvoiceTable } from '../components/InvoiceTable';
import { InvoiceDrawer } from '../components/InvoiceDrawer';
import { RefreshCw, Search } from 'lucide-react';

export const InvoicesPage: React.FC = () => {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<number | null>(null);

  // Filters state per Master Plan §4
  const [filters, setFilters] = useState<FilterState>({
    tier: 'all',
    statuses: ['open', 'partially_paid'],
    overdueOnly: false,
  });

  const fetchInvoicesList = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getInvoices();
      setInvoices(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch invoices');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoicesList();
  }, []);

  const handleResetFilters = () => {
    setFilters({
      tier: 'all',
      statuses: ['open', 'partially_paid', 'paid'],
      overdueOnly: false,
    });
    setSearchQuery('');
  };

  const hasActiveFilters =
    filters.tier !== 'all' ||
    filters.statuses.length !== 3 ||
    filters.overdueOnly ||
    searchQuery.trim().length > 0;

  // Filter client-side for immediate responsiveness
  const filteredInvoices = useMemo(() => {
    return invoices.filter((inv) => {
      // Tier filter
      if (filters.tier !== 'all' && inv.risk_tier.toLowerCase() !== filters.tier.toLowerCase()) {
        return false;
      }

      // Status filter
      if (filters.statuses.length > 0 && !filters.statuses.includes(inv.status)) {
        return false;
      }

      // Overdue filter
      if (filters.overdueOnly && !inv.is_overdue) {
        return false;
      }

      // Search query filter (buyer name or invoice number)
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchesBuyer = inv.buyer_name.toLowerCase().includes(query);
        const matchesNum = inv.invoice_number.toLowerCase().includes(query);
        if (!matchesBuyer && !matchesNum) return false;
      }

      return true;
    });
  }, [invoices, filters, searchQuery]);

  return (
    <div className="space-y-4">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-ink">Receivables &amp; Invoices</h1>
          <p className="text-xs text-ink-soft mt-0.5">
            Real-time MSME receivables ledger with statutory interest and autonomous escalation queues.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Quick search */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-ink-faint" />
            <input
              type="text"
              placeholder="Search buyer or invoice #..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1.5 text-xs bg-surface border border-border rounded-md text-ink placeholder:text-ink-faint focus:outline-none focus:ring-1 focus:ring-primary w-56 font-sans"
            />
          </div>

          <button
            onClick={fetchInvoicesList}
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

      {/* Filter Row */}
      <div className="bg-surface border border-border rounded-lg shadow-card overflow-hidden">
        <FilterChips
          filters={filters}
          onChange={setFilters}
          onReset={handleResetFilters}
          hasActiveFilters={hasActiveFilters}
        />

        {/* Invoices Table */}
        <InvoiceTable
          invoices={filteredInvoices}
          selectedId={selectedInvoiceId}
          onSelectRow={(inv) => setSelectedInvoiceId(inv.id)}
          onClearFilters={handleResetFilters}
          isLoading={loading}
        />

        {/* Table footer with count */}
        {!loading && (
          <div className="py-2.5 px-6 border-t border-border bg-surface-raised/40 text-[11px] text-ink-soft flex items-center justify-between">
            <span>
              Showing <strong className="font-mono text-ink">{filteredInvoices.length}</strong> of{' '}
              <span className="font-mono">{invoices.length}</span> invoices
            </span>
            <span className="font-mono text-[11px] text-ink-faint">
              Stripe Radar Drawer Pattern Enabled
            </span>
          </div>
        )}
      </div>

      {/* Invoice Drawer */}
      <InvoiceDrawer
        invoiceId={selectedInvoiceId}
        onClose={() => setSelectedInvoiceId(null)}
        onInvoiceUpdated={fetchInvoicesList}
      />
    </div>
  );
};
