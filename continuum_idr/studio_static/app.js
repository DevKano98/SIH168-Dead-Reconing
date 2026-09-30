const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

let demo = null;
let summary = null;
let currentIndex = 0;
let localPlaying = false;
let sessionAvailable = true;
let activeLayers = new Set(["estimate", "reference", "baselines"]);
let pollTimer = null;

function finite(value) { return Number.isFinite(Number(value)); }
function number(value, digits = 1) { return finite(value) ? Number(value).toFixed(digits) : "—"; }
function formatTime(seconds) {
  const safe = Math.max(0, Number(seconds) || 0);
  const minutes = Math.floor(safe / 60);
  return `${String(minutes).padStart(2, "0")}:${(safe % 60).toFixed(1).padStart(4, "0")}`;
}

async function load() {
  try {
    const [demoResponse, summaryResponse] = await Promise.all([fetch("/api/demo"), fetch("/api/summary")]);
    if (!demoResponse.ok || !summaryResponse.ok) throw new Error("Evaluation artifacts are unavailable");
    [demo, summary] = await Promise.all([demoResponse.json(), summaryResponse.json()]);
    setupStaticContent();
    bindControls();
    await syncSession();
    render(currentIndex);
    pollTimer = window.setInterval(syncSession, 120);
    $("#loading").classList.add("hidden");
  } catch (error) {
    $("#loading").innerHTML = `<strong>Studio could not load</strong><span>${error.message}. Run the evaluation command and refresh.</span>`;
  }
}

function setupStaticContent() {
  const outage = demo.outage;
  $("#run-id").textContent = demo.run_id;
  $("#outage-id").textContent = `${outage.outage_id} · ${number(outage.reference_distance_m, 0)} m`;
  $("#model").textContent = demo.model_id;
  $("#experiment").textContent = demo.experiment_id;
  $("#execution").textContent = demo.execution || "Desktop CPU / Python SDK";
  $("#selection-rule").textContent = demo.selection_rule || "Representative evaluation outage";

  $("#endpoint").textContent = number(outage.endpoint_error_m);
  $("#drift").textContent = number(outage.drift_percent);
  $("#reference-distance").textContent = number(outage.reference_distance_m, 0);
  $("#target-badge").textContent = outage.target_below_10_percent ? "TARGET MET" : "TARGET NOT MET";
  $("#target-badge").classList.toggle("pass", Boolean(outage.target_below_10_percent));

  const comparisons = [
    ["Continuum IDR", outage.endpoint_error_m, "continuum"],
    ["Last speed + gyro", outage.last_speed_gyro_endpoint_error_m, "baseline"],
    ["Frozen position", outage.frozen_endpoint_error_m, "frozen"],
  ];
  const maximum = Math.max(...comparisons.map(([, value]) => Number(value) || 0), 1);
  $("#comparison-bars").innerHTML = comparisons.map(([label, value, className]) => `
    <div class="bar-row ${className}"><span>${label}</span><div class="bar-track"><i style="width:${Math.max(3, 100 * value / maximum)}%"></i></div><strong>${number(value)} m</strong></div>
  `).join("");

  $("#test-runs").textContent = summary.independent_test_runs;
  $("#outage-count").textContent = summary.total_outages_evaluated;
  $("#median-error").textContent = `${number(summary.overall.median_endpoint_error_m)} m`;
  $("#median-drift").textContent = `${number(summary.overall.median_drift_percent)}%`;
  $("#pass-rate").textContent = `${number(summary.overall.pass_rate_below_10_percent * 100, 0)}%`;
  $("#benchmark-note").textContent = summary.note;
  $("#aggregate-table-body").innerHTML = Object.entries(summary.by_distance).map(([distance, row]) => `
    <tr><td><strong>${distance}</strong></td><td>${row.outage_count}</td><td>${number(row.median_endpoint_error_m)} m</td><td>${number(row.baseline_last_speed_median_error_m)} m</td><td>${number(row.baseline_frozen_median_error_m)} m</td><td>${number(row.median_drift_percent)}%</td><td>${number(row.pass_rate_below_10_percent * 100, 0)}%</td></tr>
  `).join("");

  $("#seek").max = Math.max(0, demo.samples.length - 1);
  const duration = demo.samples.at(-1).time_s - demo.samples[0].time_s;
  $("#duration").textContent = formatTime(duration);
}

