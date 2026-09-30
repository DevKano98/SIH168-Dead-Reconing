/**
 * Continuum Studio — Runtime Frontend Controller
 * Strictly connects to /api/runtime and /api/summary.
 * Never uses legacy /api/session or /api/demo.
 */

(function () {
  'use strict';

  // --- Utility functions ---
  const el = (id) => document.getElementById(id);
  const isValidNum = (v) => v !== null && v !== undefined && Number.isFinite(Number(v));
  const fmtNum = (v, digits = 1) => isValidNum(v) ? Number(v).toFixed(digits) : '—';
  const formatTime = (seconds) => {
    if (!isValidNum(seconds)) return '00:00.0';
    const s = Math.max(0, Number(seconds));
    const mins = Math.floor(s / 60);
    const secs = (s % 60).toFixed(1);
    return `${String(mins).padStart(2, '0')}:${secs.padStart(4, '0')}`;
  };

  // --- Application State ---
  const state = {
    session: null,
    historicalSummary: null,
    isPolling: false,
    pollTimer: null,
    isControlInFlight: false,
    lastSuccessfulPoll: 0,
    
    // Canvas & Viewport State
    view: {
      zoom: 1.0,
      panX: 0,
      panY: 0,
      autoFit: true,
      isDragging: false,
      dragStartX: 0,
      dragStartY: 0,
      scalePixelsPerMetre: 1.0,
    },

    // Layer toggles
    layers: {
      estimate: true,
      reference: true,
      uncertainty: true,
      grid: true,
    }
  };

  // --- Network API Client ---
  async function fetchRuntime() {
    const response = await fetch('/api/runtime', {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      cache: 'no-store'
    });
    if (!response.ok) {
      throw new Error(`Runtime error (HTTP ${response.status}): ${response.statusText}`);
    }
    return response.json();
  }

  async function postControl(action, value = null) {
    if (state.isControlInFlight) return;
    state.isControlInFlight = true;
    updatePendingControls(true);

    try {
      const payload = { action };
      if (value !== null && value !== undefined) {
        payload.value = value;
      }
      const response = await fetch('/api/runtime/control', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Control error (HTTP ${response.status})`);
      }
      const newSnapshot = await response.json();
      applySnapshot(newSnapshot);
    } catch (err) {
      showError(`Control action "${action}" failed: ${err.message}`);
    } finally {
      state.isControlInFlight = false;
      updatePendingControls(false);
    }
  }

  // --- Polling Lifecycle ---
  async function pollLoop() {
    if (state.isControlInFlight) {
      // Suspend polling while control request is in flight
      state.pollTimer = setTimeout(pollLoop, 200);
      return;
    }

    try {
      const snapshot = await fetchRuntime();
      applySnapshot(snapshot);
      setConnectionStatus('connected', 'Connected (SDK Runtime)');
      hideError();
      state.lastSuccessfulPoll = Date.now();
    } catch (err) {
      setConnectionStatus('disconnected', 'Disconnected');
      showError(`Lost connection to Continuum Python SDK runtime. ${err.message}`);
    } finally {
      // Schedule next poll serially (never overlapping)
      state.pollTimer = setTimeout(pollLoop, 250);
    }
  }

  function setConnectionStatus(status, text) {
    const badge = el('connection-badge');
    const badgeText = el('connection-text');
    badge.className = `badge-status ${status}`;
    badgeText.textContent = text;
  }

  function showError(msg) {
    const banner = el('error-banner');
    const messageEl = el('error-message');
    messageEl.textContent = msg;
    banner.classList.add('visible');
  }

  function hideError() {
    el('error-banner').classList.remove('visible');
  }

  function updatePendingControls(isPending) {
    const btns = [el('btn-play'), el('btn-step'), el('btn-toggle-gnss'), el('btn-restart'), el('rate-select')];
    btns.forEach(b => {
      if (b) b.disabled = isPending;
    });
    if (isPending) {
      setConnectionStatus('syncing', 'Syncing...');
    }
  }

  // --- Snapshot Application & UI Synchronization ---
  function applySnapshot(snap) {
    if (!snap) return;
    state.session = snap;

    // 1. Update Workflow Banner & Metadata
    el('meta-run-id').textContent = snap.run_id || '—';
    el('meta-model-id').textContent = snap.model_id || '—';
    el('card-run-id').textContent = snap.run_id || '—';
    el('card-rate').textContent = `${snap.rate || 1.0}×`;

    // 2. Play / Pause Button State
    const playText = el('play-text');
    const playIcon = el('play-icon');
    const playBtn = el('btn-play');
    if (snap.completed) {
      playText.textContent = 'Completed';
      playIcon.textContent = '✓';
      playBtn.disabled = true;
    } else if (snap.playing) {
      playText.textContent = 'Pause Engine';
      playIcon.textContent = '⏸';
      playBtn.disabled = false;
    } else {
      playText.textContent = snap.index > 0 ? 'Resume Engine' : 'Start Engine';
      playIcon.textContent = '▶';
      playBtn.disabled = false;
    }

    // Step button: only active when paused and not completed
    el('btn-step').disabled = snap.playing || snap.completed;

    // Rate select sync
    const rateSelect = el('rate-select');
    if (rateSelect && String(rateSelect.value) !== String(snap.rate)) {
      rateSelect.value = String(snap.rate);
    }

    // 3. GPS Withholding Toggle Button
    const gnssBtn = el('btn-toggle-gnss');
    const gnssIcon = el('gnss-toggle-icon');
    const gnssText = el('gnss-toggle-text');
    if (snap.gnss_enabled) {
      gnssBtn.className = 'btn-ctrl gps-toggle';
      gnssIcon.textContent = '⌁';
      gnssText.textContent = 'Withhold GPS (Simulate Tunnel)';
      el('gps-switch-state').textContent = 'Delivering';
      el('gps-switch-state').style.color = 'var(--text-bright)';
    } else {
      gnssBtn.className = 'btn-ctrl gps-toggle withholding';
      gnssIcon.textContent = '↗';
      gnssText.textContent = 'Restore GPS (Deliver Fixes)';
      el('gps-switch-state').textContent = 'Withheld (Outage)';
      el('gps-switch-state').style.color = 'var(--amber)';
    }

    // 4. Current State Readouts
    const curr = snap.current || {};
    const sdkState = curr.state || {};

    // Tracking Mode Pill
    const modePill = el('tracking-mode-pill');
    const mode = sdkState.tracking_mode || 'UNINITIALIZED';
    modePill.textContent = mode.replace(/_/g, ' ');
    if (mode === 'GNSS_AIDED') {
      modePill.className = 'mode-pill aided';
    } else if (mode === 'DEAD_RECKONING') {
      modePill.className = 'mode-pill dead-reckoning';
    } else if (mode === 'RECOVERING') {
      modePill.className = 'mode-pill recovering';
    } else {
      modePill.className = 'mode-pill uninitialized';
    }

    // Speedometer (km/h and m/s)
    const speedMps = sdkState.speed_mps;
    if (isValidNum(speedMps)) {
      el('speed-val').textContent = (speedMps * 3.6).toFixed(1);
      el('speed-mps-val').textContent = `${speedMps.toFixed(1)} m/s`;
    } else {
      el('speed-val').textContent = '—';
      el('speed-mps-val').textContent = '— m/s';
    }

    // Measured Error vs Estimated Uncertainty (Distinct quantities!)
    const measuredError = curr.error_m;
    const estUncertainty = sdkState.horizontal_uncertainty_m;
    el('measured-error-val').textContent = isValidNum(measuredError) ? `${measuredError.toFixed(1)} m` : '— m';
    el('estimated-uncertainty-val').textContent = isValidNum(estUncertainty) ? `±${estUncertainty.toFixed(1)} m` : '— m';

    // Heading
    const heading = sdkState.heading_deg;
    el('heading-val').textContent = isValidNum(heading) ? `${heading.toFixed(1)}°` : '—°';

    // Metric Coordinates
    el('disp-east').textContent = fmtNum(curr.east_m, 1);
    el('disp-north').textContent = fmtNum(curr.north_m, 1);

    // GPS Delivery Event Badge
    const deliveryBadge = el('gps-delivery-badge');
    if (curr.gnss_withheld) {
      deliveryBadge.textContent = 'Withheld';
      deliveryBadge.className = 'gps-badge withheld';
    } else if (curr.gnss_delivered) {
      deliveryBadge.textContent = 'New Fix Delivered';
      deliveryBadge.className = 'gps-badge delivered';
    } else {
      deliveryBadge.textContent = 'Monitoring';
      deliveryBadge.className = 'gps-badge idle';
    }

    // Last GNSS Decision & Accepted Age
    el('last-decision-val').textContent = sdkState.last_gnss_decision || '—';
    el('accepted-age-val').textContent = isValidNum(sdkState.last_accepted_gnss_age_s)
      ? `${sdkState.last_accepted_gnss_age_s.toFixed(1)} s`
      : '—';

    // Health Flags
    const flags = sdkState.health_flags;
    if (Array.isArray(flags) && flags.length > 0) {
      el('health-flags-val').textContent = flags.join(', ');
      el('health-flags-val').style.color = 'var(--amber)';
    } else {
      el('health-flags-val').textContent = 'None';
      el('health-flags-val').style.color = 'var(--text-faint)';
    }

    // 5. Counters & Timing
    const counters = snap.counters || {};
    el('cnt-imu').textContent = counters.imu_processed !== undefined ? counters.imu_processed.toLocaleString() : '—';
    el('cnt-delivered').textContent = counters.gnss_delivered !== undefined ? counters.gnss_delivered.toLocaleString() : '—';
    el('cnt-withheld').textContent = counters.gnss_withheld !== undefined ? counters.gnss_withheld.toLocaleString() : '0';

    const elapsed = curr.elapsed_s || 0;
    const duration = snap.duration_s || 1;
    el('elapsed-time-label').textContent = formatTime(elapsed);
    el('total-time-label').textContent = formatTime(duration);

    const progressPct = Math.min(100, Math.max(0, (elapsed / duration) * 100));
    el('session-progress-fill').style.width = `${progressPct.toFixed(1)}%`;

    el('completion-status-badge').textContent = snap.completed ? 'COMPLETED' : 'IN PROGRESS';
    el('completion-status-badge').style.color = snap.completed ? 'var(--green)' : 'var(--text-faint)';

    // 6. Workflow Step Highlighter
    highlightWorkflowStep(snap, mode);

    // 7. Update Event Log Table
    renderEventLog(snap.events || []);

    // 8. Render Trajectory Canvas
    renderTrajectoryCanvas();
  }

  function highlightWorkflowStep(snap, mode) {
    const s1 = el('step-1');
    const s2 = el('step-2');
    const s3 = el('step-3');
    const s4 = el('step-4');
    [s1, s2, s3, s4].forEach(s => s && s.classList.remove('active'));

    if (!snap.playing && snap.index === 0) {
      s1.classList.add('active');
    } else if (snap.gnss_enabled && mode !== 'DEAD_RECKONING') {
      s2.classList.add('active');
    } else if (!snap.gnss_enabled || mode === 'DEAD_RECKONING') {
      s3.classList.add('active');
    } else {
      s4.classList.add('active');
    }
  }

  function renderEventLog(events) {
    const tbody = el('event-table-body');
    const countBadge = el('event-count-badge');
    if (!tbody) return;

    countBadge.textContent = `(${events.length} event${events.length === 1 ? '' : 's'})`;

    if (events.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-faint);">No control events recorded.</td></tr>`;
      return;
    }

    // Render chronological or reverse chronological (newest on top)
    const reversed = [...events].reverse();
    tbody.innerHTML = reversed.map(ev => {
      const timeStr = isValidNum(ev.time_s) ? Number(ev.time_s).toFixed(2) : '—';
      const actionStr = String(ev.action || '—');
      const idxStr = ev.after_source_index !== undefined ? String(ev.after_source_index) : '—';
      const gnssStr = ev.gnss_enabled ? '<span style="color: var(--green);">Delivering</span>' : '<span style="color: var(--amber);">Withheld</span>';
      const rateStr = ev.rate !== undefined ? `${ev.rate}×` : '—';

      return `<tr>
        <td>${timeStr}</td>
        <td><strong>${actionStr}</strong></td>
        <td>${idxStr}</td>
        <td>${gnssStr}</td>
        <td>${rateStr}</td>
      </tr>`;
    }).join('');
  }

  // --- Trajectory Canvas Renderer ---
  function renderTrajectoryCanvas() {
    const canvas = el('trajectory-canvas');
    if (!canvas || !state.session) return;

    const samples = state.session.samples || [];
    if (samples.length === 0) return;

    // High-DPI support
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

    // Clear background
    ctx.fillStyle = '#090e18';
    ctx.fillRect(0, 0, width, height);

    // Compute bounding box across all processed samples
    let minE = Infinity, maxE = -Infinity, minN = Infinity, maxN = -Infinity;
    samples.forEach(s => {
      if (isValidNum(s.east_m)) {
        minE = Math.min(minE, s.east_m);
        maxE = Math.max(maxE, s.east_m);
      }
      if (isValidNum(s.north_m)) {
        minN = Math.min(minN, s.north_m);
        maxN = Math.max(maxN, s.north_m);
      }
      if (state.layers.reference && isValidNum(s.reference_east_m)) {
        minE = Math.min(minE, s.reference_east_m);
        maxE = Math.max(maxE, s.reference_east_m);
      }
      if (state.layers.reference && isValidNum(s.reference_north_m)) {
        minN = Math.min(minN, s.reference_north_m);
        maxN = Math.max(maxN, s.reference_north_m);
      }
    });

    if (!Number.isFinite(minE)) {
      minE = -50; maxE = 50; minN = -50; maxN = 50;
    }

    const spanE = Math.max(30, maxE - minE);
    const spanN = Math.max(30, maxN - minN);
    const centerE = (minE + maxE) / 2;
    const centerN = (minN + maxN) / 2;

    // Calculate base scale to fit with margin
    const margin = 50;
    const availW = Math.max(50, width - margin * 2);
    const availH = Math.max(50, height - margin * 2);
    const fitScale = Math.min(availW / spanE, availH / spanN);

    // Apply zoom and pan
    const scale = fitScale * state.view.zoom;
    state.view.scalePixelsPerMetre = scale;

    const screenCenterX = width / 2 + state.view.panX;
    const screenCenterY = height / 2 + state.view.panY;

    // Coordinate transform: East (+x), North (+y goes UP on canvas, so inverted in screen space)
    const toScreenX = (e) => screenCenterX + (e - centerE) * scale;
    const toScreenY = (n) => screenCenterY - (n - centerN) * scale;

    // 1. Draw Metric Grid
    if (state.layers.grid) {
      drawMetricGrid(ctx, width, height, centerE, centerN, scale, toScreenX, toScreenY);
    }

    // 2. Draw Offline Reference Trajectory (Neutral Slate Dashed Line)
    if (state.layers.reference) {
      ctx.beginPath();
      ctx.setLineDash([5, 5]);
      ctx.strokeStyle = '#64748b';
      ctx.lineWidth = 2;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      let started = false;
      samples.forEach(s => {
        if (isValidNum(s.reference_east_m) && isValidNum(s.reference_north_m)) {
          const sx = toScreenX(s.reference_east_m);
          const sy = toScreenY(s.reference_north_m);
          if (!started) {
            ctx.moveTo(sx, sy);
            started = true;
          } else {
            ctx.lineTo(sx, sy);
          }
        }
      });
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // 3. Draw Continuum Estimated Trajectory (Solid Blue Line)
    if (state.layers.estimate) {
      ctx.beginPath();
      ctx.strokeStyle = '#3b82f6';
      ctx.lineWidth = 3;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      let started = false;
      samples.forEach(s => {
        if (isValidNum(s.east_m) && isValidNum(s.north_m)) {
          const sx = toScreenX(s.east_m);
          const sy = toScreenY(s.north_m);
          if (!started) {
            ctx.moveTo(sx, sy);
            started = true;
          } else {
            ctx.lineTo(sx, sy);
          }
        }
      });
      ctx.stroke();
    }

    // 4. Draw Current Vehicle Marker & Uncertainty Ring
    const curr = state.session.current;
    if (curr && isValidNum(curr.east_m) && isValidNum(curr.north_m)) {
      const vx = toScreenX(curr.east_m);
      const vy = toScreenY(curr.north_m);
      const sdkState = curr.state || {};
      const uncertaintyM = sdkState.horizontal_uncertainty_m || 5.0;

      // Draw Uncertainty Ring
      if (state.layers.uncertainty && isValidNum(uncertaintyM)) {
        const rawRadiusPx = uncertaintyM * scale;
        const maxRadiusPx = 120; // Visual cap for screen clarity
        const capped = rawRadiusPx > maxRadiusPx;
        const drawRadiusPx = Math.min(rawRadiusPx, maxRadiusPx);

        const capNotice = el('uncertainty-cap-notice');
        if (capNotice) {
          capNotice.style.display = capped ? 'block' : 'none';
        }

        ctx.beginPath();
        ctx.arc(vx, vy, drawRadiusPx, 0, Math.PI * 2);
        ctx.fillStyle = curr.gnss_withheld ? 'rgba(245, 158, 11, 0.12)' : 'rgba(59, 130, 246, 0.12)';
        ctx.fill();
        ctx.strokeStyle = curr.gnss_withheld ? 'rgba(245, 158, 11, 0.65)' : 'rgba(59, 130, 246, 0.6)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash(capped ? [4, 4] : []);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // Draw Oriented Vehicle Arrow
      const headingDeg = sdkState.heading_deg || 0;
      const headingRad = (headingDeg * Math.PI) / 180;

      ctx.save();
      ctx.translate(vx, vy);
      ctx.rotate(headingRad);

      // Outer vehicle glow
      ctx.beginPath();
      ctx.arc(0, 0, 8, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();

      // Heading arrow
      ctx.beginPath();
      ctx.moveTo(0, -14);
      ctx.lineTo(8, 8);
      ctx.lineTo(0, 4);
      ctx.lineTo(-8, 8);
      ctx.closePath();
      ctx.fillStyle = curr.gnss_withheld ? '#f59e0b' : '#3b82f6';
      ctx.shadowColor = 'rgba(0, 0, 0, 0.4)';
      ctx.shadowBlur = 6;
      ctx.fill();
      ctx.restore();
    }

    // 5. Update Scale Bar
    updateScaleBar(scale);
  }

  function drawMetricGrid(ctx, width, height, centerE, centerN, scale, toScreenX, toScreenY) {
    // Choose clean metric step based on scale
    const targetPixelStep = 80;
    const rawStepMetres = targetPixelStep / scale;
    const steps = [10, 20, 50, 100, 200, 500, 1000];
    const metricStep = steps.find(s => s >= rawStepMetres) || 200;

    const startE = Math.floor((centerE - (width / scale) / 2) / metricStep) * metricStep;
    const endE = Math.ceil((centerE + (width / scale) / 2) / metricStep) * metricStep;
    const startN = Math.floor((centerN - (height / scale) / 2) / metricStep) * metricStep;
    const endN = Math.ceil((centerN + (height / scale) / 2) / metricStep) * metricStep;

    ctx.strokeStyle = 'rgba(30, 45, 66, 0.45)';
    ctx.lineWidth = 1;
    ctx.font = '10px ui-monospace, SFMono-Regular, Menlo, monospace';
    ctx.fillStyle = 'rgba(148, 163, 184, 0.35)';

    for (let e = startE; e <= endE; e += metricStep) {
      const x = toScreenX(e);
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
      ctx.fillText(`${e}m`, x + 4, height - 8);
    }

    for (let n = startN; n <= endN; n += metricStep) {
      const y = toScreenY(n);
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
      ctx.fillText(`${n}m`, 6, y - 4);
    }
  }

  function updateScaleBar(scale) {
    const scaleLine = el('scale-bar-line');
    const scaleLabel = el('scale-bar-label');
    if (!scaleLine || !scaleLabel) return;

    // Pick rounded metric distance that fits roughly 60-120 pixels
    const targetPx = 80;
    const rawDist = targetPx / scale;
    const cleanDists = [10, 20, 50, 100, 200, 500];
    const distMetres = cleanDists.find(d => d >= rawDist) || 100;
    const pixelWidth = distMetres * scale;

    scaleLine.style.width = `${Math.round(pixelWidth)}px`;
    scaleLabel.textContent = `${distMetres} m`;
  }

  // --- Historical Benchmark Renderer ---
  async function loadHistoricalSummary() {
    try {
      const response = await fetch('/api/summary', { cache: 'no-store' });
      if (!response.ok) return;
      const data = await response.json();
      state.historicalSummary = data;
      renderHistoricalSummary(data);
    } catch (_) {
      // Historical summary is secondary; ignore if unreachable
    }
  }

  function renderHistoricalSummary(data) {
    if (!data) return;

    el('bench-runs').textContent = data.independent_test_runs || '—';
    el('bench-outages').textContent = data.total_outages_evaluated || '—';

    const overall = data.overall || {};
    el('bench-median-error').textContent = isValidNum(overall.median_endpoint_error_m)
      ? `${overall.median_endpoint_error_m.toFixed(1)} m`
      : '—';
    el('bench-median-drift').textContent = isValidNum(overall.median_drift_percent)
      ? `${overall.median_drift_percent.toFixed(1)}%`
      : '—';
    el('bench-pass-rate').textContent = isValidNum(overall.pass_rate_below_10_percent)
      ? `${(overall.pass_rate_below_10_percent * 100).toFixed(0)}%`
      : '0.0%';

    // Distance Breakdown Table
    const tbody = el('bench-table-body');
    const byDist = data.by_distance || {};
    const rows = Object.entries(byDist).map(([distKey, row]) => {
      return `<tr>
        <td><strong>${distKey} Outage</strong></td>
        <td>${row.outage_count || '—'}</td>
        <td><strong>${fmtNum(row.median_endpoint_error_m)} m</strong></td>
        <td>${fmtNum(row.baseline_last_speed_median_error_m)} m</td>
        <td>${fmtNum(row.baseline_frozen_median_error_m)} m</td>
        <td>${fmtNum(row.median_drift_percent)}%</td>
        <td><span style="color: var(--amber);">${fmtNum(row.pass_rate_below_10_percent * 100, 0)}%</span></td>
      </tr>`;
    });

    if (rows.length > 0) {
      tbody.innerHTML = rows.join('');
    }
  }

  // --- Event Bindings & User Interactions ---
  function bindInteractions() {
    // 1. Play / Pause Button
    el('btn-play').addEventListener('click', () => {
      if (!state.session) return;
      if (state.session.completed) return;
      const action = state.session.playing ? 'pause' : 'play';
      postControl(action);
    });

    // 2. Step Button (+25 samples)
    el('btn-step').addEventListener('click', () => {
      postControl('step', 25);
    });

    // 3. GPS Withholding Toggle Button
    el('btn-toggle-gnss').addEventListener('click', () => {
      if (!state.session) return;
      const nextSetting = !state.session.gnss_enabled;
      postControl('gnss', nextSetting);
    });

    // 4. Restart Button
    el('btn-restart').addEventListener('click', () => {
      postControl('restart');
      state.view.autoFit = true;
      state.view.zoom = 1.0;
      state.view.panX = 0;
      state.view.panY = 0;
    });

    // 5. Rate Selector
    el('rate-select').addEventListener('change', (e) => {
      const val = parseFloat(e.target.value);
      if (isValidNum(val)) {
        postControl('rate', val);
      }
    });

    // 6. Export Session JSON
    el('btn-export').addEventListener('click', () => {
      window.location.href = '/api/runtime/export';
    });

    // 7. Layer Toggles
    const setupToggle = (btnId, key) => {
      const btn = el(btnId);
      if (!btn) return;
      btn.addEventListener('click', () => {
        state.layers[key] = !state.layers[key];
        btn.classList.toggle('active', state.layers[key]);
        renderTrajectoryCanvas();
      });
    };
    setupToggle('toggle-estimate', 'estimate');
    setupToggle('toggle-reference', 'reference');
    setupToggle('toggle-uncertainty', 'uncertainty');
    setupToggle('toggle-grid', 'grid');

    // 8. Canvas View Controls
    el('btn-zoom-in').addEventListener('click', () => {
      state.view.zoom = Math.min(5.0, state.view.zoom * 1.3);
      renderTrajectoryCanvas();
    });

    el('btn-zoom-out').addEventListener('click', () => {
      state.view.zoom = Math.max(0.2, state.view.zoom / 1.3);
      renderTrajectoryCanvas();
    });

    el('btn-recenter').addEventListener('click', () => {
      state.view.zoom = 1.0;
      state.view.panX = 0;
      state.view.panY = 0;
      state.view.autoFit = true;
      renderTrajectoryCanvas();
    });

    // 9. Canvas Mouse Drag to Pan
    const container = el('canvas-container');
    container.addEventListener('mousedown', (e) => {
      state.view.isDragging = true;
      state.view.dragStartX = e.clientX - state.view.panX;
      state.view.dragStartY = e.clientY - state.view.panY;
      state.view.autoFit = false;
    });

    window.addEventListener('mousemove', (e) => {
      if (!state.view.isDragging) return;
      state.view.panX = e.clientX - state.view.dragStartX;
      state.view.panY = e.clientY - state.view.dragStartY;
      renderTrajectoryCanvas();
    });

    window.addEventListener('mouseup', () => {
      state.view.isDragging = false;
    });

    // Scroll Wheel to Zoom
    container.addEventListener('wheel', (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
      state.view.zoom = Math.min(8.0, Math.max(0.15, state.view.zoom * zoomFactor));
      renderTrajectoryCanvas();
    }, { passive: false });

    // 10. Collapsible Event Log Header
    el('event-log-toggle').addEventListener('click', () => {
      const body = el('event-log-body');
      const chevron = el('event-log-chevron');
      const isCollapsed = body.classList.toggle('collapsed');
      chevron.textContent = isCollapsed ? '▼' : '▲';
    });

    // 11. Retry Connection Button
    el('btn-retry').addEventListener('click', () => {
      hideError();
      setConnectionStatus('syncing', 'Reconnecting...');
      fetchRuntime().then(applySnapshot).catch(err => {
        showError(`Retry failed: ${err.message}`);
      });
    });

    // 12. Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
      // Ignore if focus is in an input or select
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;

      if (e.code === 'Space') {
        e.preventDefault();
        el('btn-play').click();
      } else if (e.key === 'g' || e.key === 'G') {
        e.preventDefault();
        el('btn-toggle-gnss').click();
      } else if (e.key === 's' || e.key === 'S') {
        e.preventDefault();
        el('btn-step').click();
      } else if (e.key === 'r' || e.key === 'R') {
        e.preventDefault();
        el('btn-restart').click();
      }
    });

    // Window resize handling
    window.addEventListener('resize', () => {
      renderTrajectoryCanvas();
    });
  }

  // --- Bootstrap ---
  async function init() {
    bindInteractions();
    loadHistoricalSummary();
    setConnectionStatus('syncing', 'Initializing Runtime Session...');

    try {
      const initialSnap = await fetchRuntime();
      applySnapshot(initialSnap);
      setConnectionStatus('connected', 'Connected (SDK Runtime)');
      hideError();
    } catch (err) {
      setConnectionStatus('disconnected', 'Disconnected');
      showError(`Initialization error: ${err.message}. Ensure the backend is running with models and dataset.`);
    }

    // Start serial polling
    pollLoop();
  }

  // Execute on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
