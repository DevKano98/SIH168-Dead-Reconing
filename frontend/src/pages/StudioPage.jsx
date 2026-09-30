import React from 'react';
import { SimulationHeader } from '../components/simulation/SimulationHeader';
import { WorkflowStepper } from '../components/simulation/WorkflowStepper';
import { SimulationCanvas } from '../components/simulation/SimulationCanvas';
import { NavigationPanel } from '../components/simulation/NavigationPanel';
import { LiveMetrics } from '../components/simulation/LiveMetrics';
import { ErrorChart } from '../components/simulation/ErrorChart';
import { SessionControls } from '../components/simulation/SessionControls';
import { EventLog } from '../components/simulation/EventLog';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export function StudioPage({
  snapshot,
  benchmarkData,
  errorMessage,
  isControlInFlight,
  play,
  pause,
  togglePlay,
  step,
  toggleGnss,
  restart,
  randomize,
  toggleNoise,
  setScenario,
  setRate,
  retryConnection,
}) {
  return (
    <div className="max-w-[1600px] mx-auto p-4 sm:p-6 space-y-5">
      {/* 1. Main Header */}
      <SimulationHeader />

      {/* 2. Compact Error/Disconnected Warning Strip */}
      {errorMessage && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl px-4 py-2.5 flex items-center justify-between text-xs text-rose-800">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <div>
              <strong className="font-semibold">Runtime unavailable:</strong> Unable to connect to Continuum Python SDK.
            </div>
          </div>
          <button
            onClick={retryConnection}
            className="flex items-center gap-1 px-2.5 py-1 rounded bg-white border border-rose-300 hover:bg-rose-100 font-semibold text-rose-700 transition-colors shadow-xs"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Retry Connection</span>
          </button>
        </div>
      )}

      {/* 3. Workflow Stepper */}
      <WorkflowStepper
        snapshot={snapshot}
        togglePlay={togglePlay}
        isControlInFlight={isControlInFlight}
      />

      {/* 4. Two-Column Workspace: Left ~72%, Right ~28% */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left Column (~72%) */}
        <div className="lg:col-span-8 xl:col-span-8 flex flex-col gap-4">
          {/* Main Simulation / Map Canvas */}
          <div className="h-[490px] xl:h-[550px]">
            <SimulationCanvas snapshot={snapshot} />
          </div>

          {/* Live Metrics: 4 Compact Cards */}
          <LiveMetrics snapshot={snapshot} benchmarkData={benchmarkData} />

          {/* Real-Time Error & Uncertainty Chart */}
          <ErrorChart snapshot={snapshot} />

          {/* Session Controls: Stop Engine, Step +25, Restart, Randomize, Noise, Speed, Export */}
          <SessionControls
            snapshot={snapshot}
            isControlInFlight={isControlInFlight}
            pause={pause}
            step={step}
            restart={restart}
            randomize={randomize}
            toggleNoise={toggleNoise}
            setScenario={setScenario}
            setRate={setRate}
          />

          {/* Session Control Event Log */}
          <EventLog events={snapshot?.events || []} />
        </div>

        {/* Right Column (~28%) */}
        <div className="lg:col-span-4 xl:col-span-4">
          <NavigationPanel snapshot={snapshot} />
        </div>
      </div>
    </div>
  );
}
