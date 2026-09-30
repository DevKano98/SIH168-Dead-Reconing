import React from 'react';
import { Award, AlertTriangle, ShieldCheck } from 'lucide-react';

export function BenchmarkOverview({ benchmarkData }) {
  const overall = benchmarkData?.overall || {};

  return (
    <div className="space-y-5">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-slate-800 text-[10px] font-bold uppercase tracking-wider">
                HISTORICAL EVALUATION
              </span>
              <span className="text-xs text-slate-400">Driver E Held-Out Split</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-2">
              Historical Benchmark Evidence
            </h1>
            <p className="text-xs text-slate-500 mt-1 max-w-3xl leading-relaxed">
              Formal offline evaluation across held-out blackout windows.
              Clearly separate historical evaluation from the current live simulation; no comparison baseline exists for manual experimentation.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto px-3 py-2 rounded-xl bg-amber-50 border border-amber-200 text-xs font-medium text-amber-900">
            <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
            <span>Target &lt;10% drift not yet met without wheel odometry</span>
          </div>
        </div>
      </div>

      {/* Top 5 Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
          <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
            Independent Test Runs
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
            {benchmarkData?.independent_test_runs ?? '11'}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">Held-out pairs</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
          <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
            Evaluated Outages
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
            {benchmarkData?.total_outages_evaluated ?? '34'}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">Blackout windows</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
          <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
            Median Endpoint Error
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
            {overall.median_endpoint_error_m !== undefined
              ? `${overall.median_endpoint_error_m.toFixed(1)} m`
              : '354.3 m'}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">Endpoint drift</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
          <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
            Median Drift
          </div>
          <div className="text-2xl font-bold font-mono text-amber-600 mt-1">
            {overall.median_drift_percent !== undefined
              ? `${overall.median_drift_percent.toFixed(1)}%`
              : '80.3%'}
          </div>
          <div className="text-[10px] text-amber-700 mt-1">Normalized to outage</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
          <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
            Below 10% Target
          </div>
          <div className="text-2xl font-bold font-mono text-amber-600 mt-1">
            {overall.pass_rate_below_10_percent !== undefined
              ? `${(overall.pass_rate_below_10_percent * 100).toFixed(0)}%`
              : '0%'}
          </div>
          <div className="text-[10px] text-amber-700 mt-1">0 / 34 passed</div>
        </div>
      </div>
    </div>
  );
}
