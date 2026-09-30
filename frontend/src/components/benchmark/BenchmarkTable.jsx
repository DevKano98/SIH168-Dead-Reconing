import React from 'react';
import { BarChart3 } from 'lucide-react';
import { fmtNum } from '../../utils/formatters';

export function BenchmarkTable({ byDistance = {}, isLoading, error }) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
      <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-blue-600" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800">
            Distance Breakdown & Baseline Comparison
          </h2>
        </div>
        <span className="text-xs font-mono text-slate-400">Driver E Held-Out Evaluation</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs text-left">
          <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] font-semibold border-b border-slate-200">
            <tr>
              <th className="px-6 py-3">Outage Distance</th>
              <th className="px-6 py-3 font-mono text-right">Outages Evaluated</th>
              <th className="px-6 py-3 font-mono text-right text-blue-600">IDR Median Error</th>
              <th className="px-6 py-3 font-mono text-right">Last-Speed Baseline</th>
              <th className="px-6 py-3 font-mono text-right">Frozen GPS Baseline</th>
              <th className="px-6 py-3 font-mono text-right">Median Drift %</th>
              <th className="px-6 py-3 font-mono text-right">Pass Rate (&lt;10%)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-mono text-xs">
            {Object.keys(byDistance).length > 0 ? (
              Object.entries(byDistance).map(([distKey, row]) => (
                <tr key={distKey} className="hover:bg-slate-50/50 transition-colors">
                  <td className="px-6 py-3.5 font-sans font-bold text-slate-900">
                    {distKey} Outage
                  </td>
                  <td className="px-6 py-3.5 text-right text-slate-600">
                    {row.outage_count ?? '—'}
                  </td>
                  <td className="px-6 py-3.5 text-right text-blue-600 font-bold">
                    {fmtNum(row.median_endpoint_error_m, 1)} m
                  </td>
                  <td className="px-6 py-3.5 text-right text-slate-600">
                    {fmtNum(row.baseline_last_speed_median_error_m, 1)} m
                  </td>
                  <td className="px-6 py-3.5 text-right text-slate-600">
                    {fmtNum(row.baseline_frozen_median_error_m, 1)} m
                  </td>
                  <td className="px-6 py-3.5 text-right text-amber-600 font-semibold">
                    {fmtNum(row.median_drift_percent, 1)}%
                  </td>
                  <td className="px-6 py-3.5 text-right text-amber-600 font-semibold">
                    {row.pass_rate_below_10_percent !== undefined
                      ? `${(row.pass_rate_below_10_percent * 100).toFixed(0)}%`
                      : '0%'}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={7} className="px-6 py-8 text-center text-slate-400 font-sans">
                  {isLoading ? 'Loading historical benchmark summary...' : error || 'No data available.'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
