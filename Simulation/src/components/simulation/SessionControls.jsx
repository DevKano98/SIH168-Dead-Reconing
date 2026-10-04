import React, { useEffect } from 'react';
import { Square, StepForward, RotateCcw, Download, Dices, Zap } from 'lucide-react';
import { EXPORT_URL } from '../../utils/constants';

export function SessionControls({
  snapshot,
  isControlInFlight,
  pause,
  step,
  restart,
  randomize,
  toggleNoise,
  setScenario,
  setRate,
}) {
  const isPlaying = snapshot?.playing;
  const isCompleted = snapshot?.completed;
  const currentRate = snapshot?.rate ?? 1.0;
  const noiseEnabled = snapshot?.noise_enabled ?? false;
  const currentRunId = snapshot?.run_id || 'Vtb02';

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

  const scenarioOptions = [
    { id: 'Vtb02', label: 'Vtb02 (Default Blackout)' },
    { id: 'Vtb01', label: 'Vtb01 (Long Urban Route)' },
    { id: 'Vtb03', label: 'Vtb03 (Highway Cruise)' },
    { id: 'Vtb04', label: 'Vtb04 (Sprint Maneuver)' },
    { id: 'Vtb05', label: 'Vtb05 (Dense Traffic)' },
    { id: 'Vtb06', label: 'Vtb06 (Turning Maneuver)' },
    { id: 'random', label: '🎲 Random Real Road Trip' },
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-3.5 shadow-sm flex flex-col gap-3 select-none">
      {/* Top Row: Primary Transport & Scenarios */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Left Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Destructive Stop Button */}
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
            title="Restart session (Shortcut: R)"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Restart</span>
          </button>

          {/* Randomize Scenario Button */}
          <button
            onClick={randomize}
            disabled={isControlInFlight}
            className="h-9 px-3.5 rounded-xl font-semibold text-xs bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 transition-colors flex items-center gap-1.5 shadow-sm"
            title="Generate a fresh, unique road scenario with random physical perturbations"
          >
            <Dices className="w-3.5 h-3.5 text-blue-600" />
            <span>🎲 Randomize Scenario</span>
          </button>

          {/* Stochastic Real-World Sensor Noise Toggle */}
          <button
            onClick={() => toggleNoise(!noiseEnabled)}
            disabled={isControlInFlight}
            className={`h-9 px-3 rounded-xl font-medium text-xs transition-colors flex items-center gap-1.5 shadow-sm border ${
              noiseEnabled
                ? 'bg-amber-50 text-amber-900 border-amber-300 font-semibold'
                : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}
            title="Toggle realistic MEMS sensor thermal noise and road bump perturbations"
          >
            <Zap className={`w-3.5 h-3.5 ${noiseEnabled ? 'text-amber-600 fill-current' : 'text-slate-400'}`} />
            <span>Real-World Noise: {noiseEnabled ? 'ON' : 'OFF'}</span>
          </button>
        </div>

        {/* Right: Scenario Selector, Speed & Export */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Scenario Selector Dropdown */}
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-slate-400 font-medium hidden md:inline">Route:</span>
            <select
              value={currentRunId}
              onChange={(e) => setScenario(e.target.value)}
              disabled={isControlInFlight}
              className="h-9 px-2.5 rounded-xl border border-slate-200 bg-white text-xs font-semibold text-slate-800 focus:outline-none focus:border-blue-600 shadow-sm"
            >
              {scenarioOptions.map((opt) => (
                <option key={opt.id} value={opt.id}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Speed Selector */}
          <div className="flex items-center gap-1.5 text-xs">
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

          {/* Export Session JSON */}
          <button
            onClick={handleExport}
            className="h-9 px-3.5 rounded-xl text-xs font-medium bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 hover:text-slate-900 shadow-sm transition-colors flex items-center gap-1.5"
            title="Download runtime session snapshot JSON"
          >
            <Download className="w-3.5 h-3.5 text-blue-600" />
            <span className="hidden sm:inline">Export JSON</span>
          </button>
        </div>
      </div>
    </div>
  );
}
