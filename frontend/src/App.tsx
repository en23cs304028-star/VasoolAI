import React, { useState } from 'react';
import { OverviewPage } from './pages/Overview';
import { InvoicesPage } from './pages/Invoices';
import { BacktestPage } from './pages/Backtest';
import { AuditLogPage } from './pages/AuditLog';
import { ShieldCheck, FileText, Activity, Layers } from 'lucide-react';

type NavTab = 'overview' | 'invoices' | 'backtest' | 'audit_log';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('overview');

  const navItems: { id: NavTab; label: string; icon: React.ReactNode }[] = [
    { id: 'overview', label: 'Overview', icon: <Layers className="w-4 h-4" /> },
    { id: 'invoices', label: 'Invoices', icon: <FileText className="w-4 h-4" /> },
    { id: 'backtest', label: 'Backtest', icon: <Activity className="w-4 h-4" /> },
    { id: 'audit_log', label: 'Audit Log', icon: <ShieldCheck className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-bg font-sans selection:bg-primary-soft selection:text-primary">
      {/* Top Console Navigation Bar */}
      <header className="sticky top-0 z-40 bg-surface border-b border-border shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            {/* Left: Brand / Logo */}
            <div className="flex items-center gap-6">
              <div
                onClick={() => setActiveTab('overview')}
                className="flex items-center gap-2 cursor-pointer group"
              >
                <div className="w-7 h-7 rounded-md bg-primary flex items-center justify-center text-white font-bold text-sm tracking-tight shadow-sm group-hover:bg-primary-hover transition-colors">
                  V
                </div>
                <div>
                  <span className="text-base font-bold tracking-tight text-ink font-mono">
                    VasoolAI
                  </span>
                  <span className="ml-2 text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface-raised border border-border text-ink-soft hidden sm:inline-block">
                    Track 03 &middot; MSMED Engine
                  </span>
                </div>
              </div>

              {/* Center: 4 Nav Screens */}
              <nav className="hidden md:flex items-center space-x-1">
                {navItems.map((item) => {
                  const isActive = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setActiveTab(item.id)}
                      className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-1.5 ${
                        isActive
                          ? 'bg-surface-raised text-primary font-semibold border border-border/60 shadow-xs'
                          : 'text-ink-soft hover:text-ink hover:bg-surface-raised/60'
                      }`}
                    >
                      {item.icon}
                      {item.label}
                    </button>
                  );
                })}
              </nav>
            </div>

            {/* Right: Status Pill & Razorpay Buildathon Submission Indicator */}
            <div className="flex items-center gap-3">
              <div className="hidden lg:flex items-center gap-1.5 text-[11px] font-mono text-ink-soft bg-surface-raised px-2.5 py-1 rounded border border-border">
                <span className="w-2 h-2 rounded-full bg-[#16794E] animate-pulse" />
                <span>Test Mode Sandbox</span>
              </div>
            </div>
          </div>
        </div>

        {/* Mobile Navigation Bar */}
        <div className="md:hidden flex items-center justify-around border-t border-border bg-surface py-1">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`py-1.5 px-3 text-xs font-medium rounded flex items-center gap-1 ${
                  isActive ? 'text-primary font-semibold bg-surface-raised' : 'text-ink-soft'
                }`}
              >
                {item.label}
              </button>
            );
          })}
        </div>
      </header>

      {/* Main Content Viewport */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'overview' && (
          <OverviewPage onNavigateToInvoices={() => setActiveTab('invoices')} />
        )}
        {activeTab === 'invoices' && <InvoicesPage />}
        {activeTab === 'backtest' && <BacktestPage />}
        {activeTab === 'audit_log' && <AuditLogPage />}
      </main>

      {/* Subtle Footer */}
      <footer className="border-t border-border bg-surface py-3 text-center text-[11px] text-ink-faint font-mono">
        VasoolAI &mdash; Razorpay AI Buildathon Submission (Track 03) &middot; MSMED Act Statutory Interest Engine &middot; Real Sandboxed Rails
      </footer>
    </div>
  );
};
