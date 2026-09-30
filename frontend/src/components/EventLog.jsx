import React, { useState } from 'react';
import { ChevronDown, ChevronUp, History } from 'lucide-react';

export function EventLog({ events = [] }) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="bg-canvas-card border border-border-light rounded-xl overflow-hidden shadow-card">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 bg-canvas-card hover:bg-canvas-subtle/50 transition-colors flex items-center justify-between text-left select-none"
      >
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-tech-blue" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-ink-primary">
            Session Control Event Log
          </h3>
          <span className="text-[11px] font-mono text-ink-muted bg-canvas-subtle px-1.5 py-0.5 rounded border border-border-light">
            {events.length} event{events.length === 1 ? '' : 's'}
          </span>
        </div>
        {isOpen ? (
          <ChevronUp className="w-4 h-4 text-ink-muted" />
        ) : (
          <ChevronDown className="w-4 h-4 text-ink-muted" />
        )}
      </button>

      {isOpen && (
        <div className="border-t border-border-light overflow-x-auto max-h-56">
          <table className="w-full text-xs text-left">
            <thead className="bg-canvas-subtle text-ink-muted uppercase text-[10px] font-semibold sticky top-0 border-b border-border-light">
              <tr>
                <th className="px-4 py-2 font-mono">Timestamp (s)</th>
                <th className="px-4 py-2">Action</th>
                <th className="px-4 py-2 font-mono">After Source Index</th>
                <th className="px-4 py-2">GPS State</th>
                <th className="px-4 py-2 font-mono">Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle font-mono text-[11px]">
              {events.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-4 text-center text-ink-faint font-sans">
                    No control events recorded yet.
                  </td>
                </tr>
              ) : (
                [...events].reverse().map((ev, idx) => (
                  <tr key={idx} className="hover:bg-canvas-subtle/30 transition-colors">
                    <td className="px-4 py-2 text-ink-secondary">
                      {ev.time_s !== undefined && Number.isFinite(ev.time_s)
                        ? ev.time_s.toFixed(2)
                        : '—'}
                    </td>
                    <td className="px-4 py-2 font-sans font-semibold text-ink-primary">
                      {ev.action}
                    </td>
                    <td className="px-4 py-2 text-ink-muted">{ev.after_source_index ?? '—'}</td>
                    <td className="px-4 py-2 font-sans">
                      {ev.gnss_enabled ? (
                        <span className="text-tech-green font-medium">Delivering</span>
                      ) : (
                        <span className="text-tech-amber font-medium">Withheld</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-ink-secondary">
                      {ev.rate !== undefined ? `${ev.rate}×` : '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
