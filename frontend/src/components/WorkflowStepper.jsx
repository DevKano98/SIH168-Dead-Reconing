import React from 'react';
import { ArrowRight, Play, Satellite, Navigation, CheckCircle2 } from 'lucide-react';

export function WorkflowStepper({ snapshot }) {
  const isPlaying = snapshot?.playing;
  const index = snapshot?.index || 0;
  const gnssEnabled = snapshot?.gnss_enabled;
  const trackingMode = snapshot?.current?.state?.tracking_mode;
  const isCompleted = snapshot?.completed;

  // Compute active step (1 to 4)
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
      desc: 'Begin processing IO-VNBD stream',
      icon: Play,
    },
    {
      num: 2,
      title: 'Withhold GPS',
      desc: 'Simulate tunnel / urban canyon outage',
      icon: Satellite,
    },
    {
      num: 3,
      title: 'Observe Dead Reckoning',
      desc: 'Inertial EKF & speed model fallback',
      icon: Navigation,
    },
    {
      num: 4,
      title: 'Restore GPS & Export',
      desc: 'Reacquire fixes & save snapshot',
      icon: CheckCircle2,
    },
  ];

  return (
    <div className="bg-canvas-card border border-border-light rounded-xl p-3.5 shadow-card">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-ink-muted bg-canvas-subtle px-2 py-0.5 rounded border border-border-light">
            Interactive Workflow
          </span>
          <span className="text-xs text-ink-secondary hidden sm:inline">
            Causal sensor integration pipeline
          </span>
        </div>

        {/* Steps track */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 flex-1 max-w-4xl">
          {steps.map((step) => {
            const isActive = activeStep === step.num;
            const isPast = activeStep > step.num;
            const Icon = step.icon;

            return (
              <div
                key={step.num}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg border text-xs transition-all ${
                  isActive
                    ? 'bg-tech-blue-subtle/70 border-tech-blue text-tech-blue shadow-sm font-semibold'
                    : isPast
                    ? 'bg-canvas-subtle/50 border-border-light text-ink-secondary'
                    : 'bg-canvas-card border-border-subtle text-ink-muted opacity-75'
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-md flex items-center justify-center text-xs font-mono font-bold flex-shrink-0 ${
                    isActive
                      ? 'bg-tech-blue text-white shadow-sm'
                      : isPast
                      ? 'bg-green-100 text-green-700'
                      : 'bg-canvas-subtle text-ink-muted'
                  }`}
                >
                  {isPast ? '✓' : step.num}
                </div>
                <div className="truncate">
                  <div className="font-medium truncate">{step.title}</div>
                  <div className="text-[10px] text-ink-faint truncate hidden xl:block font-normal">
                    {step.desc}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
