// Continuum IDR — Mobile Navigation Fallback Demonstrator Controller
(function() {
  const canvas = document.getElementById("mapCanvas");
  const ctx = canvas.getContext("2d");

  // DOM Elements
  const speedDisplay = document.getElementById("speedDisplay");
  const headingDisplay = document.getElementById("headingDisplay");
  const uncertDisplay = document.getElementById("uncertDisplay");
  const roadSnapDisplay = document.getElementById("roadSnapDisplay");
  const gnssChip = document.getElementById("gnssChip");
  const gnssLabel = document.getElementById("gnssLabel");
  const modeChip = document.getElementById("modeChip");
  const modeLabel = document.getElementById("modeLabel");
  const toastBanner = document.getElementById("toastBanner");
  const btnTunnel = document.getElementById("btnTunnel");
  const tunnelBtnText = document.getElementById("tunnelBtnText");
  const btnStop = document.getElementById("btnStop");
  const stopBtnText = document.getElementById("stopBtnText");

  // Resize canvas
  function resizeCanvas() {
    canvas.width = canvas.parentElement.clientWidth * window.devicePixelRatio;
    canvas.height = canvas.parentElement.clientHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
  }
  window.addEventListener("resize", resizeCanvas);
  resizeCanvas();

  // State Variables
  let isTunnelActive = false;
  let isStopped = false;
  let isReplayingReal = false;
  let realReplayData = null;
  let realReplayIndex = 0;

  let carX = 0.0; // East (m)
  let carY = 0.0; // North (m)
  let carSpeed = 13.3; // m/s (~48 km/h)
  let carHeading = 90.0; // deg (East)
  let uncertaintyRadius = 3.1; // m

  const breadcrumbs = [];
  let toastTimeout = null;

  function showToast(message, type = "danger", duration = 3000) {
    if (toastTimeout) clearTimeout(toastTimeout);
    toastBanner.className = `toast-banner show ${type}`;
    toastBanner.textContent = message;
    toastTimeout = setTimeout(() => {
      toastBanner.classList.remove("show");
    }, duration);
  }

  // Interactive Actions
  window.toggleTunnel = function() {
    isTunnelActive = !isTunnelActive;
    if (isTunnelActive) {
      btnTunnel.classList.add("active-danger");
      tunnelBtnText.textContent = "Exit Tunnel";
      gnssChip.className = "chip danger";
      gnssLabel.textContent = "NO GNSS SIGNAL (0 Sats)";
      modeChip.className = "chip warning";
      modeLabel.textContent = "IDR FALLBACK";
      showToast("🚇 TUNNEL DETECTED — CONTINUUM IDR ACTIVE", "danger", 3500);
    } else {
      btnTunnel.classList.remove("active-danger");
      tunnelBtnText.textContent = "Enter Tunnel";
      gnssChip.className = "chip";
      gnssLabel.textContent = "GNSS RE-ACQUIRED (3.2m)";
      modeChip.className = "chip";
      modeLabel.textContent = "RECOVERING";
      showToast("☀️ GNSS RE-ACQUIRED — SMOOTH KALMAN CONVERGENCE", "success", 3000);
      setTimeout(() => {
        if (!isTunnelActive) {
          modeLabel.textContent = "AIDED";
          uncertaintyRadius = 3.1;
        }
      }, 2500);
    }
  };

  window.toggleTrafficStop = function() {
    isStopped = !isStopped;
    if (isStopped) {
      btnStop.classList.add("active-primary");
      stopBtnText.textContent = "Resume Drive";
      showToast("🚦 VEHICLE STOPPED — ZUPT LOCK (0 DRIFT)", "warning", 2500);
      modeLabel.textContent = "ZUPT ACTIVE";
    } else {
      btnStop.classList.remove("active-primary");
      stopBtnText.textContent = "Traffic Stop";
      modeLabel.textContent = isTunnelActive ? "IDR FALLBACK" : "AIDED";
    }
  };

  window.triggerSpeedBreaker = function() {
    showToast("⚠️ SPEED BREAKER DETECTED (+4.8 m/s²)", "warning", 2500);
    // Temporary vertical dip animation
    carSpeed = Math.max(carSpeed * 0.7, 4.0);
    setTimeout(() => { if (!isStopped) carSpeed = 13.3; }, 1500);
  };

  window.triggerPothole = function() {
    showToast("🕳️ POTHOLE IMPACT DETECTED (-4.2 m/s²)", "danger", 2500);
  };

  window.triggerMountShift = function() {
    showToast("📱 MOUNT SHIFT DETECTED (24° Tilt) — RE-CALIBRATING", "warning", 3000);
    uncertaintyRadius += 4.0;
  };

  window.loadRealReplay = function() {
    if (isReplayingReal) {
      isReplayingReal = false;
      showToast("Real replay stopped", "warning", 1500);
      return;
    }
    fetch("/api/demo")
      .then(res => res.json())
      .then(data => {
        realReplayData = data.steps;
        realReplayIndex = 0;
        isReplayingReal = true;
        showToast("🔄 Streaming Real IO-VNBD Vtb02 Run...", "success", 2500);
      })
      .catch(err => {
        showToast("Error loading demo replay", "danger", 2000);
      });
  };

  // Animation Loop (60 FPS)
  let lastTime = performance.now();

  function animate(now) {
    const dt = Math.min((now - lastTime) / 1000.0, 0.1);
    lastTime = now;

    const w = canvas.parentElement.clientWidth;
    const h = canvas.parentElement.clientHeight;

    // Simulation Physics Step
    if (isReplayingReal && realReplayData && realReplayIndex < realReplayData.length) {
      const step = realReplayData[realReplayIndex];
      carX = step.idr.east_m;
      carY = step.idr.north_m;
      carSpeed = step.idr.speed_mps;
      carHeading = step.idr.heading_deg;
      uncertaintyRadius = step.idr.uncertainty_m;

      if (step.phase === "outage" && !isTunnelActive) {
        toggleTunnel();
      } else if (step.phase === "recovery" && isTunnelActive) {
        toggleTunnel();
      }

      realReplayIndex += 1;
      if (realReplayIndex >= realReplayData.length) {
        isReplayingReal = false;
        showToast("Replay complete!", "success", 2000);
      }
    } else {
      // Normal synthetic drive
      const targetSpeed = isStopped ? 0.0 : 13.3;
      carSpeed += (targetSpeed - carSpeed) * dt * 3.0;

      // Slight gentle road curvature
      const dist = carSpeed * dt;
      carX += dist * Math.sin(carHeading * Math.PI / 180.0);
      carY += dist * Math.cos(carHeading * Math.PI / 180.0);

      if (isTunnelActive && !isStopped) {
        uncertaintyRadius = Math.min(uncertaintyRadius + dt * 0.45, 32.0);
      } else if (!isTunnelActive && !isStopped) {
        uncertaintyRadius = Math.max(uncertaintyRadius - dt * 1.5, 3.1);
      }
    }

    breadcrumbs.push({ x: carX, y: carY, isTunnel: isTunnelActive });
    if (breadcrumbs.length > 250) breadcrumbs.shift();

    // Update Telemetry HUD
    speedDisplay.textContent = Math.round(carSpeed * 3.6);
    headingDisplay.textContent = `${Math.round(carHeading).toString().padStart(3, "0")}°`;
    uncertDisplay.textContent = `±${uncertaintyRadius.toFixed(1)} m`;

    // Render Canvas
    ctx.clearRect(0, 0, w, h);

    // Camera centered on vehicle
    ctx.save();
    ctx.translate(w / 2, h / 2 + 50);
    // Rotate map with vehicle heading so car points UP
    ctx.rotate(-(carHeading - 90) * Math.PI / 180.0);

    // 1. Draw Road Grid & Geometry
    ctx.lineWidth = 1;
    ctx.strokeStyle = "#162036";
    const gridSize = 40;
    const startGridX = Math.floor((carX - 300) / gridSize) * gridSize;
    const endGridX = carX + 300;
    const startGridY = Math.floor((carY - 300) / gridSize) * gridSize;
    const endGridY = carY + 300;

    for (let gx = startGridX; gx <= endGridX; gx += gridSize) {
      ctx.beginPath();
      ctx.moveTo(gx - carX, -300);
      ctx.lineTo(gx - carX, 300);
      ctx.stroke();
    }
    for (let gy = startGridY; gy <= endGridY; gy += gridSize) {
      ctx.beginPath();
      ctx.moveTo(-300, gy - carY);
      ctx.lineTo(300, gy - carY);
      ctx.stroke();
    }

    // 2. Draw Main Road Centerline Corridor
    ctx.lineWidth = 42;
    ctx.strokeStyle = isTunnelActive ? "#1e293b" : "#1e293b";
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(-500, 0);
    ctx.lineTo(500, 0);
    ctx.stroke();

    // Road dashed lane stripes
    ctx.lineWidth = 2;
    ctx.strokeStyle = isTunnelActive ? "#475569" : "#e2e8f0";
    ctx.setLineDash([12, 16]);
    ctx.beginPath();
    ctx.moveTo(-500, 0);
    ctx.lineTo(500, 0);
    ctx.stroke();
    ctx.setLineDash([]);

    // 3. Draw Breadcrumb Trajectory
    if (breadcrumbs.length > 1) {
      for (let i = 1; i < breadcrumbs.length; i++) {
        const p1 = breadcrumbs[i - 1];
        const p2 = breadcrumbs[i];
        ctx.beginPath();
        ctx.moveTo(p1.x - carX, -(p1.y - carY));
        ctx.lineTo(p2.x - carX, -(p2.y - carY));
        ctx.lineWidth = 4;
        ctx.strokeStyle = p2.isTunnel ? "#00d2ff" : "#10b981";
        ctx.stroke();
      }
    }

    // 4. Draw 95% Uncertainty Ellipse Aura around Vehicle
    ctx.beginPath();
    ctx.arc(0, 0, uncertaintyRadius * 2.2, 0, 2 * Math.PI);
    ctx.fillStyle = isTunnelActive ? "rgba(0, 210, 255, 0.15)" : "rgba(16, 185, 129, 0.12)";
    ctx.fill();
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = isTunnelActive ? "rgba(0, 210, 255, 0.6)" : "rgba(16, 185, 129, 0.5)";
    ctx.setLineDash([4, 4]);
    ctx.stroke();
    ctx.setLineDash([]);

    // 5. Draw Vehicle Marker (Arrow Head)
    ctx.save();
    ctx.rotate(Math.PI / 2); // Orient facing up
    ctx.beginPath();
    ctx.moveTo(0, -16);
    ctx.lineTo(12, 14);
    ctx.lineTo(0, 8);
    ctx.lineTo(-12, 14);
    ctx.closePath();
    ctx.fillStyle = isTunnelActive ? "#00d2ff" : "#10b981";
    ctx.shadowColor = isTunnelActive ? "#00d2ff" : "#10b981";
    ctx.shadowBlur = 12;
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = "#fff";
    ctx.stroke();
    ctx.restore();

    ctx.restore();

    requestAnimationFrame(animate);
  }

  requestAnimationFrame(animate);

  // Optional: Read Live Phone Gyroscope/Accelerometer if on mobile HTTPS/localhost
  if (window.DeviceMotionEvent) {
    window.addEventListener("devicemotion", (event) => {
      if (event.acceleration && !isReplayingReal) {
        const az = event.acceleration.z || 0;
        if (az > 4.5) triggerSpeedBreaker();
        else if (az < -4.0) triggerPothole();
      }
    });
  }
})();
