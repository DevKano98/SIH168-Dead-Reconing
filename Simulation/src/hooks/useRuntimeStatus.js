import { useState, useEffect, useCallback } from 'react';
import { fetchHealth } from '../services/simulationApi';

export function useRuntimeStatus(intervalMs = 3000) {
  const [health, setHealth] = useState(null);
  const [isReady, setIsReady] = useState(false);
  const [status, setStatus] = useState('checking'); // 'checking' | 'ready' | 'missing' | 'offline'

  const check = useCallback(async () => {
    try {
      const data = await fetchHealth();
      setHealth(data);
      if (data.status === 'ready') {
        setIsReady(true);
        setStatus('ready');
      } else {
        setIsReady(false);
        setStatus('missing');
      }
    } catch (_) {
      setIsReady(false);
      setStatus('offline');
    }
  }, []);

  useEffect(() => {
    check();
    const timer = setInterval(check, intervalMs);
    return () => clearInterval(timer);
  }, [check, intervalMs]);

  return { health, isReady, status, refresh: check };
}