async function control(action, value) {
  try {
    const response = await fetch("/api/session/control", {
      method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({action, value}),
    });
    if (!response.ok) throw new Error("Session control failed");
    sessionAvailable = true;
    const state = await response.json();
    applySession(state);
  } catch (error) {
    sessionAvailable = false;
    if (action === "seek" || action === "restart") render(action === "restart" ? 0 : Number(value));
  }
}

async function syncSession() {
  try {
    const response = await fetch("/api/session", {cache: "no-store"});
    if (!response.ok) throw new Error("No shared session");
    sessionAvailable = true;
    applySession(await response.json());
  } catch (_) {
    sessionAvailable = false;
  }
}

function applySession(state) {
  localPlaying = Boolean(state.playing);
  $("#play").innerHTML = localPlaying ? "<span>Ⅱ</span><b>Pause replay</b>" : "<span>▶</span><b>Play replay</b>";
  if (String(state.rate) !== $("#rate").value) $("#rate").value = String(state.rate);
  if (state.index !== currentIndex) render(state.index);
}

function bindControls() {
  $("#play").addEventListener("click", () => control(localPlaying ? "pause" : "play"));
  $("#reset").addEventListener("click", () => control("restart"));
  $("#seek").addEventListener("input", (event) => control("seek", Number(event.target.value)));
  $("#rate").addEventListener("change", (event) => control("rate", Number(event.target.value)));
  $("#jump-outage").addEventListener("click", () => jumpToPhase("outage"));
  $("#jump-recovery").addEventListener("click", () => jumpToPhase("recovery"));
  $("#fit-map").addEventListener("click", () => render(currentIndex));
  $("#open-overview").addEventListener("click", () => $("#overview-dialog").showModal());
  $("#close-overview").addEventListener("click", () => $("#overview-dialog").close());
  $$("[data-layer]").forEach((button) => button.addEventListener("click", () => {
    const layer = button.dataset.layer;
    if (activeLayers.has(layer)) activeLayers.delete(layer); else activeLayers.add(layer);
    button.classList.toggle("selected", activeLayers.has(layer));
    render(currentIndex);
  }));
  window.addEventListener("resize", () => render(currentIndex));
  window.addEventListener("keydown", (event) => {
    if (event.code === "Space" && !event.target.matches("input,select,button")) { event.preventDefault(); control(localPlaying ? "pause" : "play"); }
  });
}

function jumpToPhase(phase) {
  const index = demo.samples.findIndex((sample) => sample.phase === phase);
  control("seek", Math.max(0, index - 12));
  window.setTimeout(() => control("play"), 80);
}

