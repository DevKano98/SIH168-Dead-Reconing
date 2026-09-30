import React from 'react';
import { BenchmarkOverview } from '../components/benchmark/BenchmarkOverview';
import { BenchmarkTable } from '../components/benchmark/BenchmarkTable';
import { MethodologyPanel } from '../components/benchmark/MethodologyPanel';

export function BenchmarkPage({ benchmarkData, isLoading, error }) {
  return (
    <div className="max-w-[1600px] mx-auto p-4 sm:p-6 space-y-6">
      <BenchmarkOverview benchmarkData={benchmarkData} />
      <BenchmarkTable
        byDistance={benchmarkData?.by_distance}
        isLoading={isLoading}
        error={error}
      />
      <MethodologyPanel />
    </div>
  );
}
