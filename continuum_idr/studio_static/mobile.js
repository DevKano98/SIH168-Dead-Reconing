/**
 * Continuum Driver View Controller
 * Strictly connected to /api/runtime and /api/runtime/control.
 * Synchronized to the SAME runtime session as Studio.
 */

(function () {
  'use strict';

  const el = (id) => document.getElementById(id);
  const isValidNum = (v) => v !== null && v !== undefined && Number.isFinite(Number(v));
  const formatTime = (seconds) => {
    if (!isValidNum(seconds)) return '00:00.0';
    const s = Math.max(0, Number(seconds));
    const mins = Math.floor(s / 60);
    const secs = (s % 60).toFixed(1);
    return `${String(mins).padStart(2, '0')}:${secs.padStart(4, '0')}`;
  };

  const cardinalFromDeg = (deg) => {
    if (!isValidNum(deg)) return '—';
    const norm = (deg % 360 + 360) % 360;
    const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'N'];
    return dirs[Math.round(norm / 45)];
  };

  const state = {
    session: null,
    isControlInFlight: false,
    pollTimer: null,
  };

  // --- Network API Client ---
  async function fetchRuntime() {
    const res = await fetch('/api/runtime', {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      cache: 'no-store'
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  async function postControl(action, value = null) {
    if (state.isControlInFlight) return;
    state.isControlInFlight = true;

    try {
      const payload = { action };
      if (value !== null && value !== undefined) payload.value = value;
      const res = await fetch('/api/runtime/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const snap = await res.json();
        applySnapshot(snap);
      }
    } catch (_) {
      // Failed control will be retried on next poll
    } finally {
      state.isControlInFlight = false;
    }
  }

  // --- Serial Polling Loop ---
  async function pollLoop() {
    if (state.isControlInFlight) {
      state.pollTimer = setTimeout(pollLoop, 200);
      return;
    }

    try {
      const snap = await fetchRuntime();
      applySnapshot(snap);
    } catch (_) {
      // Connection glitch; keep trying
    } finally {
      state.pollTimer = setTimeout(pollLoop, 250);
    }
  }

  // --- UI Update ---
  function applySnapshot(snap) {
    if (!snap) return;
    state.session = snap;

    const curr = snap.current || {};
    const sdkState = curr.state || {};

    // 1. Speed
    const speedMps = sdkState.speed_mps;
    el('driver-speed').textContent = isValidNum(speedMps) ? Math.round(speedMps * 3.6) : '0';

    // 2. Heading & Cardinal Direction
    const heading = sdkState.heading_deg;
    el('driver-heading').textContent = isValidNum(heading) ? `${Math.round(heading)}°` : '—°';
    el('driver-cardinal').textContent = cardinalFromDeg(heading);

    // 3. Tracking Mode Pill
    const mode = sdkState.tracking_mode || 'UNINITIALIZED';
    const pill = el('driver-mode-pill');
    pill.textContent = mode.replace(/_/g, ' ');
    if (mode === 'GNSS_AIDED') {
      pill.className = 'mode-pill aided';
    } else if (mode === 'DEAD_RECKONING') {
      pill.className = 'mode-pill dead-reckoning';
    } else if (mode === 'RECOVERING') {
      pill.className = 'mode-pill recovering';
    } else {
      pill.className = 'mode-pill uninitialized';
    }

    // 4. Uncertainty
    const uncert = sdkState.horizontal_uncertainty_m;
    el('driver-uncertainty').textContent = isValidNum(uncert) ? `±${uncert.toFixed(1)} m` : '±— m';

    // 5. GPS Status
    const gpsStatusEl = el('driver-gps-status');
    if (snap.gnss_enabled) {
      gpsStatusEl.textContent = curr.gnss_delivered ? 'Delivered' : 'Delivering';
      gpsStatusEl.style.color = 'var(--text)';
    } else {
      gpsStatusEl.textContent = 'Withheld (Outage)';
      gpsStatusEl.style.color = 'var(--amber)';
    }

    // 6. Elapsed Time
    el('driver-elapsed').textContent = formatTime(curr.elapsed_s);

    // 7. Shared Control Buttons
    const playBtn = el('driver-btn-play');
    const playIcon = el('driver-play-icon');
    const playLabel = el('driver-play-label');

    if (snap.completed) {
      playLabel.textContent = 'Completed';
      playIcon.textContent = '✓';
      playBtn.disabled = true;
    } else if (snap.playing) {
      playLabel.textContent = 'Pause';
      playIcon.textContent = '⏸';
      playBtn.disabled = false;
    } else {
      playLabel.textContent = snap.index > 0 ? 'Resume' : 'Start';
      playIcon.textContent = '▶';
      playBtn.disabled = false;
    }

    const gnssBtn = el('driver-btn-gnss');
    const gnssLabel = el('driver-gnss-label');
    if (snap.gnss_enabled) {
      gnssBtn.className = 'hud-btn';
      gnssLabel.textContent = 'Withhold GPS';
    } else {
      gnssBtn.className = 'hud-btn withheld';
      gnssLabel.textContent = 'Restore GPS';
    }

    // 8. Render Canvas Map
    drawDriverMap();
  }

  // --- Mini Metric Map Canvas ---
  function drawDriverMap() {
    const canvas = el('driver-canvas');
    if (!canvas || !state.session) return;

    const samples = state.session.samples || [];
    if (samples.length === 0) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;

    if (canvas.width !== Math.round(width * dpr) || canvas.height !== Math.round(height * dpr)) {
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
    }

    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    // Dark background
    ctx.fillStyle = '#070c14';
    ctx.fillRect(0, 0, width, height);

    // Current position
    const curr = state.session.current;
    if (!curr || !isValidNum(curr.east_m) || !isValidNum(curr.north_m)) return;

    const curE = curr.east_m;
    const curN = curr.north_m;
    const heading = (curr.state?.heading_deg || 0) * Math.PI / 180;

    // Fixed zoom scale: roughly 1.5 pixels per metre
    const scale = 1.6;
    const cx = width / 2;
    const cy = height * 0.55;

    const toX = (e) => cx + (e - curE) * scale;
    const toY = (n) => cy - (n - curN) * scale;

    // Draw background metric grid
    ctx.strokeStyle = 'rgba(30, 45, 66, 0.4)';
    ctx.lineWidth = 1;
    for (let x = (cx % 50); x < width; x += 50) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = (cy % 50); y < height; y += 50) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    // Draw reference line
    ctx.beginPath();
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 2;
    let refStarted = false;
    samples.forEach(s => {
      if (isValidNum(s.reference_east_m) && isValidNum(s.reference_north_m)) {
        const sx = toX(s.reference_east_m);
        const sy = toY(s.reference_north_m);
        if (!refStarted) {
          ctx.moveTo(sx, sy);
          refStarted = true;
        } else {
          ctx.lineTo(sx, sy);
        }
      }
    });
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw estimated path
    ctx.beginPath();
    ctx.strokeStyle = '#3b82f6';
    ctx.lineWidth = 3;
    let estStarted = false;
    samples.forEach(s => {
      if (isValidNum(s.east_m) && isValidNum(s.north_m)) {
        const sx = toX(s.east_m);
        const sy = toY(s.north_m);
        if (!estStarted) {
          ctx.moveTo(sx, sy);
          estStarted = true;
        } else {
          ctx.lineTo(sx, sy);
        }
      }
    });
    ctx.stroke();

    // Draw uncertainty circle around vehicle
    const uncertaintyM = curr.state?.horizontal_uncertainty_m || 5.0;
    const radiusPx = Math.min(80, uncertaintyM * scale);
    ctx.beginPath();
    ctx.arc(cx, cy, radiusPx, 0, Math.PI * 2);
    ctx.fillStyle = curr.gnss_withheld ? 'rgba(245, 158, 11, 0.14)' : 'rgba(59, 130, 246, 0.12)';
    ctx.fill();
    ctx.strokeStyle = curr.gnss_withheld ? 'rgba(245, 158, 11, 0.6)' : 'rgba(59, 130, 246, 0.5)';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Draw vehicle marker
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(heading);

    ctx.beginPath();
    ctx.arc(0, 0, 9, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.fill();

    ctx.beginPath();
    ctx.moveTo(0, -16);
    ctx.lineTo(9, 9);
    ctx.lineTo(0, 5);
    ctx.lineTo(-9, 9);
    ctx.closePath();
    ctx.fillStyle = curr.gnss_withheld ? '#f59e0b' : '#3b82f6';
    ctx.fill();
    ctx.restore();
  }

  // --- Bind Controls ---
  function bindControls() {
    el('driver-btn-play').addEventListener('click', () => {
      if (!state.session || state.session.completed) return;
      postControl(state.session.playing ? 'pause' : 'play');
    });

    el('driver-btn-gnss').addEventListener('click', () => {
      if (!state.session) return;
      postControl('gnss', !state.session.gnss_enabled);
    });

    el('driver-btn-restart').addEventListener('click', () => {
      postControl('restart');
    });

    window.addEventListener('resize', drawDriverMap);
  }

  // --- Initialize ---
  function init() {
    bindControls();
    fetchRuntime().then(applySnapshot).catch(() => {});
    pollLoop();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
