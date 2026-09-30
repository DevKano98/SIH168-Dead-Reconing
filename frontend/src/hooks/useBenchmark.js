import { useState, useEffect } from 'react';
import { fetchBenchmarkSummary } from '../services/simulationApi';

export function useBenchmark() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const summary = await fetchBenchmarkSummary();
      setData(summary);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load historical benchmark summary');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return {
    benchmarkData: data,
    isLoading: loading,
    error,
    reload: load,
  };
}
