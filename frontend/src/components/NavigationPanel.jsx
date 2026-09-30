import React from 'react';
import { Gauge, Radio, ShieldAlert, Cpu, Timer, Check, AlertOctagon, Info } from 'lucide-react';

export function NavigationPanel({ snapshot }) {
  const current = snapshot?.current || {};
  const sdkState = current?.state || {};
  const counters = snapshot?.counters || {};

  const trackingMode = sdkState.tracking_mode || 'UNINITIALIZED';
  const speedMps = sdkState.speed_mps;
  const speedKmh = speedMps !== null && speedMps !== undefined && Number.isFinite(speedMps)
    ? (speedMps * 3.6).toFixed(1)
    : '—';

  const headingDeg = sdkState.heading_deg;
  const headingStr = headingDeg !== null && headingDeg !== undefined && Number.isFinite(headingDeg)
    ? `${headingDeg.toFixed(1)}°`
    : '—°';

  const measuredError = current?.error_m;
  const estimatedUncertainty = sdkState.horizontal_uncertainty_m;

  const lastDecision = sdkState.last_gnss_decision || 'NONE';
  const acceptedAge = sdkState.last_accepted_gnss_age_s;
  const healthFlags = sdkState.health_flags || [];

  const elapsedS = current?.elapsed_s || 0;
  const durationS = snapshot?.duration_s || 1;
  const progressPct = Math.min(100, Math.max(0, (elapsedS / durationS) * 100));

  const formatTime = (seconds) => {
    if (seconds === null || seconds === undefined || !Number.isFinite(seconds)) return '00:00.0';
    const s = Math.max(0, Number(seconds));
    const mins = Math.floor(s / 60);
    const secs = (s % 60).toFixed(1);
    return `${String(mins).padStart(2, '0')}:${secs.padStart(4, '0')}`;
  };

  const getModeBadge = (mode) => {
    switch (mode) {
      case 'GNSS_AIDED':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-tech-green-subtle text-tech-green border border-green-200">
            GNSS AIDED
          </span>
        );
      case 'DEAD_RECKONING':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-tech-amber-subtle text-tech-amber border border-tech-amber-border animate-pulse">
            DEAD RECKONING
          </span>
        );
      case 'RECOVERING':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-tech-blue-subtle text-tech-blue border border-tech-blue-border">
            RECOVERING
          </span>
        );
      case 'ALIGNING':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-canvas-subtle text-ink-secondary border border-border-light">
            ALIGNING
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-canvas-subtle text-ink-muted border border-border-light">
            UNINITIALIZED
          </span>
        );
    }
  };

  return (
    <aside className="w-full flex flex-col gap-4">
      {/* 1. Live Navigation State Card */}
      <div className="bg-canvas-card border border-border-light rounded-xl p-4 shadow-card">
        <div className="flex items-center justify-between pb-3 border-b border-border-light">
          <div className="flex items-center gap-2">
            <Gauge className="w-4 h-4 text-tech-blue" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-ink-primary">
              Navigation State
            </h2>
          </div>
          {getModeBadge(trackingMode)}
        </div>

        {/* Speedometer display */}
        <div className="py-4 border-b border-border-light flex items-baseline justify-between">
          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-extrabold font-mono tracking-tight text-ink-primary">
                {speedKmh}
              </span>
              <span className="text-sm font-bold text-ink-muted uppercase">km/h</span>
            </div>
            <div className="text-xs font-mono text-ink-secondary mt-0.5">
              {speedMps !== null && speedMps !== undefined && Number.isFinite(speedMps)
                ? `${speedMps.toFixed(2)} m/s`
                : '— m/s'}
            </div>
          </div>

          <div className="text-right">
            <div className="text-xs text-ink-muted font-medium">Heading</div>
            <div className="text-xl font-bold font-mono text-ink-primary mt-0.5">
              {headingStr}
            </div>
          </div>
        </div>

        {/* Distinct Quantities: Measured Error vs Estimated Uncertainty */}
        <div className="grid grid-cols-2 gap-2.5 py-3 border-b border-border-light">
          <div className="p-2.5 rounded-lg bg-canvas-subtle border border-border-light">
            <div className="text-[11px] font-medium text-ink-muted flex items-center justify-between">
              <span>Measured Error</span>
            </div>
            <div className="text-lg font-bold font-mono text-ink-primary mt-1">
              {measuredError !== null && measuredError !== undefined && Number.isFinite(measuredError)
                ? `${measuredError.toFixed(1)} m`
                : '— m'}
            </div>
            <div className="text-[10px] text-ink-faint mt-0.5 leading-tight">
              Distance to offline reference
            </div>
          </div>

          <div className="p-2.5 rounded-lg bg-tech-blue-subtle/40 border border-tech-blue-border/60">
            <div className="text-[11px] font-medium text-tech-blue flex items-center justify-between">
              <span>Estimated Uncertainty</span>
            </div>
            <div className="text-lg font-bold font-mono text-tech-blue mt-1">
              {estimatedUncertainty !== null && estimatedUncertainty !== undefined && Number.isFinite(estimatedUncertainty)
                ? `±${estimatedUncertainty.toFixed(1)} m`
                : '— m'}
            </div>
            <div className="text-[10px] text-tech-blue/70 mt-0.5 leading-tight">
              EKF 1-sigma horizontal bound
            </div>
          </div>
        </div>

        {/* Telemetry rows */}
        <div className="pt-3 divide-y divide-border-subtle text-xs">
          <div className="flex items-center justify-between py-1.5">
            <span className="text-ink-secondary">GPS Input Switch</span>
            <span
              className={`font-semibold ${
                snapshot?.gnss_enabled ? 'text-tech-green' : 'text-tech-amber'
              }`}
            >
              {snapshot?.gnss_enabled ? 'Delivering Fixes' : 'Withheld (Outage)'}
            </span>
          </div>

          <div className="flex items-center justify-between py-1.5">
            <span className="text-ink-secondary">GPS Delivery Event</span>
            <span className="font-mono text-ink-primary">
              {current?.gnss_withheld ? (
                <span className="text-tech-amber font-semibold">Withheld</span>
              ) : current?.gnss_delivered ? (
                <span className="text-tech-green font-semibold">Fix Delivered</span>
              ) : (
                <span className="text-ink-faint">Idle</span>
              )}
            </span>
          </div>

          <div className="flex items-center justify-between py-1.5">
            <span className="text-ink-secondary">Last GNSS Decision</span>
            <span className="font-mono font-medium text-ink-primary">{lastDecision}</span>
          </div>

          <div className="flex items-center justify-between py-1.5">
            <span className="text-ink-secondary">Accepted GNSS Age</span>
            <span className="font-mono text-ink-primary">
              {acceptedAge !== null && acceptedAge !== undefined && Number.isFinite(acceptedAge)
                ? `${acceptedAge.toFixed(1)} s`
                : '—'}
            </span>
          </div>

          <div className="flex items-center justify-between py-1.5">
            <span className="text-ink-secondary">Active Health Flags</span>
            <span className="font-mono text-xs">
              {healthFlags.length > 0 ? (
                <span className="text-tech-amber font-semibold">{healthFlags.join(', ')}</span>
              ) : (
                <span className="text-ink-faint">None</span>
              )}
            </span>
          </div>
        </div>
      </div>

      {/* 2. Session Provenance Card */}
      <div className="bg-canvas-card border border-border-light rounded-xl p-4 shadow-card">
        <div className="flex items-center justify-between pb-3 border-b border-border-light">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-tech-blue" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-ink-primary">
              Session Provenance
            </h2>
          </div>
          <span
            className={`text-[10px] font-bold font-mono px-2 py-0.5 rounded ${
              snapshot?.completed
                ? 'bg-green-100 text-green-800'
                : 'bg-canvas-subtle text-ink-muted'
            }`}
          >
            {snapshot?.completed ? 'COMPLETED' : 'IN PROGRESS'}
          </span>
        </div>

        {/* Sensor Counter Grid */}
        <div className="grid grid-cols-3 gap-2 py-3 border-b border-border-light text-center">
          <div className="p-2 rounded bg-canvas-subtle">
            <div className="text-[10px] text-ink-muted uppercase">IMU Processed</div>
            <div className="text-sm font-bold font-mono text-ink-primary mt-0.5">
              {counters.imu_processed !== undefined ? counters.imu_processed.toLocaleString() : '—'}
            </div>
          </div>
          <div className="p-2 rounded bg-canvas-subtle">
            <div className="text-[10px] text-ink-muted uppercase">GPS Delivered</div>
            <div className="text-sm font-bold font-mono text-tech-green mt-0.5">
              {counters.gnss_delivered !== undefined ? counters.gnss_delivered.toLocaleString() : '—'}
            </div>
          </div>
          <div className="p-2 rounded bg-canvas-subtle">
            <div className="text-[10px] text-ink-muted uppercase">GPS Withheld</div>
            <div className="text-sm font-bold font-mono text-tech-amber mt-0.5">
              {counters.gnss_withheld !== undefined ? counters.gnss_withheld.toLocaleString() : '0'}
            </div>
          </div>
        </div>

        {/* Read-only Progress Track */}
        <div className="pt-3">
          <div className="flex items-center justify-between text-xs font-mono text-ink-secondary mb-1.5">
            <span>{formatTime(elapsedS)}</span>
            <span className="text-ink-muted">{formatTime(durationS)}</span>
          </div>
          <div className="w-full h-1.5 bg-canvas-subtle rounded-full overflow-hidden border border-border-light">
            <div
              className="h-full bg-tech-blue transition-all duration-200"
              style={{ width: `${progressPct.toFixed(1)}%` }}
            />
          </div>
        </div>
      </div>
    </aside>
  );
}
