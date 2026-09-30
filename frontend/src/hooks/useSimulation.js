import { useState, useEffect, useRef, useCallback } from 'react';
import { fetchRuntime, postControlAction } from '../services/simulationApi';

export function useSimulation(pollIntervalMs = 250) {
  const [snapshot, setSnapshot] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connecting'); // 'connecting' | 'connected' | 'error' | 'syncing'
  const [errorMessage, setErrorMessage] = useState(null);
  const [isControlInFlight, setIsControlInFlight] = useState(false);

  const inFlightRef = useRef(false);
  const timerRef = useRef(null);
  const isMountedRef = useRef(true);

  // Polling loop
  const poll = useCallback(async () => {
    if (!isMountedRef.current) return;
    if (inFlightRef.current) {
      timerRef.current = setTimeout(poll, 150);
      return;
    }

    try {
      const data = await fetchRuntime();
      if (isMountedRef.current) {
        setSnapshot(data);
        setConnectionStatus('connected');
        setErrorMessage(null);
      }
    } catch (err) {
      if (isMountedRef.current) {
        setConnectionStatus('error');
        setErrorMessage(err.message || 'Unable to connect to Continuum Python SDK runtime');
      }
    } finally {
      if (isMountedRef.current) {
        timerRef.current = setTimeout(poll, pollIntervalMs);
      }
    }
  }, [pollIntervalMs]);

  useEffect(() => {
    isMountedRef.current = true;
    poll();
    return () => {
      isMountedRef.current = false;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [poll]);

  // Control executor
  const executeControl = useCallback(async (action, value = null) => {
    if (inFlightRef.current) return;
    inFlightRef.current = true;
    setIsControlInFlight(true);
    setConnectionStatus('syncing');

    try {
      const updated = await postControlAction(action, value);
      if (isMountedRef.current) {
        setSnapshot(updated);
        setConnectionStatus('connected');
        setErrorMessage(null);
      }
    } catch (err) {
      if (isMountedRef.current) {
        setErrorMessage(`Action "${action}" failed: ${err.message}`);
      }
    } finally {
      inFlightRef.current = false;
      if (isMountedRef.current) {
        setIsControlInFlight(false);
      }
    }
  }, []);

  const play = useCallback(() => executeControl('play'), [executeControl]);
  const pause = useCallback(() => executeControl('pause'), [executeControl]);
  const togglePlay = useCallback(() => {
    if (!snapshot) return;
    if (snapshot.completed) return;
    if (snapshot.playing) pause();
    else play();
  }, [snapshot, play, pause]);

  const step = useCallback((count = 25) => executeControl('step', count), [executeControl]);
  const setGnss = useCallback((enabled) => executeControl('gnss', enabled), [executeControl]);
  const toggleGnss = useCallback(() => {
    if (!snapshot) return;
    setGnss(!snapshot.gnss_enabled);
  }, [snapshot, setGnss]);

  const restart = useCallback(() => executeControl('restart'), [executeControl]);
  const setRate = useCallback((rate) => executeControl('rate', rate), [executeControl]);

  const retryConnection = useCallback(() => {
    setErrorMessage(null);
    setConnectionStatus('connecting');
    poll();
  }, [poll]);

  return {
    snapshot,
    connectionStatus,
    errorMessage,
    isControlInFlight,
    play,
    pause,
    togglePlay,
    step,
    setGnss,
    toggleGnss,
    restart,
    setRate,
    retryConnection,
  };
}
