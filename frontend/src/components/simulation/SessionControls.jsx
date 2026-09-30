import React, { useEffect } from 'react';
import { Square, StepForward, RotateCcw, Download } from 'lucide-react';
import { EXPORT_URL } from '../../utils/constants';

export function SessionControls({
  snapshot,
  isControlInFlight,
  pause,
  step,
  restart,
  setRate,
}) {
  const isPlaying = snapshot?.playing;
  const isCompleted = snapshot?.completed;
  const currentRate = snapshot?.rate ?? 1.0;

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement?.tagName)) return;

      if (e.key === 's' || e.key === 'S') {
        e.preventDefault();
        if (!isPlaying && !isCompleted) step(25);
      } else if (e.key === 'r' || e.key === 'R') {
        e.preventDefault();
        restart();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [step, restart, isPlaying, isCompleted]);

  const handleExport = () => {
    window.location.href = EXPORT_URL;
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-3.5 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3 select-none">
      {/* Control Buttons */}
      <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
        {/* Destructive Stop Button: white background, red border/text */}
        <button
          onClick={pause}
          disabled={!isPlaying || isControlInFlight}
          className="h-9 px-3.5 rounded-xl font-medium text-xs bg-white text-rose-600 border border-rose-300 hover:bg-rose-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5 shadow-sm"
        >
          <Square className="w-3.5 h-3.5 fill-current" />
          <span>Stop Engine</span>
        </button>

        {/* Step +25 */}
        <button
          onClick={() => step(25)}
          disabled={isPlaying || isCompleted || isControlInFlight}
          className="h-9 px-3.5 rounded-xl font-medium text-xs bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5 shadow-sm"
          title="Step +25 samples (Shortcut: S)"
        >
          <StepForward className="w-3.5 h-3.5 text-blue-600" />
          <span>Step +25</span>
        </button>

        {/* Restart */}
        <button
          onClick={restart}
          disabled={isControlInFlight}
          className="h-9 px-3.5 rounded-xl font-medium text-xs bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 transition-colors flex items-center gap-1.5 shadow-sm"
          title="Restart with new session ID (Shortcut: R)"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Restart</span>
        </button>
      </div>

      {/* Speed & Export */}
      <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-400 font-medium">Speed:</span>
          <select
            value={currentRate}
            onChange={(e) => setRate(parseFloat(e.target.value))}
            disabled={isControlInFlight}
            className="h-9 px-2.5 rounded-xl border border-slate-200 bg-white text-xs font-mono font-medium text-slate-800 focus:outline-none focus:border-blue-600 shadow-sm"
          >
            <option value="0.5">0.5×</option>
            <option value="1">1.0×</option>
            <option value="2">2.0×</option>
            <option value="4">4.0×</option>
          </select>
        </div>

        <button
          onClick={handleExport}
          className="h-9 px-3.5 rounded-xl text-xs font-medium bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 hover:text-slate-900 shadow-sm transition-colors flex items-center gap-1.5"
        >
          <Download className="w-3.5 h-3.5 text-blue-600" />
          <span>Export Session (JSON)</span>
        </button>
      </div>
    </div>
  );
}
