import React from 'react';
import { Play, Pause, Check } from 'lucide-react';

export function WorkflowStepper({ snapshot, togglePlay, isControlInFlight }) {
  const isPlaying = snapshot?.playing;
  const index = snapshot?.index || 0;
  const gnssEnabled = snapshot?.gnss_enabled ?? true;
  const trackingMode = snapshot?.current?.state?.tracking_mode;
  const isCompleted = snapshot?.completed;

  // Active step calculation
  let activeStep = 1;
  if (isCompleted) {
    activeStep = 4;
  } else if (!gnssEnabled || trackingMode === 'DEAD_RECKONING') {
    activeStep = 3;
  } else if (isPlaying || index > 0) {
    activeStep = 2;
  } else {
    activeStep = 1;
  }

  const steps = [
    {
      num: 1,
      title: 'Start Engine',
      subtitle: 'Initialize simulation',
    },
    {
      num: 2,
      title: 'Withhold GPS',
      subtitle: 'Simulate tunnel / outage',
    },
    {
      num: 3,
      title: 'Observe Dead Reckoning',
      subtitle: 'Analyze drift & error',
    },
    {
      num: 4,
      title: 'Restore GPS & Export',
      subtitle: 'Compare & export results',
    },
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 select-none">
      {/* 4 Horizontal Steps */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 flex-1">
        {steps.map((step) => {
          const isActive = activeStep === step.num;
          const isPast = activeStep > step.num;

          return (
            <div
              key={step.num}
              className={`flex items-center gap-3 p-2.5 rounded-xl border transition-all ${
                isActive
                  ? 'bg-blue-50/70 border-blue-200 shadow-sm'
                  : isPast
                  ? 'bg-emerald-50/40 border-emerald-100'
                  : 'bg-slate-50/50 border-slate-100'
              }`}
            >
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-mono font-bold flex-shrink-0 ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm'
                    : isPast
                    ? 'bg-emerald-600 text-white'
                    : 'bg-slate-200 text-slate-500'
                }`}
              >
                {isPast ? <Check className="w-4 h-4" /> : step.num}
              </div>
              <div className="min-w-0">
                <div
                  className={`text-xs font-semibold truncate ${
                    isActive ? 'text-blue-900' : isPast ? 'text-emerald-900' : 'text-slate-600'
                  }`}
                >
                  {step.title}
                </div>
                <div className="text-[11px] text-slate-400 truncate">{step.subtitle}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Start Engine action at far right */}
      <div className="flex items-center justify-end flex-shrink-0">
        <button
          onClick={togglePlay}
          disabled={isCompleted || isControlInFlight}
          className={`h-10 px-4 rounded-xl font-semibold text-xs flex items-center gap-2 transition-all shadow-sm ${
            isCompleted
              ? 'bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed'
              : isPlaying
              ? 'bg-white border border-slate-300 text-slate-800 hover:bg-slate-50'
              : 'bg-emerald-600 hover:bg-emerald-700 text-white'
          }`}
        >
          {isPlaying ? (
            <>
              <Pause className="w-3.5 h-3.5" />
              <span>Pause Engine</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{index > 0 ? 'Resume Engine' : 'Start Engine'}</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
