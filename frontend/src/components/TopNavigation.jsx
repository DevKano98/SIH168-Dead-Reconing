import React from 'react';
import { Navigation, Compass, ExternalLink, Activity, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react';

export function TopNavigation({ activeTab, setActiveTab, snapshot, connectionStatus, retryConnection }) {
  const getStatusBadge = () => {
    switch (connectionStatus) {
      case 'connected':
        return (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-tech-green-subtle text-tech-green border border-green-200">
            <span className="w-2 h-2 rounded-full bg-tech-green animate-pulse" />
            <span>Connected (SDK Runtime)</span>
          </div>
        );
      case 'syncing':
        return (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-tech-blue-subtle text-tech-blue border border-tech-blue-border">
            <RefreshCw className="w-3 h-3 animate-spin" />
            <span>Syncing State...</span>
          </div>
        );
      case 'error':
      default:
        return (
          <button
            onClick={retryConnection}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-tech-red-subtle text-tech-red border border-red-200 hover:bg-red-100 transition-colors"
            title="Click to retry connection"
          >
            <AlertTriangle className="w-3 h-3" />
            <span>Disconnected (Retry)</span>
          </button>
        );
    }
  };

  return (
    <header className="bg-canvas-card border-b border-border-light sticky top-0 z-40 select-none">
      <div className="max-w-[1720px] mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-4">
        {/* Brand identity */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-tech-blue flex items-center justify-center text-white shadow-sm">
              <Navigation className="w-4 h-4 transform -rotate-45" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-ink-primary tracking-tight text-base leading-none">Continuum</span>
                <span className="font-semibold text-tech-blue text-xs uppercase tracking-wider px-1.5 py-0.5 bg-tech-blue-subtle rounded border border-tech-blue-border">Studio</span>
              </div>
              <p className="text-[10px] text-ink-muted leading-tight font-medium mt-0.5">Autonomous Dead Reckoning SDK</p>
            </div>
          </div>

          {/* Navigation view tabs */}
          <nav className="hidden md:flex items-center gap-1 border-l border-border-light pl-6">
            <button
              onClick={() => setActiveTab('studio')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'studio'
                  ? 'bg-canvas-subtle text-tech-blue shadow-card'
                  : 'text-ink-secondary hover:text-ink-primary hover:bg-canvas-subtle/50'
              }`}
            >
              Studio Workspace
            </button>
            <button
              onClick={() => setActiveTab('benchmark')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'benchmark'
                  ? 'bg-canvas-subtle text-tech-blue shadow-card'
                  : 'text-ink-secondary hover:text-ink-primary hover:bg-canvas-subtle/50'
              }`}
            >
              Historical Benchmark Evidence
            </button>
          </nav>
        </div>

        {/* View Links & Session Metadata */}
        <div className="flex items-center gap-3">
          <div className="hidden lg:flex items-center gap-2 text-xs font-mono text-ink-muted border-r border-border-light pr-4">
            {snapshot?.run_id && (
              <span className="px-2 py-0.5 rounded bg-canvas-subtle border border-border-light text-[11px]">
                Run: <strong className="text-ink-primary font-semibold">{snapshot.run_id}</strong>
              </span>
            )}
            {snapshot?.model_id && (
              <span className="px-2 py-0.5 rounded bg-canvas-subtle border border-border-light text-[11px]">
                Model: <strong className="text-ink-primary font-semibold">{snapshot.model_id}</strong>
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <a
              href="/mobile"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-ink-secondary hover:text-tech-blue bg-canvas-subtle hover:bg-tech-blue-subtle rounded border border-border-light transition-colors"
            >
              <span>Driver HUD</span>
              <ExternalLink className="w-3 h-3 opacity-60" />
            </a>
            <a
              href="/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-ink-secondary hover:text-tech-blue bg-canvas-subtle hover:bg-tech-blue-subtle rounded border border-border-light transition-colors"
            >
              <span>Docs</span>
              <ExternalLink className="w-3 h-3 opacity-60" />
            </a>
          </div>

          {/* Connection status badge */}
          <div className="pl-1">
            {getStatusBadge()}
          </div>
        </div>
      </div>
    </header>
  );
}
