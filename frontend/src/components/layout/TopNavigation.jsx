import React from 'react';
import { Navigation, ExternalLink, RefreshCw, AlertTriangle, CheckCircle2 } from 'lucide-react';

export function TopNavigation({ activePage, setActivePage, connectionStatus, retryConnection, snapshot }) {
  const renderStatusPill = () => {
    switch (connectionStatus) {
      case 'connected':
        return (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Connected (SDK Runtime)</span>
          </div>
        );
      case 'syncing':
        return (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
            <RefreshCw className="w-3 h-3 animate-spin text-blue-600" />
            <span>Syncing...</span>
          </div>
        );
      case 'error':
      default:
        return (
          <button
            onClick={retryConnection}
            className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 transition-colors"
            title="Click to reconnect"
          >
            <AlertTriangle className="w-3 h-3 text-rose-600" />
            <span>Disconnected (Retry)</span>
          </button>
        );
    }
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 sticky top-0 z-40 select-none px-4 sm:px-6">
      <div className="h-full flex items-center justify-between max-w-[1720px] mx-auto">
        {/* Left: Continuum brand mark */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm">
            <Navigation className="w-4 h-4 transform -rotate-45" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-bold text-lg text-slate-900 tracking-tight">Continuum</span>
            <span className="text-[11px] font-bold uppercase tracking-wider text-blue-600 px-1.5 py-0.2 rounded bg-blue-50 border border-blue-200">
              STUDIO
            </span>
          </div>
        </div>

        {/* Center: Primary navigation tabs */}
        <nav className="hidden md:flex items-center gap-1 bg-slate-50 p-1 rounded-lg border border-slate-200">
          <button
            onClick={() => setActivePage('studio')}
            className={`px-3.5 py-1.5 rounded-md text-xs font-semibold transition-all ${
              activePage === 'studio'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Studio
          </button>
          <button
            onClick={() => setActivePage('benchmark')}
            className={`px-3.5 py-1.5 rounded-md text-xs font-semibold transition-all ${
              activePage === 'benchmark'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Evidence & Benchmark
          </button>
          <a
            href="/mobile"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium text-slate-600 hover:text-blue-600 hover:bg-white/60 transition-colors"
          >
            <span>Driver View</span>
            <ExternalLink className="w-3 h-3 opacity-60" />
          </a>
          <a
            href="/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium text-slate-600 hover:text-blue-600 hover:bg-white/60 transition-colors"
          >
            <span>Developer Docs</span>
            <ExternalLink className="w-3 h-3 opacity-60" />
          </a>
        </nav>

        {/* Right: Metadata & Connection status pill */}
        <div className="flex items-center gap-3">
          {snapshot?.run_id && (
            <div className="hidden xl:flex items-center gap-2 text-xs font-mono text-slate-500 bg-slate-50 px-2.5 py-1 rounded border border-slate-200">
              <span>Run: <strong className="text-slate-800">{snapshot.run_id}</strong></span>
              <span className="text-slate-300">|</span>
              <span>Model: <strong className="text-slate-800">{snapshot.model_id}</strong></span>
            </div>
          )}
          {renderStatusPill()}
        </div>
      </div>
    </header>
  );
}
