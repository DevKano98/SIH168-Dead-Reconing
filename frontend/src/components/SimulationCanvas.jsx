import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Layers, ZoomIn, ZoomOut, Maximize2, Crosshair, AlertCircle } from 'lucide-react';

export function SimulationCanvas({ snapshot }) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

  // Layer toggles
  const [layers, setLayers] = useState({
    estimate: true,
    reference: true,
    uncertainty: true,
    grid: true,
  });

  // Viewport transform
  const [view, setView] = useState({
    zoom: 1.0,
    panX: 0,
    panY: 0,
    autoFit: true,
    scalePixelsPerMetre: 1.0,
  });

  const isDraggingRef = useRef(false);
  const dragStartRef = useRef({ x: 0, y: 0 });
  const viewRef = useRef(view);
  viewRef.current = view;

  const [uncertaintyCapped, setUncertaintyCapped] = useState(false);
  const [currentCoords, setCurrentCoords] = useState({ east: null, north: null });
  const [scaleDisplay, setScaleDisplay] = useState({ metres: 50, pixels: 60 });

  const toggleLayer = (layerKey) => {
    setLayers((prev) => ({ ...prev, [layerKey]: !prev[layerKey] }));
  };

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

  // Mouse pan handlers
  const onMouseDown = (e) => {
    isDraggingRef.current = true;
    dragStartRef.current = {
      x: e.clientX - viewRef.current.panX,
      y: e.clientY - viewRef.current.panY,
    };
  };

  const onMouseMove = (e) => {
    if (!isDraggingRef.current) return;
    const newPanX = e.clientX - dragStartRef.current.x;
    const newPanY = e.clientY - dragStartRef.current.y;
    setView((prev) => ({
      ...prev,
      panX: newPanX,
      panY: newPanY,
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
    return () => {
      container.removeEventListener('wheel', onWheel);
    };
  }, [onWheel]);

  // Main Canvas Render Loop
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

    // Clear background: pale engineering instrument surface
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, width, height);

    // Coordinate bounds calculation
    let minE = Infinity, maxE = -Infinity, minN = Infinity, maxN = -Infinity;
    samples.forEach((s) => {
      if (s.east_m !== null && s.east_m !== undefined && Number.isFinite(s.east_m)) {
        minE = Math.min(minE, s.east_m);
        maxE = Math.max(maxE, s.east_m);
      }
      if (s.north_m !== null && s.north_m !== undefined && Number.isFinite(s.north_m)) {
        minN = Math.min(minN, s.north_m);
        maxN = Math.max(maxN, s.north_m);
      }
      if (layers.reference && s.reference_east_m !== null && Number.isFinite(s.reference_east_m)) {
        minE = Math.min(minE, s.reference_east_m);
        maxE = Math.max(maxE, s.reference_east_m);
      }
      if (layers.reference && s.reference_north_m !== null && Number.isFinite(s.reference_north_m)) {
        minN = Math.min(minN, s.reference_north_m);
        maxN = Math.max(maxN, s.reference_north_m);
      }
    });

    if (!Number.isFinite(minE)) {
      minE = -50;
      maxE = 50;
      minN = -50;
      maxN = 50;
    }

    const spanE = Math.max(25, maxE - minE);
    const spanN = Math.max(25, maxN - minN);
    const centerE = (minE + maxE) / 2;
    const centerN = (minN + maxN) / 2;

    const margin = 48;
    const availW = Math.max(40, width - margin * 2);
    const availH = Math.max(40, height - margin * 2);
    const fitScale = Math.min(availW / spanE, availH / spanN);

    const scale = fitScale * view.zoom;
    const screenCenterX = width / 2 + view.panX;
    const screenCenterY = height / 2 + view.panY;

    // Coordinate transforms: East (+x), North (+y points upward in ENU, so inverted on canvas)
    const toScreenX = (e) => screenCenterX + (e - centerE) * scale;
    const toScreenY = (n) => screenCenterY - (n - centerN) * scale;

    // 1. Draw Precision Metric Grid
    if (layers.grid) {
      const targetPixelStep = 80;
      const rawStepMetres = targetPixelStep / scale;
      const steps = [5, 10, 20, 50, 100, 200, 500, 1000];
      const metricStep = steps.find((s) => s >= rawStepMetres) || 200;

      const startE = Math.floor((centerE - (width / scale) / 2) / metricStep) * metricStep;
      const endE = Math.ceil((centerE + (width / scale) / 2) / metricStep) * metricStep;
      const startN = Math.floor((centerN - (height / scale) / 2) / metricStep) * metricStep;
      const endN = Math.ceil((centerN + (height / scale) / 2) / metricStep) * metricStep;

      ctx.strokeStyle = '#F1F5F9';
      ctx.lineWidth = 1;
      ctx.font = '10px ui-monospace, SFMono-Regular, Menlo, monospace';
      ctx.fillStyle = '#94A3B8';

      // Vertical grid lines (East)
      for (let e = startE; e <= endE; e += metricStep) {
        const x = toScreenX(e);
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
        ctx.fillText(`${e > 0 ? '+' : ''}${Math.round(e)}m`, x + 4, height - 8);
      }

      // Horizontal grid lines (North)
      for (let n = startN; n <= endN; n += metricStep) {
        const y = toScreenY(n);
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
        ctx.fillText(`${n > 0 ? '+' : ''}${Math.round(n)}m`, 6, y - 4);
      }

      // Draw local origin cross if in view
      const ox = toScreenX(0);
      const oy = toScreenY(0);
      if (ox >= 0 && ox <= width && oy >= 0 && oy <= height) {
        ctx.strokeStyle = '#CBD5E1';
        ctx.setLineDash([2, 2]);
        ctx.beginPath();
        ctx.moveTo(ox, 0);
        ctx.lineTo(ox, height);
        ctx.moveTo(0, oy);
        ctx.lineTo(width, oy);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    }

    // 2. Draw Offline Reference Trajectory (Dashed Slate)
    if (layers.reference) {
      ctx.beginPath();
      ctx.setLineDash([4, 4]);
      ctx.strokeStyle = '#64748B';
      ctx.lineWidth = 2;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      let started = false;
      samples.forEach((s) => {
        if (s.reference_east_m !== null && s.reference_north_m !== null && Number.isFinite(s.reference_east_m)) {
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
    }

    // 3. Draw Continuum Estimated Trajectory (Solid Blue)
    if (layers.estimate) {
      ctx.beginPath();
      ctx.strokeStyle = '#2563EB';
      ctx.lineWidth = 3;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      let started = false;
      samples.forEach((s) => {
        if (s.east_m !== null && s.north_m !== null && Number.isFinite(s.east_m)) {
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
    }

    // 4. Draw Current Vehicle Marker & Uncertainty Ring
    if (current && current.east_m !== null && current.north_m !== null && Number.isFinite(current.east_m)) {
      const vx = toScreenX(current.east_m);
      const vy = toScreenY(current.north_m);
      const sdkState = current.state || {};
      const uncertM = sdkState.horizontal_uncertainty_m || 5.0;
      const isWithheld = !snapshot.gnss_enabled;

      // Uncertainty Ring
      if (layers.uncertainty && Number.isFinite(uncertM)) {
        const rawRadiusPx = uncertM * scale;
        const maxRadiusPx = 130;
        const capped = rawRadiusPx > maxRadiusPx;
        setUncertaintyCapped(capped);

        const drawRadiusPx = Math.min(rawRadiusPx, maxRadiusPx);

        ctx.beginPath();
        ctx.arc(vx, vy, drawRadiusPx, 0, Math.PI * 2);
        ctx.fillStyle = isWithheld ? 'rgba(217, 119, 6, 0.12)' : 'rgba(37, 99, 235, 0.10)';
        ctx.fill();

        ctx.strokeStyle = isWithheld ? 'rgba(217, 119, 6, 0.75)' : 'rgba(37, 99, 235, 0.65)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash(capped ? [4, 4] : []);
        ctx.stroke();
        ctx.setLineDash([]);
      } else {
        setUncertaintyCapped(false);
      }

      // Draw Vehicle Heading Glyphs
      const headingDeg = sdkState.heading_deg || 0;
      const headingRad = (headingDeg * Math.PI) / 180;

      ctx.save();
      ctx.translate(vx, vy);
      ctx.rotate(headingRad);

      // Outer halo
      ctx.beginPath();
      ctx.arc(0, 0, 9, 0, Math.PI * 2);
      ctx.fillStyle = '#FFFFFF';
      ctx.shadowColor = 'rgba(15, 23, 42, 0.25)';
      ctx.shadowBlur = 4;
      ctx.fill();

      // Sharp directional arrowhead
      ctx.beginPath();
      ctx.moveTo(0, -14);
      ctx.lineTo(8, 7);
      ctx.lineTo(0, 3);
      ctx.lineTo(-8, 7);
      ctx.closePath();
      ctx.fillStyle = isWithheld ? '#D97706' : '#2563EB';
      ctx.shadowColor = 'rgba(0, 0, 0, 0.15)';
      ctx.shadowBlur = 2;
      ctx.fill();
      ctx.restore();

      setCurrentCoords({
        east: current.east_m.toFixed(1),
        north: current.north_m.toFixed(1),
      });
    }

    // Dynamic scale bar update
    const targetPx = 80;
    const rawDist = targetPx / scale;
    const cleanDists = [5, 10, 20, 50, 100, 200, 500, 1000];
    const distMetres = cleanDists.find((d) => d >= rawDist) || 100;
    const pixelWidth = distMetres * scale;
    setScaleDisplay({ metres: distMetres, pixels: Math.round(pixelWidth) });

  }, [snapshot, layers, view]);

  return (
    <div className="relative w-full h-full min-h-[480px] bg-canvas-card rounded-xl border border-border-light overflow-hidden shadow-card flex flex-col select-none">
      {/* Top Toolbar */}
      <div className="h-11 px-3.5 border-b border-border-light bg-canvas-card flex items-center justify-between gap-3 text-xs z-10">
        <div className="flex items-center gap-1 sm:gap-2">
          <span className="text-[11px] font-semibold text-ink-muted uppercase tracking-wider hidden sm:inline mr-1">
            Layers
          </span>
          <button
            onClick={() => toggleLayer('estimate')}
            className={`px-2.5 py-1 rounded text-xs font-medium border flex items-center gap-1.5 transition-colors ${
              layers.estimate
                ? 'bg-tech-blue-subtle text-tech-blue border-tech-blue-border'
                : 'bg-canvas-subtle text-ink-muted border-border-light hover:text-ink-primary'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-tech-blue" />
            <span>Estimate</span>
          </button>

          <button
            onClick={() => toggleLayer('reference')}
            className={`px-2.5 py-1 rounded text-xs font-medium border flex items-center gap-1.5 transition-colors ${
              layers.reference
                ? 'bg-slate-100 text-slate-700 border-slate-300'
                : 'bg-canvas-subtle text-ink-muted border-border-light hover:text-ink-primary'
            }`}
          >
            <span className="w-2 h-0.5 bg-slate-500 rounded" />
            <span>Reference (Offline)</span>
          </button>

          <button
            onClick={() => toggleLayer('uncertainty')}
            className={`px-2.5 py-1 rounded text-xs font-medium border flex items-center gap-1.5 transition-colors ${
              layers.uncertainty
                ? 'bg-amber-50 text-amber-800 border-amber-200'
                : 'bg-canvas-subtle text-ink-muted border-border-light hover:text-ink-primary'
            }`}
          >
            <span className="w-2 h-2 rounded-full border border-amber-600 bg-amber-100" />
            <span className="hidden md:inline">Uncertainty</span>
          </button>

          <button
            onClick={() => toggleLayer('grid')}
            className={`px-2 py-1 rounded text-xs font-medium border transition-colors ${
              layers.grid
                ? 'bg-canvas-subtle text-ink-primary border-border-light'
                : 'text-ink-muted border-transparent hover:text-ink-primary'
            }`}
          >
            Grid
          </button>
        </div>

        {/* Zoom & Recenter Controls */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => handleZoom(1.3)}
            className="p-1.5 rounded hover:bg-canvas-subtle text-ink-secondary hover:text-ink-primary border border-border-light transition-colors"
            title="Zoom In (+)"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => handleZoom(0.77)}
            className="p-1.5 rounded hover:bg-canvas-subtle text-ink-secondary hover:text-ink-primary border border-border-light transition-colors"
            title="Zoom Out (-)"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleRecenter}
            className="px-2 py-1 rounded hover:bg-canvas-subtle text-ink-secondary hover:text-ink-primary border border-border-light transition-colors flex items-center gap-1"
            title="Recenter and Fit View"
          >
            <Crosshair className="w-3.5 h-3.5 text-tech-blue" />
            <span className="hidden sm:inline">Recenter</span>
          </button>
        </div>
      </div>

      {/* Main Interactive Canvas Area */}
      <div
        ref={containerRef}
        className="relative flex-1 w-full h-full cursor-grab active:cursor-grabbing bg-canvas-card"
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
      >
        <canvas ref={canvasRef} className="w-full h-full block" />

        {/* Top-Left Coordinate HUD */}
        <div className="absolute top-3 left-3 flex flex-col gap-1.5 pointer-events-none z-10">
          <div className="px-2.5 py-1 rounded-md bg-white/95 backdrop-blur-sm border border-border-light shadow-sm text-xs font-mono text-ink-secondary flex items-center gap-2">
            <span>E: <strong className="text-ink-primary font-semibold">{currentCoords.east ?? '—'}</strong> m</span>
            <span className="text-border-medium">·</span>
            <span>N: <strong className="text-ink-primary font-semibold">{currentCoords.north ?? '—'}</strong> m</span>
          </div>

          {uncertaintyCapped && (
            <div className="px-2.5 py-1 rounded-md bg-tech-amber-subtle border border-tech-amber-border text-[11px] text-tech-amber font-medium flex items-center gap-1.5 shadow-sm">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
              <span>Visual uncertainty capped at 130px; numeric uncertainty is authoritative.</span>
            </div>
          )}
        </div>

        {/* Bottom Scale Bar & Local Frame Provenance */}
        <div className="absolute bottom-3 left-3 right-3 flex items-end justify-between pointer-events-none z-10">
          <div className="text-[11px] text-ink-muted bg-white/90 backdrop-blur-sm px-2.5 py-1 rounded border border-border-light hidden sm:block max-w-sm">
            <strong>Local Metric Frame (East/North)</strong>: Integrated from IO-VNBD sensor recording.
          </div>

          <div className="flex flex-col items-end gap-1 bg-white/95 backdrop-blur-sm px-2.5 py-1.5 rounded-md border border-border-light shadow-sm">
            <div
              className="h-1.5 bg-ink-primary rounded-full"
              style={{ width: `${scaleDisplay.pixels}px` }}
            />
            <span className="text-[10px] font-mono text-ink-secondary font-medium">
              {scaleDisplay.metres} m
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
