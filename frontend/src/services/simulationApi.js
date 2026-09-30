/**
 * Continuum Studio Simulation API Service
 * Exclusively connects to the active Python SDK runtime endpoints.
 */

export async function fetchRuntime() {
  const response = await fetch('/api/runtime', {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    let errorDetail = `Runtime error (${response.status})`;
    try {
      const data = await response.json();
      if (data.detail) errorDetail = data.detail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return response.json();
}

export async function postControlAction(action, value = null) {
  const payload = { action };
  if (value !== null && value !== undefined) {
    payload.value = value;
  }

  const response = await fetch('/api/runtime/control', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let errorDetail = `Control failed (${response.status})`;
    try {
      const data = await response.json();
      if (data.detail) errorDetail = data.detail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return response.json();
}

export async function fetchBenchmarkSummary() {
  const response = await fetch('/api/summary', {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    let errorDetail = `Summary error (${response.status})`;
    try {
      const data = await response.json();
      if (data.detail) errorDetail = data.detail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return response.json();
}

export async function fetchHealth() {
  const response = await fetch('/api/health', {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error(`Health check failed (${response.status})`);
  }

  return response.json();
}

export const EXPORT_SESSION_URL = '/api/runtime/export';
