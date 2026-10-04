import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { Activity } from 'lucide-react';

export function ErrorChart({ snapshot }) {
  const samples = snapshot?.samples || [];

  const chartData = useMemo(() => {
    if (!samples.length) return [];
    const step = Math.max(1, Math.floor(samples.length / 100));
    const pts = [];

    for (let i = 0; i < samples.length; i += step) {
      const s = samples[i];
      const errorM = s.error_m !== null && Number.isFinite(s.error_m) ? Number(s.error_m.toFixed(1)) : null;
      const uncertM = s.state?.horizontal_uncertainty_m !== null && Number.isFinite(s.state?.horizontal_uncertainty_m)
        ? Number(s.state.horizontal_uncertainty_m.toFixed(1))
        : null;

      pts.push({
        time: s.elapsed_s !== null && Number.isFinite(s.elapsed_s) ? Number(s.elapsed_s.toFixed(1)) : 0,
        error: errorM,
        uncertainty: uncertM,
      });
    }

    const last = samples[samples.length - 1];
    if (pts.length > 0 && pts[pts.length - 1].time !== Number(last.elapsed_s?.toFixed(1))) {
      pts.push({
        time: Number(last.elapsed_s?.toFixed(1) || 0),
        error: last.error_m !== null && Number.isFinite(last.error_m) ? Number(last.error_m.toFixed(1)) : null,
        uncertainty: last.state?.horizontal_uncertainty_m !== null && Number.isFinite(last.state?.horizontal_uncertainty_m)
          ? Number(last.state.horizontal_uncertainty_m.toFixed(1))
          : null,
      });
    }

    return pts;
  }, [samples]);

  const maxVal = useMemo(() => {
    let m = 20;
    chartData.forEach((d) => {
      if (d.error && d.error > m) m = d.error;
      if (d.uncertainty && d.uncertainty > m) m = d.uncertainty;
    });
    return Math.ceil(m * 1.15);
  }, [chartData]);

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-blue-600" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
            Real-time Error (m) & Uncertainty (1σ)
          </h3>
        </div>

        <div className="flex items-center gap-4 text-xs font-medium">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-blue-600 rounded-full" />
            <span className="text-slate-600 text-[11px]">Estimated Error</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-2 bg-blue-100 border border-blue-200 rounded-sm" />
            <span className="text-slate-600 text-[11px]">Uncertainty (1σ)</span>
          </div>
        </div>
      </div>

      <div className="h-44 w-full">
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
              <defs>
                <linearGradient id="errorUncertaintyGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563EB" stopOpacity={0.16} />
                  <stop offset="95%" stopColor="#2563EB" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis
                dataKey="time"
                tickLine={false}
                axisLine={{ stroke: '#e2e8f0' }}
                tick={{ fontSize: 10, fill: '#94a3b8', fontFamily: 'JetBrains Mono' }}
                unit="s"
              />
              <YAxis
                domain={[0, maxVal]}
                tickLine={false}
                axisLine={{ stroke: '#e2e8f0' }}
                tick={{ fontSize: 10, fill: '#94a3b8', fontFamily: 'JetBrains Mono' }}
                unit="m"
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload?.length) return null;
                  const d = payload[0].payload;
                  return (
                    <div className="bg-white/95 backdrop-blur-sm border border-slate-200 rounded-lg p-2 shadow-md text-xs font-mono">
                      <div className="text-[11px] text-slate-500 mb-1 font-sans">
                        Elapsed: <strong className="text-slate-900">{d.time}s</strong>
                      </div>
                      <div className="text-blue-600 font-semibold">
                        Error: {d.error !== null ? `${d.error} m` : '—'}
                      </div>
                      <div className="text-slate-600">
                        Uncertainty: {d.uncertainty !== null ? `±${d.uncertainty} m` : '—'}
                      </div>
                    </div>
                  );
                }}
              />
              <Area
                type="monotone"
                dataKey="uncertainty"
                stroke="#93c5fd"
                strokeWidth={1}
                fillOpacity={1}
                fill="url(#errorUncertaintyGrad)"
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="error"
                stroke="#2563eb"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-xs text-slate-400">
            No telemetry samples available yet. Start the engine to plot real-time error.
          </div>
        )}
      </div>
    </div>
  );
}
