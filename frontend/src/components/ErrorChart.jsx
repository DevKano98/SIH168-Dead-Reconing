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
import { Activity, ShieldCheck } from 'lucide-react';

export function ErrorChart({ snapshot }) {
  const samples = snapshot?.samples || [];

  // Downsample to max 120 points for fluid 60fps chart rendering
  const chartData = useMemo(() => {
    if (!samples.length) return [];
    const step = Math.max(1, Math.floor(samples.length / 120));
    const result = [];

    for (let i = 0; i < samples.length; i += step) {
      const s = samples[i];
      const errorM = s.error_m !== null && Number.isFinite(s.error_m) ? Number(s.error_m.toFixed(1)) : null;
      const uncertM = s.state?.horizontal_uncertainty_m !== null && Number.isFinite(s.state?.horizontal_uncertainty_m)
        ? Number(s.state.horizontal_uncertainty_m.toFixed(1))
        : null;

      result.push({
        time: s.elapsed_s !== null && Number.isFinite(s.elapsed_s) ? Number(s.elapsed_s.toFixed(1)) : 0,
        error: errorM,
        uncertainty: uncertM,
        withheld: s.gnss_withheld,
      });
    }

    // Always include the latest sample
    const last = samples[samples.length - 1];
    if (result.length > 0 && result[result.length - 1].time !== Number(last.elapsed_s?.toFixed(1))) {
      result.push({
        time: Number(last.elapsed_s?.toFixed(1) || 0),
        error: last.error_m !== null && Number.isFinite(last.error_m) ? Number(last.error_m.toFixed(1)) : null,
        uncertainty: last.state?.horizontal_uncertainty_m !== null && Number.isFinite(last.state?.horizontal_uncertainty_m)
          ? Number(last.state.horizontal_uncertainty_m.toFixed(1))
          : null,
        withheld: last.gnss_withheld,
      });
    }

    return result;
  }, [samples]);

  const maxVal = useMemo(() => {
    let m = 20;
    chartData.forEach((d) => {
      if (d.error && d.error > m) m = d.error;
      if (d.uncertainty && d.uncertainty > m) m = d.uncertainty;
    });
    return Math.ceil(m * 1.15);
  }, [chartData]);

  if (!samples.length) {
    return (
      <div className="bg-canvas-card border border-border-light rounded-xl p-4 shadow-card h-48 flex items-center justify-center text-xs text-ink-muted">
        Start the engine to stream real-time position error & uncertainty telemetry.
      </div>
    );
  }

  return (
    <div className="bg-canvas-card border border-border-light rounded-xl p-4 shadow-card">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-tech-blue" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-ink-primary">
            Position Error vs 1-Sigma Uncertainty Envelope
          </h3>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-tech-blue rounded-full" />
            <span className="text-ink-secondary text-[11px] font-medium">Measured Error (m)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-2 bg-blue-100 border border-tech-blue-border rounded-sm" />
            <span className="text-ink-secondary text-[11px] font-medium">1-Sigma Covariance</span>
          </div>
        </div>
      </div>

      <div className="h-44 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="uncertaintyGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2563EB" stopOpacity={0.18} />
                <stop offset="95%" stopColor="#2563EB" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
            <XAxis
              dataKey="time"
              tickLine={false}
              axisLine={{ stroke: '#E2E8F0' }}
              tick={{ fontSize: 10, fill: '#94A3B8', fontFamily: 'JetBrains Mono' }}
              unit="s"
            />
            <YAxis
              domain={[0, maxVal]}
              tickLine={false}
              axisLine={{ stroke: '#E2E8F0' }}
              tick={{ fontSize: 10, fill: '#94A3B8', fontFamily: 'JetBrains Mono' }}
              unit="m"
            />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const d = payload[0].payload;
                return (
                  <div className="bg-white/95 backdrop-blur-sm border border-border-light rounded-lg p-2 shadow-elevated text-xs font-mono">
                    <div className="text-[11px] text-ink-muted mb-1 font-sans">
                      Elapsed: <strong className="text-ink-primary">{d.time}s</strong>
                    </div>
                    <div className="text-tech-blue font-semibold">
                      Measured Error: {d.error !== null ? `${d.error} m` : '—'}
                    </div>
                    <div className="text-ink-secondary">
                      Uncertainty: {d.uncertainty !== null ? `±${d.uncertainty} m` : '—'}
                    </div>
                  </div>
                );
              }}
            />
            <Area
              type="monotone"
              dataKey="uncertainty"
              stroke="#93C5FD"
              strokeWidth={1}
              fillOpacity={1}
              fill="url(#uncertaintyGradient)"
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="error"
              stroke="#2563EB"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
