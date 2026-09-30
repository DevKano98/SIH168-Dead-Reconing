const $ = (s) => document.querySelector(s);

let demoData = null;
let summaryData = null;
let currentIndex = 0;
let playbackTimer = null;

// Initialize
Promise.all([
  fetch("/api/demo").then((r) => {
    if (!r.ok) throw new Error("demo_replay.json missing");
    return r.json();
  }),
  fetch("/api/summary").then((r) => {
    if (!r.ok) throw new Error("summary.json missing");
    return r.json();
  }),
])
  .then(([d, s]) => {
    demoData = d;
    summaryData = s;
    setupUI();
    render(0);
  })
  .catch((err) => {
    console.error(err);
    $("#execution").textContent = "Evaluation artifacts unavailable";
    $("#execution").style.color = "#f87171";
  });

function setupUI() {
  const d = demoData;
  const s = summaryData;

  // Header & Info
  $("#execution").textContent = d.execution || "Desktop CPU / Python SDK";
  $("#experiment").textContent = d.experiment_id;
  $("#model").textContent = d.model_id;
  $("#run-id").textContent = d.run_id;
  $("#outage-id").textContent = `${d.outage.outage_id} (${d.outage.reference_distance_m.toFixed(0)}m, ${d.outage.duration_s.toFixed(1)}s)`;

  // Demo Outage Outcome
  const out = d.outage;
  $("#endpoint").textContent = out.endpoint_error_m.toFixed(1);
  $("#drift").textContent = `${out.drift_percent.toFixed(1)}% of distance`;

  if (out.last_speed_gyro_endpoint_error_m !== undefined) {
    $("#b1-endpoint").textContent = out.last_speed_gyro_endpoint_error_m.toFixed(1);
    $("#b1-drift").textContent = `${out.last_speed_gyro_drift_percent.toFixed(1)}% drift`;
  }
  if (out.frozen_endpoint_error_m !== undefined) {
    $("#b0-endpoint").textContent = out.frozen_endpoint_error_m.toFixed(1);
    $("#b0-drift").textContent = `${out.frozen_drift_percent.toFixed(1)}% drift`;
  }

  const passed = out.target_below_10_percent;
  $("#target").textContent = passed ? "PASS" : "NOT MET";
  $("#target").style.color = passed ? "#2dd4bf" : "#fb923c";
  $("#target-sub").textContent = passed ? "Drift < 10% benchmark achieved" : "Screening target (< 10%)";

  // Aggregate Table
  const tbody = $("#aggregate-table-body");
  if (s.by_distance) {
    tbody.innerHTML = "";
    Object.entries(s.by_distance).forEach(([bucket, row]) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${bucket}</strong></td>
        <td>${row.outage_count}</td>
        <td><strong>${row.median_endpoint_error_m.toFixed(1)} m</strong></td>
        <td>${row.p95_endpoint_error_m.toFixed(1)} m</td>
        <td><strong>${row.median_drift_percent.toFixed(1)}%</strong></td>
        <td>${row.baseline_last_speed_median_error_m.toFixed(1)} m</td>
        <td>${row.baseline_frozen_median_error_m.toFixed(1)} m</td>
        <td><span class="badge ${row.pass_rate_below_10_percent > 0 ? 'badge-accent' : ''}">${(row.pass_rate_below_10_percent * 100).toFixed(0)}%</span></td>
      `;
      tbody.appendChild(tr);
    });
  }

  $("#note").textContent = s.note || "";
  $("#seek").max = d.samples.length - 1;
}

function getExtents(samples) {
  const pts = [];
  samples.forEach((s) => {
    pts.push([s.reference_east_m, s.reference_north_m]);
    pts.push([s.east_m, s.north_m]);
    if (s.baseline_east_m !== null && s.baseline_east_m !== undefined) {
      pts.push([s.baseline_east_m, s.baseline_north_m]);
    }
  });
  const xs = pts.map((p) => p[0]);
  const ys = pts.map((p) => p[1]);
  return [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
}

function render(idx) {
  if (!demoData) return;
  currentIndex = Math.max(0, Math.min(idx, demoData.samples.length - 1));
  const s = demoData.samples[currentIndex];

  const canvas = $("#trajectory");
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  canvas.width = w * dpr;
  canvas.height = h * dpr;

  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);

  // Background
  ctx.fillStyle = "#060d17";
  ctx.fillRect(0, 0, w, h);

  const [xmin, xmax, ymin, ymax] = getExtents(demoData.samples);
  const pad = 45;
  const scale = Math.min((w - 2 * pad) / (xmax - xmin || 1), (h - 2 * pad) / (ymax - ymin || 1));
  const toXY = (x, y) => [pad + (x - xmin) * scale, h - pad - (y - ymin) * scale];

  // Grid
  ctx.strokeStyle = "#101e30";
  ctx.lineWidth = 1;
  for (let k = 0; k <= 8; k++) {
    ctx.beginPath();
    ctx.moveTo(0, (k * h) / 8);
    ctx.lineTo(w, (k * h) / 8);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo((k * w) / 8, 0);
    ctx.lineTo((k * w) / 8, h);
    ctx.stroke();
  }

  // Draw Path Helper
  function drawPath(keyX, keyY, color, lineWidth, lineDash = [], maxIndex = demoData.samples.length) {
    ctx.beginPath();
    ctx.setLineDash(lineDash);
    let started = false;
    for (let j = 0; j < maxIndex; j++) {
      const p = demoData.samples[j];
      const vx = p[keyX];
      const vy = p[keyY];
      if (vx === null || vx === undefined || isNaN(vx)) continue;
      const [qx, qy] = toXY(vx, vy);
      if (!started) {
        ctx.moveTo(qx, qy);
        started = true;
      } else {
        ctx.lineTo(qx, qy);
      }
    }
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.stroke();
    ctx.setLineDash([]);
  }

  // 1. Reference path (gray)
  drawPath("reference_east_m", "reference_north_m", "#475569", 2);

  // 2. Outage interval on reference (highlighted orange background)
  const outageSamples = demoData.samples.filter((x) => x.in_outage);
  if (outageSamples.length > 1) {
    ctx.beginPath();
    outageSamples.forEach((p, j) => {
      const [qx, qy] = toXY(p.reference_east_m, p.reference_north_m);
      j === 0 ? ctx.moveTo(qx, qy) : ctx.lineTo(qx, qy);
    });
    ctx.strokeStyle = "rgba(251, 146, 60, 0.4)";
    ctx.lineWidth = 6;
    ctx.stroke();
  }

  // 3. Baseline 0 (Frozen Position marker)
  const firstFrozen = demoData.samples.find((x) => x.frozen_east_m !== null && x.frozen_east_m !== undefined);
  if (firstFrozen && currentIndex >= firstFrozen.index) {
    const [fx, fy] = toXY(firstFrozen.frozen_east_m, firstFrozen.frozen_north_m);
    ctx.beginPath();
    ctx.arc(fx, fy, 4, 0, Math.PI * 2);
    ctx.fillStyle = "#f87171";
    ctx.fill();
  }

  // 4. Baseline 1 (Last Speed + Gyro dashed line)
  if (firstFrozen && currentIndex >= firstFrozen.index) {
    drawPath("baseline_east_m", "baseline_north_m", "#facc15", 1.8, [4, 4], currentIndex + 1);
  }

  // 5. Continuum IDR Estimated Path (bright blue up to current position)
  drawPath("east_m", "north_m", "#38bdf8", 2.8, [], currentIndex + 1);

  // 6. Current vehicle position & uncertainty
  const [curX, curY] = toXY(s.east_m, s.north_m);

  // 95% Uncertainty circle
  const uncRadius = Math.max(8, Math.min(100, (s.uncertainty_m || 5.0) * scale));
  ctx.beginPath();
  ctx.arc(curX, curY, uncRadius, 0, Math.PI * 2);
  ctx.fillStyle = s.in_outage ? "rgba(251, 146, 60, 0.12)" : "rgba(56, 189, 248, 0.12)";
  ctx.fill();
  ctx.strokeStyle = s.in_outage ? "rgba(251, 146, 60, 0.6)" : "rgba(56, 189, 248, 0.6)";
  ctx.lineWidth = 1.5;
  ctx.setLineDash([3, 3]);
  ctx.stroke();
  ctx.setLineDash([]);

  // Heading pointer
  if (s.heading_deg !== null && s.heading_deg !== undefined) {
    const hRad = (s.heading_deg * Math.PI) / 180;
    const len = 18;
    const hx = curX + len * Math.sin(hRad);
    const hy = curY - len * Math.cos(hRad);
    ctx.beginPath();
    ctx.moveTo(curX, curY);
    ctx.lineTo(hx, hy);
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = 2.5;
    ctx.stroke();
  }

  // Vehicle center dot
  ctx.beginPath();
  ctx.arc(curX, curY, 6, 0, Math.PI * 2);
  ctx.fillStyle = s.in_outage ? "#fb923c" : s.mode === "RECOVERING" ? "#38bdf8" : "#2dd4bf";
  ctx.fill();
  ctx.strokeStyle = "#ffffff";
  ctx.lineWidth = 1.5;
  ctx.stroke();

  // Update Telemetry Panel
  const modeEl = $("#mode");
  modeEl.textContent = s.mode;
  modeEl.className = "mode-value " + (s.in_outage ? "mode-dr" : s.mode === "RECOVERING" ? "mode-rec" : "");

  $("#speed").textContent = s.speed_mps !== null && s.speed_mps !== undefined ? s.speed_mps.toFixed(1) : "—";
  $("#speed-kmh").textContent = s.speed_mps !== null && s.speed_mps !== undefined ? `${(s.speed_mps * 3.6).toFixed(0)} km/h` : "— km/h";
  $("#error").textContent = s.error_m !== null && s.error_m !== undefined ? s.error_m.toFixed(1) : "—";
  $("#uncertainty").textContent = s.uncertainty_m !== null && s.uncertainty_m !== undefined ? s.uncertainty_m.toFixed(1) : "—";

  const gnssEl = $("#gnss");
  gnssEl.textContent = s.gnss_delivered ? "ACCEPTED FIX" : s.in_outage ? "WITHHELD" : "AIDING";
  gnssEl.style.color = s.in_outage ? "#fb923c" : s.gnss_delivered ? "#2dd4bf" : "#94a3b8";
  $("#decision").textContent = s.gnss_decision || "AIDING";

  // Event Banner Update
  const banner = $("#event-banner");
  const bText = $("#banner-text");
  if (s.in_outage) {
    banner.className = "event-banner in-outage";
    bText.textContent = "⚡ SIMULATED GNSS OUTAGE (TUNNEL BLACKOUT) — RUNNING ML DEAD RECKONING";
  } else if (s.mode === "RECOVERING") {
    banner.className = "event-banner recovering";
    bText.textContent = "✓ GNSS RESTORED — ESTIMATOR CONVERGING SMOOTHLY";
  } else {
    banner.className = "event-banner";
    bText.textContent = "● GNSS-AIDED NAVIGATION ACTIVE";
  }

  // Outage progress bar
  const first = outageSamples[0]?.index;
  const last = outageSamples.at(-1)?.index;
  let progress = 0;
  if (first !== undefined && last !== undefined) {
    progress = s.index < first ? 0 : s.index > last ? 1 : (s.index - first) / (last - first);
  }
  $("#outage-bar").style.width = `${progress * 100}%`;
  $("#outage-distance").textContent = `${demoData.outage.reference_distance_m.toFixed(0)} m tunnel`;

  if (s.index < first) {
    $("#outage-status").textContent = "Pre-outage aided warm-up";
    $("#outage-timer").textContent = "0.0 s";
  } else if (s.index <= last) {
    const elapsedOutage = s.time_s - demoData.samples[first].time_s;
    $("#outage-status").textContent = `In blackout (${(progress * 100).toFixed(0)}%)`;
    $("#outage-timer").textContent = `${elapsedOutage.toFixed(1)} s`;
  } else {
    $("#outage-status").textContent = "GNSS recovered";
    $("#outage-timer").textContent = `${demoData.outage.duration_s.toFixed(1)} s`;
  }

  // Timeline & Clock
  $("#seek").value = currentIndex;
  const elapsedTotal = s.time_s - demoData.samples[0].time_s;
  const mins = Math.floor(elapsedTotal / 60);
  const secs = (elapsedTotal % 60).toFixed(1);
  $("#clock").textContent = `${String(mins).padStart(2, "0")}:${secs.padStart(4, "0")}`;
}

function play() {
  if (playbackTimer) {
    clearInterval(playbackTimer);
    playbackTimer = null;
    $("#play").textContent = "▶ Play";
    return;
  }
  $("#play").textContent = "❚❚ Pause";
  const rate = Number($("#rate").value) || 2;
  const intervalMs = 100 / rate;

  playbackTimer = setInterval(() => {
    if (currentIndex >= demoData.samples.length - 1) {
      clearInterval(playbackTimer);
      playbackTimer = null;
      $("#play").textContent = "▶ Play";
      return;
    }
    render(currentIndex + 1);
  }, intervalMs);
}

// Event Listeners
$("#play").onclick = play;
$("#reset").onclick = () => {
  if (playbackTimer) play();
  render(0);
};

$("#seek").oninput = (e) => {
  render(Number(e.target.value));
};

$("#rate").onchange = () => {
  if (playbackTimer) {
    play();
    play();
  }
};

$("#outage").onclick = () => {
  const i = demoData.samples.findIndex((s) => s.in_outage);
  render(Math.max(0, i - 15));
  if (!playbackTimer) play();
};

$("#restore").onclick = () => {
  const i = demoData.samples.findIndex(
    (s, j) => j > 0 && demoData.samples[j - 1].in_outage && !s.in_outage
  );
  render(Math.max(0, i - 15));
  if (!playbackTimer) play();
};

window.addEventListener("keydown", (e) => {
  if (e.code === "Space") {
    e.preventDefault();
    play();
  } else if (e.code === "ArrowLeft") {
    render(currentIndex - 10);
  } else if (e.code === "ArrowRight") {
    render(currentIndex + 10);
  }
});

window.addEventListener("resize", () => {
  render(currentIndex);
});
