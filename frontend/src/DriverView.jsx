import React, { useRef, useEffect } from 'react';
import { useSimulation } from './hooks/useSimulation';
import { Navigation, Play, Pause, StepForward, Satellite, RotateCcw, ArrowLeft, ShieldAlert } from 'lucide-react';

export function DriverView() {
  const {
    snapshot,
    connectionStatus,
    play,
    pause,
    togglePlay,
    step,
    toggleGnss,
    restart,
  } = useSimulation(200);

  const canvasRef = useRef(null);

  const current = snapshot?.current || {};
  const sdkState = current?.state || {};

  const speedMps = sdkState.speed_mps;
  const speedKmh = speedMps !== null && speedMps !== undefined && Number.isFinite(speedMps)
    ? Math.round(speedMps * 3.6)
    : 0;

  const headingDeg = sdkState.heading_deg;
  const headingNorm = headingDeg !== null && headingDeg !== undefined && Number.isFinite(headingDeg)
    ? Math.round((headingDeg % 360 + 360) % 360)
    : 0;

  const cardinalDirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'N'];
  const cardinalStr = headingDeg !== null && Number.isFinite(headingDeg)
    ? cardinalDirs[Math.round(headingNorm / 45)]
    : '—';

  const trackingMode = sdkState.tracking_mode || 'UNINITIALIZED';
  const uncertaintyM = sdkState.horizontal_uncertainty_m;
  const isWithheld = !snapshot?.gnss_enabled;
  const elapsedS = current?.elapsed_s || 0;

  const formatTime = (seconds) => {
    if (!Number.isFinite(seconds)) return '00:00.0';
    const s = Math.max(0, seconds);
    const mins = Math.floor(s / 60);
    const secs = (s % 60).toFixed(1);
    return `${String(mins).padStart(2, '0')}:${secs.padStart(4, '0')}`;
  };

  // Mini canvas rendering
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const samples = snapshot?.samples || [];
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;

    if (canvas.width !== Math.round(width * dpr) || canvas.height !== Math.round(height * dpr)) {
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
    }

    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    ctx.fillStyle = '#F8FAFC';
    ctx.fillRect(0, 0, width, height);

    if (samples.length < 2) return;

    let minE = Infinity, maxE = -Infinity, minN = Infinity, maxN = -Infinity;
    samples.forEach((s) => {
      if (Number.isFinite(s.east_m)) {
        minE = Math.min(minE, s.east_m);
        maxE = Math.max(maxE, s.east_m);
      }
      if (Number.isFinite(s.north_m)) {
        minN = Math.min(minN, s.north_m);
        maxN = Math.max(maxN, s.north_m);
      }
    });

    if (!Number.isFinite(minE)) {
      minE = -30; maxE = 30; minN = -30; maxN = 30;
    }

    const spanE = Math.max(20, maxE - minE);
    const spanN = Math.max(20, maxN - minN);
    const centerE = (minE + maxE) / 2;
    const centerN = (minN + maxN) / 2;

    const margin = 24;
    const scale = Math.min((width - margin * 2) / spanE, (height - margin * 2) / spanN);
    const toScreenX = (e) => width / 2 + (e - centerE) * scale;
    const toScreenY = (n) => height / 2 - (n - centerN) * scale;

    // Draw estimated path
    ctx.beginPath();
    ctx.strokeStyle = '#2563EB';
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    let started = false;
    samples.forEach((s) => {
      if (Number.isFinite(s.east_m) && Number.isFinite(s.north_m)) {
        const sx = toScreenX(s.east_m);
        const sy = toScreenY(s.north_m);
        if (!started) {
          ctx.moveTo(sx, sy);
          started = true;
        } else {
          ctx.lineTo(sx, sy);
        }
      }
    });
    ctx.stroke();

    // Draw current vehicle marker
    if (current && Number.isFinite(current.east_m) && Number.isFinite(current.north_m)) {
      const vx = toScreenX(current.east_m);
      const vy = toScreenY(current.north_m);

      // Uncertainty circle
      if (Number.isFinite(uncertaintyM)) {
        const rad = Math.min(60, uncertaintyM * scale);
        ctx.beginPath();
        ctx.arc(vx, vy, rad, 0, Math.PI * 2);
        ctx.fillStyle = isWithheld ? 'rgba(217, 119, 6, 0.15)' : 'rgba(37, 99, 235, 0.12)';
        ctx.fill();
        ctx.strokeStyle = isWithheld ? '#D97706' : '#2563EB';
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      ctx.save();
      ctx.translate(vx, vy);
      ctx.rotate((headingNorm * Math.PI) / 180);
      ctx.beginPath();
      ctx.moveTo(0, -10);
      ctx.lineTo(6, 6);
      ctx.lineTo(0, 2);
      ctx.lineTo(-6, 6);
      ctx.closePath();
      ctx.fillStyle = isWithheld ? '#D97706' : '#2563EB';
      ctx.fill();
      ctx.restore();
    }
  }, [snapshot, current, uncertaintyM, isWithheld, headingNorm]);

  return (
    <div className="min-h-screen bg-canvas-base flex flex-col items-center justify-center p-2 sm:p-6 font-sans">
      <div className="w-full max-w-md bg-canvas-card border border-border-light rounded-3xl shadow-panel overflow-hidden flex flex-col">
        {/* Top Header */}
        <header className="px-5 py-4 border-b border-border-light flex items-center justify-between bg-canvas-card">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-tech-blue flex items-center justify-center text-white">
              <Navigation className="w-3.5 h-3.5 transform -rotate-45" />
            </div>
            <div>
              <span className="font-bold text-sm text-ink-primary">Continuum</span>
              <span className="text-xs font-semibold text-tech-blue ml-1.5 uppercase tracking-wider">HUD</span>
            </div>
          </div>

          <a
            href="/"
            className="flex items-center gap-1 px-3 py-1 rounded-md text-xs font-medium text-ink-secondary bg-canvas-subtle hover:bg-canvas-subtle/80 border border-border-light transition-colors"
          >
            <ArrowLeft className="w-3 h-3" />
            <span>Studio</span>
          </a>
        </header>

        {/* Hero Speed & Compass */}
        <div className="p-6 text-center border-b border-border-light bg-gradient-to-b from-white to-canvas-subtle/30">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold font-mono uppercase tracking-wider mb-3 border">
            {trackingMode === 'DEAD_RECKONING' ? (
              <span className="text-tech-amber border-tech-amber-border bg-tech-amber-subtle px-2 py-0.5 rounded-full flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-tech-amber animate-ping" />
                DEAD RECKONING
              </span>
            ) : trackingMode === 'GNSS_AIDED' ? (
              <span className="text-tech-green border-green-200 bg-tech-green-subtle px-2 py-0.5 rounded-full">
                GNSS AIDED
              </span>
            ) : (
              <span className="text-ink-muted border-border-light bg-canvas-subtle px-2 py-0.5 rounded-full">
                {trackingMode}
              </span>
            )}
          </div>

          <div className="flex items-baseline justify-center gap-2">
            <span className="text-7xl font-extrabold font-mono tracking-tight text-ink-primary">
              {speedKmh}
            </span>
            <span className="text-lg font-bold text-ink-muted uppercase">km/h</span>
          </div>

          <div className="mt-3 flex items-center justify-center gap-4 text-xs font-mono text-ink-secondary">
            <span className="font-semibold text-ink-primary text-sm">{cardinalStr}</span>
            <span className="text-border-medium">·</span>
            <span>{headingNorm}° Bearing</span>
            <span className="text-border-medium">·</span>
            <span>{formatTime(elapsedS)}</span>
          </div>
        </div>

        {/* Live Mini Canvas */}
        <div className="relative h-48 w-full border-b border-border-light bg-canvas-base">
          <canvas ref={canvasRef} className="w-full h-full block" />
          <div className="absolute top-2 left-2 text-[10px] font-mono font-medium text-ink-muted bg-white/90 backdrop-blur-sm px-2 py-0.5 rounded border border-border-light">
            Local ENU Course
          </div>
        </div>

        {/* Telemetry Status Strip */}
        <div className="grid grid-cols-2 divide-x divide-border-light border-b border-border-light bg-canvas-card text-center py-3">
          <div>
            <div className="text-[10px] uppercase font-semibold text-ink-muted">Uncertainty</div>
            <div className="text-base font-bold font-mono text-tech-blue mt-0.5">
              {Number.isFinite(uncertaintyM) ? `±${uncertaintyM.toFixed(1)} m` : '±— m'}
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase font-semibold text-ink-muted">GNSS Input</div>
            <div
              className={`text-base font-bold font-mono mt-0.5 ${
                isWithheld ? 'text-tech-amber' : 'text-tech-green'
              }`}
            >
              {isWithheld ? 'Withheld' : 'Delivering'}
            </div>
          </div>
        </div>

        {/* Touch Transport Controls */}
        <div className="p-4 bg-canvas-card flex items-center justify-between gap-2">
          <button
            onClick={togglePlay}
            className={`flex-1 py-3 rounded-xl font-bold text-sm flex items-center justify-center gap-2 shadow-sm transition-all ${
              snapshot?.playing
                ? 'bg-canvas-subtle border border-border-medium text-ink-primary'
                : 'bg-tech-blue text-white hover:bg-blue-700'
            }`}
          >
            {snapshot?.playing ? (
              <>
                <Pause className="w-4 h-4" />
                <span>Pause</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>{snapshot?.index > 0 ? 'Resume' : 'Start'}</span>
              </>
            )}
          </button>

          <button
            onClick={() => step(25)}
            disabled={snapshot?.playing}
            className="p-3 rounded-xl bg-canvas-subtle border border-border-light text-ink-secondary hover:text-ink-primary disabled:opacity-40 transition-colors"
            title="Step +25"
          >
            <StepForward className="w-5 h-5" />
          </button>

          <button
            onClick={toggleGnss}
            className={`p-3 rounded-xl border transition-colors ${
              isWithheld
                ? 'bg-tech-amber text-white border-amber-600'
                : 'bg-canvas-subtle text-ink-secondary border-border-light hover:text-tech-amber'
            }`}
            title="Toggle GPS Outage"
          >
            <Satellite className="w-5 h-5" />
          </button>

          <button
            onClick={restart}
            className="p-3 rounded-xl bg-canvas-subtle border border-border-light text-ink-secondary hover:text-ink-primary transition-colors"
            title="Restart"
          >
            <RotateCcw className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
