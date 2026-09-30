import React, { useRef, useEffect, useState, useCallback } from 'react';
import { ZoomIn, ZoomOut, Crosshair, Layers, Compass, AlertCircle } from 'lucide-react';

export function SimulationCanvas({ snapshot }) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

  // Map view type: 'map' | 'satellite' | 'terrain'
  const [mapStyle, setMapStyle] = useState('map');

  // Viewport pan & zoom state
  const [view, setView] = useState({
    zoom: 1.0,
    panX: 0,
    panY: 0,
    autoFit: true,
  });

  const isDraggingRef = useRef(false);
  const dragStartRef = useRef({ x: 0, y: 0 });
  const viewRef = useRef(view);
  viewRef.current = view;

  const [scaleDisplay, setScaleDisplay] = useState({ metres: 50, pixels: 60 });
  const [currentCoords, setCurrentCoords] = useState({ east: null, north: null });
  const [uncertaintyCapped, setUncertaintyCapped] = useState(false);

  const handleZoom = (factor) => {
    setView((prev) => ({
      ...prev,
      zoom: Math.min(10.0, Math.max(0.1, prev.zoom * factor)),
      autoFit: false,
    }));
  };

  const handleRecenter = () => {
    setView((prev) => ({
      ...prev,
      zoom: 1.0,
      panX: 0,
      panY: 0,
      autoFit: true,
    }));
  };

  const onMouseDown = (e) => {
    isDraggingRef.current = true;
    dragStartRef.current = {
      x: e.clientX - viewRef.current.panX,
      y: e.clientY - viewRef.current.panY,
    };
  };

  const onMouseMove = (e) => {
    if (!isDraggingRef.current) return;
    setView((prev) => ({
      ...prev,
      panX: e.clientX - dragStartRef.current.x,
      panY: e.clientY - dragStartRef.current.y,
      autoFit: false,
    }));
  };

  const onMouseUp = () => {
    isDraggingRef.current = false;
  };

  const onWheel = useCallback((e) => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.15 : 0.87;
    setView((prev) => ({
      ...prev,
      zoom: Math.min(10.0, Math.max(0.1, prev.zoom * factor)),
      autoFit: false,
    }));
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    container.addEventListener('wheel', onWheel, { passive: false });
    return () => container.removeEventListener('wheel', onWheel);
  }, [onWheel]);

  // Main Canvas Render Effect
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const samples = snapshot?.samples || [];
    const current = snapshot?.current || {};
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

    // Background color based on selected map style
    if (mapStyle === 'satellite') {
      ctx.fillStyle = '#0f172a';
    } else if (mapStyle === 'terrain') {
      ctx.fillStyle = '#f8fafc';
    } else {
      ctx.fillStyle = '#ffffff';
    }
    ctx.fillRect(0, 0, width, height);

    // Compute coordinate bounds
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
      if (Number.isFinite(s.reference_east_m)) {
        minE = Math.min(minE, s.reference_east_m);
        maxE = Math.max(maxE, s.reference_east_m);
      }
      if (Number.isFinite(s.reference_north_m)) {
        minN = Math.min(minN, s.reference_north_m);
        maxN = Math.max(maxN, s.reference_north_m);
      }
    });

    if (!Number.isFinite(minE)) {
      minE = -50; maxE = 50; minN = -50; maxN = 50;
    }

    const spanE = Math.max(30, maxE - minE);
    const spanN = Math.max(30, maxN - minN);
    const centerE = (minE + maxE) / 2;
    const centerN = (minN + maxN) / 2;

    const margin = 50;
    const fitScale = Math.min(
      Math.max(40, width - margin * 2) / spanE,
      Math.max(40, height - margin * 2) / spanN
    );

    const scale = fitScale * view.zoom;
    const screenCenterX = width / 2 + view.panX;
    const screenCenterY = height / 2 + view.panY;

    const toScreenX = (e) => screenCenterX + (e - centerE) * scale;
    const toScreenY = (n) => screenCenterY - (n - centerN) * scale;

    // 1. Draw Grid
    const targetPx = 80;
    const rawStep = targetPx / scale;
    const stepSteps = [5, 10, 20, 50, 100, 200, 500, 1000];
    const metricStep = stepSteps.find((s) => s >= rawStep) || 200;

    const startE = Math.floor((centerE - (width / scale) / 2) / metricStep) * metricStep;
    const endE = Math.ceil((centerE + (width / scale) / 2) / metricStep) * metricStep;
    const startN = Math.floor((centerN - (height / scale) / 2) / metricStep) * metricStep;
    const endN = Math.ceil((centerN + (height / scale) / 2) / metricStep) * metricStep;

    ctx.strokeStyle = mapStyle === 'satellite' ? 'rgba(51, 65, 85, 0.4)' : '#f1f5f9';
    ctx.lineWidth = 1;
    ctx.font = '10px JetBrains Mono, monospace';
    ctx.fillStyle = mapStyle === 'satellite' ? '#64748b' : '#94a3b8';

    for (let e = startE; e <= endE; e += metricStep) {
      const x = toScreenX(e);
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
      ctx.fillText(`${e}m`, x + 4, height - 8);
    }

    for (let n = startN; n <= endN; n += metricStep) {
      const y = toScreenY(n);
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
      ctx.fillText(`${n}m`, 6, y - 4);
    }

    // 2. Draw Offline Reference Trajectory (Dashed Slate)
    ctx.beginPath();
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = mapStyle === 'satellite' ? '#94a3b8' : '#64748b';
    ctx.lineWidth = 2;
    let started = false;
    samples.forEach((s) => {
      if (Number.isFinite(s.reference_east_m) && Number.isFinite(s.reference_north_m)) {
        const sx = toScreenX(s.reference_east_m);
        const sy = toScreenY(s.reference_north_m);
        if (!started) {
          ctx.moveTo(sx, sy);
          started = true;
        } else {
          ctx.lineTo(sx, sy);
        }
      }
    });
    ctx.stroke();
    ctx.setLineDash([]);

    // 3. Draw Continuum Estimated Trajectory (Solid Blue)
    ctx.beginPath();
    ctx.strokeStyle = '#2563eb';
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    started = false;
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

    // 4. Draw GPS Status Points / Outage breadcrumbs
    samples.forEach((s) => {
      if (s.gnss_delivered && Number.isFinite(s.east_m) && Number.isFinite(s.north_m)) {
        const sx = toScreenX(s.east_m);
        const sy = toScreenY(s.north_m);
        ctx.beginPath();
        ctx.arc(sx, sy, 3, 0, Math.PI * 2);
        ctx.fillStyle = '#16a34a';
        ctx.fill();
      } else if (s.gnss_withheld && Number.isFinite(s.east_m) && Number.isFinite(s.north_m)) {
        const sx = toScreenX(s.east_m);
        const sy = toScreenY(s.north_m);
        ctx.beginPath();
        ctx.arc(sx, sy, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = '#dc2626';
        ctx.fill();
      }
    });

    // 5. Draw Current Vehicle Marker & Uncertainty Ring
    if (current && Number.isFinite(current.east_m) && Number.isFinite(current.north_m)) {
      const vx = toScreenX(current.east_m);
      const vy = toScreenY(current.north_m);
      const sdkState = current.state || {};
      const uncertM = sdkState.horizontal_uncertainty_m || 5.0;
      const isWithheld = !snapshot.gnss_enabled;

      if (Number.isFinite(uncertM)) {
        const rawRadiusPx = uncertM * scale;
        const maxRadiusPx = 130;
        const capped = rawRadiusPx > maxRadiusPx;
        setUncertaintyCapped(capped);

        const drawRadiusPx = Math.min(rawRadiusPx, maxRadiusPx);
        ctx.beginPath();
        ctx.arc(vx, vy, drawRadiusPx, 0, Math.PI * 2);
        ctx.fillStyle = isWithheld ? 'rgba(220, 38, 38, 0.12)' : 'rgba(37, 99, 235, 0.10)';
        ctx.fill();
        ctx.strokeStyle = isWithheld ? 'rgba(220, 38, 38, 0.7)' : 'rgba(37, 99, 235, 0.65)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash(capped ? [4, 4] : []);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // Draw sharp directional vehicle arrow
      const headingDeg = sdkState.heading_deg || 0;
      ctx.save();
      ctx.translate(vx, vy);
      ctx.rotate((headingDeg * Math.PI) / 180);

      // Vehicle center circle
      ctx.beginPath();
      ctx.arc(0, 0, 8, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.shadowColor = 'rgba(0, 0, 0, 0.2)';
      ctx.shadowBlur = 4;
      ctx.fill();

      // Heading glyph
      ctx.beginPath();
      ctx.moveTo(0, -13);
      ctx.lineTo(7, 6);
      ctx.lineTo(0, 2);
      ctx.lineTo(-7, 6);
      ctx.closePath();
      ctx.fillStyle = isWithheld ? '#dc2626' : '#2563eb';
      ctx.fill();
      ctx.restore();

      setCurrentCoords({
        east: current.east_m.toFixed(1),
        north: current.north_m.toFixed(1),
      });
    }

    // Scale Bar calculation
    const cleanDists = [5, 10, 20, 50, 100, 200, 500, 1000];
    const distMetres = cleanDists.find((d) => d >= rawStep) || 100;
    setScaleDisplay({ metres: distMetres, pixels: Math.round(distMetres * scale) });

  }, [snapshot, mapStyle, view]);

  return (
    <div className="relative w-full h-full min-h-[480px] bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm flex flex-col select-none">
      {/* Simulation Environment Header Toolbar */}
      <div className="h-12 px-4 border-b border-slate-200 bg-white flex items-center justify-between gap-3 text-xs z-10">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-blue-600" />
          <h2 className="font-bold text-slate-800 text-xs tracking-tight">Simulation Environment</h2>
        </div>

        {/* View Controls: Map View, Satellite, Terrain */}
        <div className="flex items-center gap-1 bg-slate-50 p-0.5 rounded-lg border border-slate-200">
          {['map', 'satellite', 'terrain'].map((st) => (
            <button
              key={st}
              onClick={() => setMapStyle(st)}
              className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${
                mapStyle === st
                  ? 'bg-white text-blue-600 shadow-sm font-semibold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              {st === 'map' ? 'Map View' : st === 'satellite' ? 'Satellite' : 'Terrain'}
            </button>
          ))}
        </div>
      </div>

      {/* Main Interactive Canvas */}
      <div
        ref={containerRef}
        className="relative flex-1 w-full h-full cursor-grab active:cursor-grabbing bg-white"
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
      >
        <canvas ref={canvasRef} className="w-full h-full block" />

        {/* Top-Left Coordinates HUD */}
        <div className="absolute top-3 left-3 flex flex-col gap-1.5 pointer-events-none z-10">
          <div className="px-3 py-1.5 rounded-lg bg-white/95 backdrop-blur-sm border border-slate-200 shadow-sm text-xs font-mono text-slate-600 flex items-center gap-2">
            <span>E: <strong className="text-slate-900">{currentCoords.east ?? '—'}</strong> m</span>
            <span className="text-slate-300">·</span>
            <span>N: <strong className="text-slate-900">{currentCoords.north ?? '—'}</strong> m</span>
          </div>

          {uncertaintyCapped && (
            <div className="px-2.5 py-1 rounded bg-amber-50 border border-amber-200 text-[10px] text-amber-800 font-medium flex items-center gap-1 shadow-sm">
              <AlertCircle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
              <span>Visual uncertainty capped at 130px</span>
            </div>
          )}
        </div>

        {/* Floating Map Controls at Right */}
        <div className="absolute top-3 right-3 flex flex-col gap-1 z-10">
          <button
            onClick={() => handleZoom(1.3)}
            className="w-8 h-8 rounded-lg bg-white/95 hover:bg-white text-slate-700 border border-slate-200 shadow-sm flex items-center justify-center transition-colors font-bold text-sm"
            title="Zoom In"
          >
            +
          </button>
          <button
            onClick={() => handleZoom(0.77)}
            className="w-8 h-8 rounded-lg bg-white/95 hover:bg-white text-slate-700 border border-slate-200 shadow-sm flex items-center justify-center transition-colors font-bold text-sm"
            title="Zoom Out"
          >
            −
          </button>
          <button
            onClick={handleRecenter}
            className="w-8 h-8 rounded-lg bg-white/95 hover:bg-white text-blue-600 border border-slate-200 shadow-sm flex items-center justify-center transition-colors"
            title="Recenter"
          >
            <Crosshair className="w-4 h-4" />
          </button>
        </div>

        {/* Floating Legend within Map */}
        <div className="absolute bottom-3 left-3 bg-white/95 backdrop-blur-sm border border-slate-200 rounded-xl p-2.5 shadow-sm text-[11px] text-slate-600 flex flex-wrap items-center gap-3 z-10">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span>GPS Available</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
            <span>GPS Withheld</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-1 bg-blue-600 rounded" />
            <span>Estimated Trajectory</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-slate-500 border-b border-dashed border-slate-500" />
            <span>Reference (Ground Truth)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full border border-blue-500 bg-blue-100" />
            <span>Uncertainty Ring</span>
          </div>
        </div>

        {/* Metric Scale Bar at Bottom-Right */}
        <div className="absolute bottom-3 right-3 flex flex-col items-end gap-1 bg-white/95 backdrop-blur-sm px-2.5 py-1.5 rounded-lg border border-slate-200 shadow-sm pointer-events-none z-10">
          <div
            className="h-1.5 bg-slate-800 rounded-full"
            style={{ width: `${scaleDisplay.pixels}px` }}
          />
          <span className="text-[10px] font-mono text-slate-600 font-medium">
            {scaleDisplay.metres} m
          </span>
        </div>
      </div>
    </div>
  );
}
