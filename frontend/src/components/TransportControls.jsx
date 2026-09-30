import React, { useEffect } from 'react';
import { Play, Pause, StepForward, Satellite, RotateCcw, Download, Check, Sparkles } from 'lucide-react';
import { EXPORT_SESSION_URL } from '../services/simulationApi';

export function TransportControls({
  snapshot,
  isControlInFlight,
  play,
  pause,
  togglePlay,
  step,
  toggleGnss,
  restart,
  setRate,
}) {
  const isPlaying = snapshot?.playing;
  const isCompleted = snapshot?.completed;
  const index = snapshot?.index || 0;
  const gnssEnabled = snapshot?.gnss_enabled ?? true;
  const currentRate = snapshot?.rate ?? 1.0;

  // Keyboard shortcut listener
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement?.tagName)) return;

      if (e.code === 'Space') {
        e.preventDefault();
        togglePlay();
      } else if (e.key === 'g' || e.key === 'G') {
        e.preventDefault();
        toggleGnss();
      } else if (e.key === 's' || e.key === 'S') {
        e.preventDefault();
        if (!isPlaying && !isCompleted) step(25);
      } else if (e.key === 'r' || e.key === 'R') {
        e.preventDefault();
        restart();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [togglePlay, toggleGnss, step, restart, isPlaying, isCompleted]);

  const handleExport = () => {
    window.location.href = EXPORT_SESSION_URL;
  };

  return (
    <div className="bg-canvas-card border border-border-light rounded-xl p-3.5 shadow-card flex flex-col sm:flex-row items-center justify-between gap-3 select-none">
      {/* Primary Action Buttons */}
      <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
        {/* Play / Pause / Start Button */}
        <button
          onClick={togglePlay}
          disabled={isCompleted || isControlInFlight}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold text-xs transition-all shadow-sm ${
            isCompleted
              ? 'bg-canvas-subtle text-ink-muted border border-border-light cursor-not-allowed'
              : isPlaying
              ? 'bg-canvas-card text-ink-primary border border-border-medium hover:bg-canvas-subtle'
              : 'bg-tech-blue hover:bg-blue-700 text-white'
          }`}
          title="Shortcut: Space"
        >
          {isCompleted ? (
            <>
              <Check className="w-4 h-4 text-tech-green" />
              <span>Session Completed</span>
            </>
          ) : isPlaying ? (
            <>
              <Pause className="w-4 h-4" />
              <span>Pause Engine</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              <span>{index > 0 ? 'Resume Engine' : 'Start Engine'}</span>
            </>
          )}
        </button>

        {/* Step Forward Button */}
        <button
          onClick={() => step(25)}
          disabled={isPlaying || isCompleted || isControlInFlight}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg font-medium text-xs bg-canvas-card border border-border-light hover:bg-canvas-subtle disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-ink-primary shadow-sm"
          title="Step +25 samples forward (Shortcut: S)"
        >
          <StepForward className="w-3.5 h-3.5 text-tech-blue" />
          <span>Step +25</span>
        </button>

        {/* GPS Outage Toggle Button */}
        <button
          onClick={toggleGnss}
          disabled={isControlInFlight}
          className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg font-semibold text-xs border transition-all shadow-sm ${
            gnssEnabled
              ? 'bg-canvas-card border-border-light text-ink-primary hover:border-tech-amber hover:text-tech-amber'
              : 'bg-tech-amber text-white border-amber-600 shadow-sm'
          }`}
          title="Toggle GNSS availability (Shortcut: G)"
        >
          <Satellite className="w-3.5 h-3.5" />
          <span>{gnssEnabled ? 'Withhold GPS (Simulate Tunnel)' : 'Restore GPS (Deliver Fixes)'}</span>
        </button>

        {/* Restart Button */}
        <button
          onClick={restart}
          disabled={isControlInFlight}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg font-medium text-xs bg-canvas-card border border-border-light hover:bg-canvas-subtle transition-colors text-ink-secondary hover:text-ink-primary shadow-sm"
          title="Restart experiment with new session ID (Shortcut: R)"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Restart</span>
        </button>
      </div>

      {/* Meta Controls (Rate & Export) */}
      <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
        <div className="flex items-center gap-2 text-xs">
          <span className="text-ink-muted font-medium">Rate:</span>
          <select
            value={currentRate}
            onChange={(e) => setRate(parseFloat(e.target.value))}
            disabled={isControlInFlight}
            className="px-2.5 py-1.5 rounded-lg border border-border-light bg-canvas-card text-xs font-mono font-medium text-ink-primary focus:outline-none focus:border-tech-blue shadow-sm"
          >
            <option value="0.5">0.5×</option>
            <option value="1">1.0×</option>
            <option value="2">2.0×</option>
            <option value="4">4.0×</option>
          </select>
        </div>

        <button
          onClick={handleExport}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-canvas-card border border-border-light hover:bg-canvas-subtle text-ink-secondary hover:text-ink-primary shadow-sm transition-colors"
          title="Download full session JSON snapshot"
        >
          <Download className="w-3.5 h-3.5 text-tech-blue" />
          <span>Export JSON</span>
        </button>
      </div>
    </div>
  );
}
