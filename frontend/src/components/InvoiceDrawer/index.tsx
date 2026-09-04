import React, { useEffect, useState } from 'react';
import { getInvoice } from '../../api/invoices';
import { InvoiceDetail } from '../../types/models';
import { DetailsTab } from './DetailsTab';
import { TimelineTab } from './TimelineTab';
import { X, RefreshCw } from 'lucide-react';

interface InvoiceDrawerProps {
  invoiceId: number | null;
  onClose: () => void;
  onInvoiceUpdated?: () => void;
}

export const InvoiceDrawer: React.FC<InvoiceDrawerProps> = ({
  invoiceId,
  onClose,
  onInvoiceUpdated,
}) => {
  const [activeTab, setActiveTab] = useState<'details' | 'timeline'>('details');
  const [invoice, setInvoice] = useState<InvoiceDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDetail = async () => {
    if (!invoiceId) return;
    try {
      setLoading(true);
      setError(null);
      const data = await getInvoice(invoiceId);
      setInvoice(data);
      if (onInvoiceUpdated) onInvoiceUpdated();
    } catch (err: any) {
      setError(err.message || 'Failed to fetch invoice details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (invoiceId) {
      setActiveTab('details');
      fetchDetail();
    } else {
      setInvoice(null);
    }
  }, [invoiceId]);

  if (!invoiceId) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* 30% ink opacity overlay */}
      <div
        onClick={onClose}
        className="fixed inset-0 bg-[#101828]/30 backdrop-blur-[1px] transition-opacity duration-200"
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-[480px] bg-surface shadow-drawer flex flex-col z-10 border-l border-border transform transition ease-in-out duration-300">
          {/* Header */}
          <div className="p-5 border-b border-border bg-surface flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs px-2 py-0.5 rounded bg-surface-raised border border-border text-ink font-semibold">
                  {invoice?.invoice_number || `Invoice #${invoiceId}`}
                </span>
                {invoice && (
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] uppercase font-medium font-mono ${
                      invoice.status === 'paid'
                        ? 'bg-low-bg text-low'
                        : invoice.status === 'partially_paid'
                        ? 'bg-medium-bg text-medium'
                        : 'bg-surface-raised text-ink-soft border border-border'
                    }`}
                  >
                    {invoice.status}
                  </span>
                )}
              </div>
              <h2 className="text-base font-semibold text-ink mt-1.5 truncate max-w-[360px]">
                {invoice?.buyer_name || 'Loading Buyer...'}
              </h2>
              <div className="text-xs text-ink-soft flex items-center gap-2 mt-0.5">
                <span>Supplier: {invoice?.supplier_name || 'Demo Supplier'}</span>
                <span>&bull;</span>
                <span className="font-mono">Due: {invoice?.due_date}</span>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={fetchDetail}
                title="Refresh"
                className="p-1.5 rounded text-ink-soft hover:text-ink hover:bg-surface-raised transition-colors"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={onClose}
                title="Close drawer (Esc)"
                className="p-1.5 rounded text-ink-soft hover:text-ink hover:bg-surface-raised transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Navigation Tabs (Details | Timeline) */}
          <div className="flex border-b border-border bg-surface px-5">
            <button
              onClick={() => setActiveTab('details')}
              className={`py-3 text-xs font-semibold border-b-2 mr-6 transition-all ${
                activeTab === 'details'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-ink-soft hover:text-ink'
              }`}
            >
              Details &amp; Action
            </button>
            <button
              onClick={() => setActiveTab('timeline')}
              className={`py-3 text-xs font-semibold border-b-2 transition-all ${
                activeTab === 'timeline'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-ink-soft hover:text-ink'
              }`}
            >
              Audit Timeline
            </button>
          </div>

          {/* Body Content */}
          <div className="flex-1 overflow-y-auto p-5 bg-bg">
            {loading && !invoice ? (
              <div className="py-20 text-center text-sm text-ink-soft">
                <div className="inline-block w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin mb-2" />
                <p>Loading details...</p>
              </div>
            ) : error ? (
              <div className="p-4 bg-high-bg border border-high/30 rounded text-xs text-high">
                {error}
              </div>
            ) : invoice ? (
              activeTab === 'details' ? (
                <DetailsTab invoice={invoice} onRefresh={fetchDetail} />
              ) : (
                <TimelineTab invoiceId={invoice.id} buyerId={invoice.buyer_id} />
              )
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
};
