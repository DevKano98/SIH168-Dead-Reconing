import React, { useState } from 'react';
import { History, ChevronDown, ChevronUp } from 'lucide-react';
import { fmtNum } from '../../utils/formatters';

export function EventLog({ events = [] }) {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 bg-white hover:bg-slate-50 transition-colors flex items-center justify-between text-left select-none"
      >
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-blue-600" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
            Session Control Event Log
          </h3>
          <span className="text-[11px] font-mono text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
            {events.length} event{events.length === 1 ? '' : 's'}
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-slate-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-slate-400" />
        )}
      </button>

      {isExpanded && (
        <div className="border-t border-slate-100 overflow-x-auto max-h-52">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] font-semibold sticky top-0 border-b border-slate-200">
              <tr>
                <th className="px-4 py-2 font-mono">Time (s)</th>
                <th className="px-4 py-2">Event</th>
                <th className="px-4 py-2">Details</th>
                <th className="px-4 py-2">GPS State</th>
                <th className="px-4 py-2 font-mono">Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-xs">
              {events.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-4 text-center text-slate-400 font-sans">
                    No control events recorded yet.
                  </td>
                </tr>
              ) : (
                [...events].reverse().map((ev, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-4 py-2 text-slate-600">
                      {ev.time_s !== undefined ? Number(ev.time_s).toFixed(2) : '—'}
                    </td>
                    <td className="px-4 py-2 font-sans font-semibold text-slate-800">
                      {ev.action}
                    </td>
                    <td className="px-4 py-2 font-sans text-slate-500 text-[11px]">
                      Source index: {ev.after_source_index ?? '—'}
                    </td>
                    <td className="px-4 py-2 font-sans">
                      {ev.gnss_enabled ? (
                        <span className="text-emerald-600 font-medium">Delivering</span>
                      ) : (
                        <span className="text-rose-600 font-medium">Withheld</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-slate-600">
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
