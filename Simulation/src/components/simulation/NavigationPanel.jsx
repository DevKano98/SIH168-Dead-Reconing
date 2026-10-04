import React from 'react';
import { Gauge, Clock, ShieldAlert, Cpu } from 'lucide-react';
import { formatDuration, formatSpeed, fmtNum, cardinalFromDeg } from '../../utils/formatters';

export function NavigationPanel({ snapshot }) {
  const current = snapshot?.current || {};
  const sdkState = current?.state || {};

  // Tracking Mode & State Badge
  let stateBadge = 'UNINITIALIZED';
  if (snapshot?.completed) {
    stateBadge = 'WAITING';
  } else if (snapshot?.playing) {
    stateBadge = 'RUNNING';
  } else if (snapshot?.index > 0) {
    stateBadge = 'PAUSED';
  }

  const badgeStyles = {
    RUNNING: 'bg-emerald-50 text-emerald-700 border-emerald-200 animate-pulse',
    PAUSED: 'bg-amber-50 text-amber-700 border-amber-200',
    WAITING: 'bg-slate-100 text-slate-700 border-slate-200',
    ERROR: 'bg-rose-50 text-rose-700 border-rose-200',
    UNINITIALIZED: 'bg-slate-100 text-slate-500 border-slate-200',
  };

  const { kmh, mps } = formatSpeed(sdkState.speed_mps);
  const elapsedStr = formatDuration(current?.elapsed_s || 0);

  const measuredError = current?.error_m;
  const estimatedUncertainty = sdkState.horizontal_uncertainty_m;
  const headingDeg = sdkState.heading_deg;
  const cardinal = cardinalFromDeg(headingDeg);

  const lastDecision = sdkState.last_gnss_decision || 'NONE';
  const acceptedAge = sdkState.last_accepted_gnss_age_s;
  const healthFlags = sdkState.health_flags || [];

  return (
    <aside className="w-full bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-5 select-none">
      {/* Header: Navigation State, Badge, & Timer */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800">
            Navigation State
          </h2>
          <div className="flex items-center gap-1.5 text-xs font-mono text-slate-500 mt-1">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span>{elapsedStr}</span>
          </div>
        </div>

        <span
          className={`px-2.5 py-1 rounded-full text-[11px] font-bold font-mono tracking-wider border ${
            badgeStyles[stateBadge] || badgeStyles.UNINITIALIZED
          }`}
        >
          {stateBadge}
        </span>
      </div>

      {/* Main Metric: Vehicle Speed */}
      <div className="py-2">
        <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
          Vehicle Speed
        </div>
        <div className="flex items-baseline gap-2 mt-1">
          <span className="text-5xl font-extrabold font-mono tracking-tight text-slate-900">
            {kmh}
          </span>
          <span className="text-base font-bold text-slate-400 uppercase">km/h</span>
        </div>
        <div className="text-xs font-mono text-slate-500 mt-0.5">
          {mps !== '—' ? `${mps} m/s` : '— m/s'}
        </div>
      </div>

      {/* Two Important Cards: Position Error & Estimated Uncertainty */}
      <div className="grid grid-cols-2 gap-3 pt-1">
        <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
          <div className="text-[11px] font-medium text-slate-500">Position Error</div>
          <div className="text-xl font-bold font-mono text-slate-900 mt-1">
            {fmtNum(measuredError, 1)} m
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5 leading-tight">
            Distance to reference
          </div>
        </div>

        <div className="p-3 rounded-xl bg-blue-50/50 border border-blue-100">
          <div className="text-[11px] font-medium text-blue-700">Estimated Uncertainty</div>
          <div className="text-xl font-bold font-mono text-blue-800 mt-1">
            {fmtNum(estimatedUncertainty, 1, '±—')} m
          </div>
          <div className="text-[10px] text-blue-600/70 mt-0.5 leading-tight">
            Horizontal bound · 1σ
          </div>
        </div>
      </div>

      {/* Properties List */}
      <div className="pt-2 divide-y divide-slate-100 text-xs">
        <div className="flex items-center justify-between py-2">
          <span className="text-slate-500">Vehicle Heading</span>
          <span className="font-mono text-slate-900 font-medium">
            {fmtNum(headingDeg, 1)}° {cardinal ? `(${cardinal})` : ''}
          </span>
        </div>

        <div className="flex items-center justify-between py-2">
          <span className="text-slate-500">GPS Input Switch</span>
          <span
            className={`font-semibold ${
              snapshot?.gnss_enabled ? 'text-emerald-600' : 'text-rose-600'
            }`}
          >
            {snapshot?.gnss_enabled ? 'Delivering' : 'Withheld (Outage)'}
          </span>
        </div>

        <div className="flex items-center justify-between py-2">
          <span className="text-slate-500">GPS Delivery Event</span>
          <span className="font-mono text-slate-800">
            {current?.gnss_withheld ? (
              <span className="text-rose-600 font-semibold">Withheld</span>
            ) : current?.gnss_delivered ? (
              <span className="text-emerald-600 font-semibold">Fix Delivered</span>
            ) : (
              <span className="text-slate-400">Idle</span>
            )}
          </span>
        </div>

        <div className="flex items-center justify-between py-2">
          <span className="text-slate-500">Last GNSS Decision</span>
          <span className="font-mono font-medium text-slate-900">{lastDecision}</span>
        </div>

        <div className="flex items-center justify-between py-2">
          <span className="text-slate-500">Accepted GNSS Age</span>
          <span className="font-mono text-slate-800">
            {fmtNum(acceptedAge, 1)} s
          </span>
        </div>

        <div className="flex items-center justify-between py-2">
          <span className="text-slate-500">Active Health Flags</span>
          <span className="font-mono text-slate-800">
            {healthFlags.length > 0 ? (
              <span className="text-amber-600 font-semibold">{healthFlags.join(', ')}</span>
            ) : (
              <span className="text-slate-400">None</span>
            )}
          </span>
        </div>
      </div>
    </aside>
  );
}