function extents(samples, index) {
  const points = [];
  samples.forEach((sample, sampleIndex) => {
    const candidates = [[sample.reference_east_m, sample.reference_north_m]];
    if (sampleIndex <= index) {
      candidates.push([sample.east_m, sample.north_m], [sample.baseline_east_m, sample.baseline_north_m]);
    }
    candidates.forEach(([x,y]) => {
      if (finite(x) && finite(y)) points.push([Number(x), Number(y)]);
    });
  });
  const xs = points.map(([x]) => x), ys = points.map(([,y]) => y);
  return [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
}

function canvasContext(canvas) {
  const dpr = window.devicePixelRatio || 1;
  const width = canvas.clientWidth, height = canvas.clientHeight;
  canvas.width = Math.round(width * dpr); canvas.height = Math.round(height * dpr);
  const context = canvas.getContext("2d"); context.setTransform(dpr,0,0,dpr,0,0);
  return {context, width, height};
}

function drawTrajectory(index) {
  const canvas = $("#trajectory"), {context: ctx, width, height} = canvasContext(canvas);
  const [xmin,xmax,ymin,ymax] = extents(demo.samples, index);
  const pad = 55, spanX = Math.max(1,xmax-xmin), spanY = Math.max(1,ymax-ymin);
  const scale = Math.min((width-pad*2)/spanX,(height-pad*2)/spanY);
  const toXY = (x,y) => [pad+(x-xmin)*scale,height-pad-(y-ymin)*scale];
  ctx.fillStyle="#091522";ctx.fillRect(0,0,width,height);

  // Quiet metric map grid and a broad road corridor based on the reference route.
  ctx.strokeStyle="rgba(92,126,158,.12)";ctx.lineWidth=1;
  for(let x=0;x<width;x+=48){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,height);ctx.stroke();}
  for(let y=0;y<height;y+=48){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(width,y);ctx.stroke();}
  path(ctx,"reference_east_m","reference_north_m",demo.samples.length,toXY,"#17283a",18,[]);
  path(ctx,"reference_east_m","reference_north_m",demo.samples.length,toXY,"#30465d",2,[10,12]);

  const outage = demo.samples.filter((sample) => sample.in_outage);
  drawArrayPath(ctx,outage,"reference_east_m","reference_north_m",toXY,"rgba(255,180,92,.22)",11,[]);
  if(activeLayers.has("reference")) path(ctx,"reference_east_m","reference_north_m",demo.samples.length,toXY,"#e2eaf2",2,[]);
  if(activeLayers.has("baselines")) path(ctx,"baseline_east_m","baseline_north_m",index+1,toXY,"#ffb45c",2,[6,6]);
  if(activeLayers.has("estimate")) path(ctx,"east_m","north_m",index+1,toXY,"#4ca5ff",3,[]);

  const sample=demo.samples[index], [x,y]=toXY(sample.east_m,sample.north_m);
  const radius=Math.max(9,Math.min(90,(Number(sample.uncertainty_m)||0)*scale));
  ctx.beginPath();ctx.arc(x,y,radius,0,Math.PI*2);ctx.fillStyle=sample.in_outage?"rgba(255,180,92,.12)":"rgba(76,165,255,.11)";ctx.fill();ctx.strokeStyle=sample.in_outage?"rgba(255,180,92,.55)":"rgba(76,165,255,.48)";ctx.setLineDash([4,4]);ctx.stroke();ctx.setLineDash([]);
  const heading=(Number(sample.heading_deg)||0)*Math.PI/180;
  ctx.save();ctx.translate(x,y);ctx.rotate(heading);ctx.beginPath();ctx.moveTo(0,-13);ctx.lineTo(9,10);ctx.lineTo(0,6);ctx.lineTo(-9,10);ctx.closePath();ctx.fillStyle="#f7fbff";ctx.shadowColor="#4ca5ff";ctx.shadowBlur=15;ctx.fill();ctx.restore();
  $("#scale-label").textContent=`1 px ≈ ${number(1/scale,1)} m`;
}

function path(ctx,keyX,keyY,count,toXY,color,width,dash){drawArrayPath(ctx,demo.samples.slice(0,count),keyX,keyY,toXY,color,width,dash);}
function drawArrayPath(ctx,samples,keyX,keyY,toXY,color,width,dash){ctx.beginPath();ctx.setLineDash(dash);let started=false;samples.forEach(sample=>{if(!finite(sample[keyX])||!finite(sample[keyY]))return;const [x,y]=toXY(Number(sample[keyX]),Number(sample[keyY]));if(!started){ctx.moveTo(x,y);started=true}else ctx.lineTo(x,y);});ctx.strokeStyle=color;ctx.lineWidth=width;ctx.lineCap="round";ctx.lineJoin="round";ctx.stroke();ctx.setLineDash([]);}

