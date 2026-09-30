import React from 'react';
import { useBenchmark } from '../hooks/useBenchmark';
import { Award, AlertTriangle, CheckCircle, Info, BarChart3, Database } from 'lucide-react';

export function BenchmarkView() {
  const { benchmarkData, isLoading, error } = useBenchmark();

  const overall = benchmarkData?.overall || {};
  const byDist = benchmarkData?.by_distance || {};

  return (
    <div className="max-w-[1720px] mx-auto px-4 sm:px-6 py-6 space-y-6">
      {/* Header Banner */}
      <div className="bg-canvas-card border border-border-light rounded-xl p-6 shadow-card">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-800 text-[10px] font-bold uppercase tracking-wider">
                Formal Offline Evaluation
              </span>
              <span className="text-xs text-ink-muted">Driver E (IO-VNBD Held-Out Split)</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-ink-primary mt-2">
              Historical Benchmark Evidence
            </h1>
            <p className="text-sm text-ink-secondary mt-1 max-w-3xl leading-relaxed">
              Rigorous held-out evaluation across 34 blackout windows in the IO-VNBD dataset.
              This evaluation is strictly separate from interactive manual experimentation; no artificial baselines are fabricated.
            </p>
          </div>

          <div className="flex items-center gap-3 self-start md:self-auto">
            <div className="px-3.5 py-2 rounded-lg bg-tech-amber-subtle border border-tech-amber-border text-xs font-medium text-amber-900 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-tech-amber flex-shrink-0" />
              <span>Target &lt;10% drift not yet met without wheel odometry</span>
            </div>
          </div>
        </div>
      </div>

      {/* Aggregate Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
        <div className="bg-canvas-card border border-border-light rounded-xl p-4 shadow-card">
          <div className="text-[11px] font-medium text-ink-muted uppercase tracking-wider">
            Test Runs
          </div>
          <div className="text-2xl font-bold font-mono text-ink-primary mt-1">
            {benchmarkData?.independent_test_runs ?? '11'}
          </div>
          <div className="text-[10px] text-ink-faint mt-1">Independent runs</div>
        </div>

        <div className="bg-canvas-card border border-border-light rounded-xl p-4 shadow-card">
          <div className="text-[11px] font-medium text-ink-muted uppercase tracking-wider">
            Evaluated Outages
          </div>
          <div className="text-2xl font-bold font-mono text-ink-primary mt-1">
            {benchmarkData?.total_outages_evaluated ?? '34'}
          </div>
          <div className="text-[10px] text-ink-faint mt-1">Blackout windows</div>
        </div>

        <div className="bg-canvas-card border border-border-light rounded-xl p-4 shadow-card">
          <div className="text-[11px] font-medium text-ink-muted uppercase tracking-wider">
            Median Error
          </div>
          <div className="text-2xl font-bold font-mono text-ink-primary mt-1">
            {overall.median_endpoint_error_m !== undefined
              ? `${overall.median_endpoint_error_m.toFixed(1)} m`
              : '354.3 m'}
          </div>
          <div className="text-[10px] text-ink-faint mt-1">Endpoint drift</div>
        </div>

        <div className="bg-canvas-card border border-border-light rounded-xl p-4 shadow-card">
          <div className="text-[11px] font-medium text-ink-muted uppercase tracking-wider">
            Median Drift %
          </div>
          <div className="text-2xl font-bold font-mono text-tech-amber mt-1">
            {overall.median_drift_percent !== undefined
              ? `${overall.median_drift_percent.toFixed(1)}%`
              : '80.3%'}
          </div>
          <div className="text-[10px] text-amber-700 mt-1">Normalized to outage dist</div>
        </div>

        <div className="bg-canvas-card border border-border-light rounded-xl p-4 shadow-card">
          <div className="text-[11px] font-medium text-ink-muted uppercase tracking-wider">
            Below 10% Target
          </div>
          <div className="text-2xl font-bold font-mono text-tech-red mt-1">
            {overall.pass_rate_below_10_percent !== undefined
              ? `${(overall.pass_rate_below_10_percent * 100).toFixed(1)}%`
              : '0.0%'}
          </div>
          <div className="text-[10px] text-red-700 mt-1">0 / 34 passed</div>
        </div>
      </div>

      {/* Distance Breakdown Table */}
      <div className="bg-canvas-card border border-border-light rounded-xl overflow-hidden shadow-card">
        <div className="px-6 py-4 border-b border-border-light flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-tech-blue" />
            <h2 className="text-sm font-bold uppercase tracking-wider text-ink-primary">
              Distance Breakdown & Baseline Comparison
            </h2>
          </div>
          <span className="text-xs font-mono text-ink-muted">Driver E Held-Out Split</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-canvas-subtle text-ink-muted uppercase text-[10px] font-semibold border-b border-border-light">
              <tr>
                <th className="px-6 py-3">Outage Distance</th>
                <th className="px-6 py-3 font-mono">Evaluated Outages</th>
                <th className="px-6 py-3 font-mono text-tech-blue">Continuum IDR Error</th>
                <th className="px-6 py-3 font-mono">Last-Speed Baseline</th>
                <th className="px-6 py-3 font-mono">Frozen GPS Baseline</th>
                <th className="px-6 py-3 font-mono">Median Drift %</th>
                <th className="px-6 py-3 font-mono">Pass Rate (&lt;10%)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle font-mono text-xs">
              {Object.keys(byDist).length > 0 ? (
                Object.entries(byDist).map(([distKey, row]) => (
                  <tr key={distKey} className="hover:bg-canvas-subtle/50 transition-colors">
                    <td className="px-6 py-3.5 font-sans font-bold text-ink-primary">
                      {distKey} Outage
                    </td>
                    <td className="px-6 py-3.5 text-ink-secondary">{row.outage_count ?? '—'}</td>
                    <td className="px-6 py-3.5 text-tech-blue font-bold">
                      {row.median_endpoint_error_m !== undefined
                        ? `${row.median_endpoint_error_m.toFixed(1)} m`
                        : '—'}
                    </td>
                    <td className="px-6 py-3.5 text-ink-secondary">
                      {row.baseline_last_speed_median_error_m !== undefined
                        ? `${row.baseline_last_speed_median_error_m.toFixed(1)} m`
                        : '—'}
                    </td>
                    <td className="px-6 py-3.5 text-ink-secondary">
                      {row.baseline_frozen_median_error_m !== undefined
                        ? `${row.baseline_frozen_median_error_m.toFixed(1)} m`
                        : '—'}
                    </td>
                    <td className="px-6 py-3.5 text-tech-amber font-semibold">
                      {row.median_drift_percent !== undefined
                        ? `${row.median_drift_percent.toFixed(1)}%`
                        : '—'}
                    </td>
                    <td className="px-6 py-3.5 text-tech-red font-semibold">
                      {row.pass_rate_below_10_percent !== undefined
                        ? `${(row.pass_rate_below_10_percent * 100).toFixed(0)}%`
                        : '0%'}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-ink-muted font-sans">
                    {isLoading ? 'Loading benchmark summary from /api/summary...' : error || 'No benchmark data available.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Honest Scientific Boundaries & Limitations */}
      <div className="bg-canvas-card border border-border-light rounded-xl p-6 shadow-card space-y-4">
        <div className="flex items-center gap-2">
          <Info className="w-5 h-5 text-tech-blue" />
          <h3 className="text-sm font-bold uppercase tracking-wider text-ink-primary">
            Methodological Boundaries & Limitations
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-ink-secondary leading-relaxed">
          <div className="p-4 rounded-lg bg-canvas-subtle border border-border-light space-y-1.5">
            <strong className="text-ink-primary block font-semibold">
              1. Phone GNSS Update Frequency
            </strong>
            <p>
              In IO-VNBD Driver E smartphone recordings, raw GPS coordinates refresh at ~0.1 Hz (~9–10 second intervals).
              The engine processes only genuine fixes and rejects duplicate or stale updates.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-canvas-subtle border border-border-light space-y-1.5">
            <strong className="text-ink-primary block font-semibold">
              2. Inertial Sensor Thermal Drift
            </strong>
            <p>
              Consumer smartphone MEMS gyroscopes experience thermal bias drift accumulating unconstrained over outages exceeding 40 seconds.
              Without road-network map matching or CAN wheel odometry, the &lt;10% drift target is currently missed.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-canvas-subtle border border-border-light space-y-1.5">
            <strong className="text-ink-primary block font-semibold">
              3. Recorded Dataset Demonstration
            </strong>
            <p>
              This studio interface connects to a local desktop Python SDK session processing recorded IO-VNBD sensors.
              It is not live smartphone hardware sensing and not validated for safety-critical aviation or automotive autopilot.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-canvas-subtle border border-border-light space-y-1.5">
            <strong className="text-ink-primary block font-semibold">
              4. No Arbitrary Baselines
            </strong>
            <p>
              Comparison baselines (frozen position, last speed) are only defined for standard fixed-interval benchmark windows,
              not manual interactive toggling. We report all raw metrics without embellishment.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
