/**
 * Technical numerical and time formatters for scientific telemetry display.
 */

export const isValidNum = (v) => v !== null && v !== undefined && Number.isFinite(Number(v));

export const fmtNum = (v, digits = 1, fallback = '—') => {
  return isValidNum(v) ? Number(v).toFixed(digits) : fallback;
};

export const formatDuration = (seconds) => {
  if (!isValidNum(seconds)) return '00:00.0';
  const s = Math.max(0, Number(seconds));
  const mins = Math.floor(s / 60);
  const secs = (s % 60).toFixed(1);
  return `${String(mins).padStart(2, '0')}:${secs.padStart(4, '0')}`;
};

export const formatSpeed = (speedMps) => {
  if (!isValidNum(speedMps)) return { kmh: '—', mps: '—' };
  const mps = Number(speedMps);
  const kmh = (mps * 3.6).toFixed(1);
  return {
    kmh,
    mps: mps.toFixed(2),
  };
};

export const cardinalFromDeg = (deg) => {
  if (!isValidNum(deg)) return '—';
  const norm = ((Number(deg) % 360) + 360) % 360;
  const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'N'];
  return dirs[Math.round(norm / 45)];
};