function drawErrorChart(index) {
  const canvas=$("#error-chart"),{context:ctx,width,height}=canvasContext(canvas), values=demo.samples.map(sample=>Number(sample.error_m)||0);
  const max=Math.max(...values,1),pad=8;
  ctx.clearRect(0,0,width,height);ctx.strokeStyle="rgba(143,163,187,.12)";ctx.lineWidth=1;
  [0,.5,1].forEach(f=>{const y=pad+(height-pad*2)*f;ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(width,y);ctx.stroke();});
  const xy=(i,v)=>[pad+i/(values.length-1)*(width-pad*2),height-pad-v/max*(height-pad*2)];
  ctx.beginPath();values.forEach((v,i)=>{const [x,y]=xy(i,v);i?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.strokeStyle="#4ca5ff";ctx.lineWidth=2;ctx.stroke();
  const [markerX]=xy(index,values[index]);ctx.beginPath();ctx.moveTo(markerX,pad);ctx.lineTo(markerX,height-pad);ctx.strokeStyle="#e9f2fb";ctx.lineWidth=1;ctx.stroke();
  $("#chart-current").textContent=`${number(values[index])} m`;
}

function render(requestedIndex) {
  if(!demo)return;
  currentIndex=Math.max(0,Math.min(demo.samples.length-1,Number(requestedIndex)||0));
  const sample=demo.samples[currentIndex], first=demo.samples.findIndex(s=>s.in_outage), last=demo.samples.findLastIndex(s=>s.in_outage);
  const phase=sample.in_outage?"outage":sample.phase==="recovery"?"recovery":"aided";
  const label=phase==="outage"?"GNSS blackout":phase==="recovery"?"GNSS recovery":"GNSS aided";
  $("#mode").textContent=sample.mode.replaceAll("_"," ");$("#map-status").className=`map-status ${phase}`;
  $("#phase-title").textContent=label;$("#phase-pill").textContent=phase==="outage"?"GNSS WITHHELD":phase==="recovery"?"RECOVERING":"GNSS AIDED";$("#phase-pill").className=`phase-pill ${phase}`;
  $("#speed").textContent=number(Number(sample.speed_mps)*3.6,0);const refSpeed=Number(sample.reference_speed_mps)*3.6;$("#speed-delta").textContent=finite(refSpeed)?`Reference ${number(refSpeed,0)} km/h`:"Reference unavailable";
  $("#error").textContent=`${number(sample.error_m)} m`;$("#uncertainty").textContent=`±${number(sample.uncertainty_m)} m`;$("#heading").textContent=`${number(sample.heading_deg,0)}°`;$("#gnss").textContent=sample.in_outage?"Withheld":sample.gnss_delivered?"New fix delivered":"No new fix";$("#decision").textContent=sample.gnss_decision||"—";
  const progress=currentIndex<first?0:currentIndex>last?1:(currentIndex-first)/Math.max(1,last-first);$("#outage-bar").style.width=`${progress*100}%`;$("#outage-progress-label").textContent=currentIndex<first?"Not started":currentIndex<=last?`${number(progress*100,0)}% complete`:"Completed";$("#outage-timer").textContent=currentIndex<first?"0.0 s":`${number(Math.min(sample.time_s-demo.samples[first].time_s,demo.outage.duration_s))} s`;$("#outage-distance").textContent=`${number(demo.outage.reference_distance_m,0)} m interval`;
  const card=$("#event-card");card.className=`event-card ${phase}`;$("#event-label").textContent=phase==="outage"?"GNSS measurements withheld":phase==="recovery"?"Measurements restored":"Reference fix monitoring";$("#event-copy").textContent=phase==="outage"?"The saved engine trace continues from IMU and learned motion updates.":phase==="recovery"?"Returning fixes are being checked by the running estimator.":"The engine is using accepted fixes to maintain its absolute state.";
  $("#seek").value=currentIndex;$("#clock").textContent=formatTime(sample.time_s-demo.samples[0].time_s);
  drawTrajectory(currentIndex);drawErrorChart(currentIndex);
}

load();
