import React, { useState, useEffect } from 'react';
import { useSimulation } from './hooks/useSimulation';
import { useBenchmark } from './hooks/useBenchmark';
import { AppShell } from './components/layout/AppShell';
import { StudioPage } from './pages/StudioPage';
import { BenchmarkPage } from './pages/BenchmarkPage';

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
    randomize,
    toggleNoise,
    setScenario,
    setRate,
    retryConnection,
  } = useSimulation(250);

  const { benchmarkData, isLoading: isBenchmarkLoading, error: benchmarkError } = useBenchmark();

  const [activePage, setActivePage] = useState('studio');
  const [currentSection, setCurrentSection] = useState('simulation');

  // Direct hash navigation (#benchmark or #evidence)
  useEffect(() => {
    const handleHash = () => {
      const hash = window.location.hash.toLowerCase();
      if (hash.includes('benchmark') || hash.includes('evidence')) {
        setActivePage('benchmark');
      } else {
        setActivePage('studio');
      }
    };

    handleHash();
    window.addEventListener('hashchange', handleHash);
    return () => window.removeEventListener('hashchange', handleHash);
  }, []);

  return (
    <AppShell
      activePage={activePage}
      setActivePage={(p) => {
        setActivePage(p);
        window.location.hash = p === 'benchmark' ? 'benchmark' : '';
      }}
      currentSection={currentSection}
      setCurrentSection={setCurrentSection}
      connectionStatus={connectionStatus}
      retryConnection={retryConnection}
      snapshot={snapshot}
    >
      {activePage === 'studio' ? (
        <StudioPage
          snapshot={snapshot}
          benchmarkData={benchmarkData}
          errorMessage={errorMessage}
          isControlInFlight={isControlInFlight}
          play={play}
          pause={pause}
          togglePlay={togglePlay}
          step={step}
          toggleGnss={toggleGnss}
          restart={restart}
          randomize={randomize}
          toggleNoise={toggleNoise}
          setScenario={setScenario}
          setRate={setRate}
          retryConnection={retryConnection}
        />
      ) : (
        <BenchmarkPage
          benchmarkData={benchmarkData}
          isLoading={isBenchmarkLoading}
          error={benchmarkError}
        />
      )}
    </AppShell>
  );
}
export default App;
