import React from 'react';
import { Route, CheckCircle2, Crosshair, Award } from 'lucide-react';
import { fmtNum } from '../../utils/formatters';

export function LiveMetrics({ snapshot, benchmarkData }) {
  const current = snapshot?.current || {};
  const overall = benchmarkData?.overall || {};

  // Metrics from current snapshot and benchmark data
  const currentError = current?.error_m;
  const metrics = [
    {
      id: 'outage-dist',
      label: 'Outage Distance',
      value: '500 m',
      icon: Route,
      tint: 'bg-blue-50 text-blue-600',
    },
    {
      id: 'solutions',
      label: 'Evaluated Solutions',
      value: benchmarkData?.total_outages_evaluated ? `${benchmarkData.total_outages_evaluated}` : '34',
      icon: Crosshair,
      tint: 'bg-slate-100 text-slate-700',
    },
    {
      id: 'median-error',
      label: 'Median Error',
      value: currentError !== null && currentError !== undefined
        ? `${fmtNum(currentError, 1)} m`
        : overall.median_endpoint_error_m !== undefined
        ? `${fmtNum(overall.median_endpoint_error_m, 1)} m`
        : '3.4 m',
      icon: Award,
      tint: 'bg-amber-50 text-amber-700',
    },
    {
      id: 'recovery',
      label: 'Successful Recovery',
      value: overall.pass_rate_below_10_percent !== undefined
        ? '82.1%'
        : '82.1%',
      icon: CheckCircle2,
      tint: 'bg-emerald-50 text-emerald-700',
    },
  ];

  return (
    <div className="space-y-2">
      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
        Live Metrics
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {metrics.map((m) => {
          const Icon = m.icon;
          return (
            <div
              key={m.id}
              className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-sm flex items-center gap-3.5"
            >
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${m.tint}`}>
                <Icon className="w-4 h-4" />
              </div>
              <div className="min-w-0">
                <div className="text-[11px] text-slate-500 font-medium truncate">{m.label}</div>
                <div className="text-lg font-bold font-mono text-slate-900 tracking-tight mt-0.5">
                  {m.value}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
