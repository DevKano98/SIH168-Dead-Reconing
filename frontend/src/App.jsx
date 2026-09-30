import React, { useState, useEffect } from 'react';
import { useSimulation } from './hooks/useSimulation';
import { TopNavigation } from './components/TopNavigation';
import { WorkflowStepper } from './components/WorkflowStepper';
import { SimulationCanvas } from './components/SimulationCanvas';
import { NavigationPanel } from './components/NavigationPanel';
import { TransportControls } from './components/TransportControls';
import { ErrorChart } from './components/ErrorChart';
import { EventLog } from './components/EventLog';
import { BenchmarkView } from './components/BenchmarkView';
import { AlertCircle, RefreshCw } from 'lucide-react';

export function App() {
  const {
    snapshot,
    connectionStatus,
    errorMessage,
    isControlInFlight,
    play,
    pause,
    togglePlay,
    step,
    toggleGnss,
    restart,
    setRate,
    retryConnection,
  } = useSimulation(250);

  const [activeTab, setActiveTab] = useState('studio');

  // Support direct hash navigation (#benchmark or #evidence)
  useEffect(() => {
    const handleHash = () => {
      const hash = window.location.hash.toLowerCase();
      if (hash.includes('benchmark') || hash.includes('evidence')) {
        setActiveTab('benchmark');
      } else {
        setActiveTab('studio');
      }
    };

    handleHash();
    window.addEventListener('hashchange', handleHash);
    return () => window.removeEventListener('hashchange', handleHash);
  }, []);

  return (
    <div className="min-h-screen bg-canvas-base flex flex-col font-sans text-ink-primary">
      {/* Top Header Navigation */}
      <TopNavigation
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setActiveTab(tab);
          window.location.hash = tab === 'benchmark' ? 'benchmark' : '';
        }}
        snapshot={snapshot}
        connectionStatus={connectionStatus}
        retryConnection={retryConnection}
      />

      {/* Disconnection or Error Notification Banner */}
      {errorMessage && (
        <div className="bg-tech-red-subtle border-b border-red-200 px-4 py-2 text-xs text-tech-red flex items-center justify-between">
          <div className="flex items-center gap-2 max-w-[1720px] mx-auto w-full">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span className="font-medium truncate">{errorMessage}</span>
            <button
              onClick={retryConnection}
              className="ml-auto underline font-semibold hover:text-red-900 transition-colors flex items-center gap-1"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Retry</span>
            </button>
          </div>
        </div>
      )}

      {/* Main Workspace Body */}
      <main className="flex-1 w-full">
        {activeTab === 'studio' ? (
          <div className="max-w-[1720px] mx-auto px-4 sm:px-6 py-5 space-y-4">
            {/* Interactive Workflow Guidance Stepper */}
            <WorkflowStepper snapshot={snapshot} />

            {/* Core Workspace Grid: Left Canvas & Controls (70%), Right Inspector (30%) */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
              {/* Left Column: Canvas, Real-Time Chart, Transport, Event Log */}
              <div className="lg:col-span-8 xl:col-span-9 flex flex-col gap-4">
                {/* 2D Local ENU Trajectory Canvas */}
                <div className="h-[480px] xl:h-[540px]">
                  <SimulationCanvas snapshot={snapshot} />
                </div>

                {/* Primary Transport & Sensor Control Bar */}
                <TransportControls
                  snapshot={snapshot}
                  isControlInFlight={isControlInFlight}
                  play={play}
                  pause={pause}
                  togglePlay={togglePlay}
                  step={step}
                  toggleGnss={toggleGnss}
                  restart={restart}
                  setRate={setRate}
                />

                {/* Real-Time Error & Uncertainty Envelope Chart */}
                <ErrorChart snapshot={snapshot} />

                {/* Collapsible Session Control Event Log */}
                <EventLog events={snapshot?.events || []} />
              </div>

              {/* Right Column: Navigation State Inspector */}
              <div className="lg:col-span-4 xl:col-span-3">
                <NavigationPanel snapshot={snapshot} />
              </div>
            </div>
          </div>
        ) : (
          <BenchmarkView />
        )}
      </main>

      {/* Technical Footer */}
      <footer className="border-t border-border-light bg-canvas-card py-4 mt-8">
        <div className="max-w-[1720px] mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-ink-muted">
          <div>
            <strong>Continuum Studio</strong> · SIH168 Dead Reckoning Evaluation Environment · v0.3.0
          </div>
          <div className="text-[11px] text-ink-faint">
            Strict causal inference on recorded IO-VNBD datasets · Not live phone sensing
          </div>
        </div>
      </footer>
    </div>
  );
}
export default App;
