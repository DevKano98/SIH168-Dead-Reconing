const driver = {
  demo: null,
  index: 0,
  playing: false,
};

const el = (id) => document.getElementById(id);
const valid = (value) => Number.isFinite(Number(value));
const fmt = (value, digits = 1) => valid(value) ? Number(value).toFixed(digits) : "—";

async function initDriver() {
  try {
    const response = await fetch("/api/demo");
    if (!response.ok) throw new Error("Replay unavailable");
    driver.demo = await response.json();
    renderDriver(0);
    bindDriverControls();
    window.setInterval(syncDriver, 120);
    window.addEventListener("resize", () => renderDriver(driver.index));
  } catch (error) {
    el("driver-message").textContent = error.message;
    el("driver-submessage").textContent = "Generate evaluation artifacts, then reload this view.";
  }
}

async function sessionControl(action, value) {
  const response = await fetch("/api/session/control", {
    method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({action, value}),
  });
  if (response.ok) applySession(await response.json());
}

async function syncDriver() {
  try {
    const response = await fetch("/api/session", {cache:"no-store"});
    if (response.ok) applySession(await response.json());
  } catch (_) { /* Studio server status is already visible in the UI. */ }
}

function applySession(session) {
  driver.playing = Boolean(session.playing);
  el("driver-play").textContent = driver.playing ? "Pause synchronized replay" : "Start synchronized replay";
  if (session.index !== driver.index) renderDriver(session.index);
}

function bindDriverControls() {
  el("driver-play").addEventListener("click", () => sessionControl(driver.playing ? "pause" : "play"));
  el("driver-reset").addEventListener("click", () => sessionControl("restart"));
}

function canvasSetup(canvas) {
  const dpr = window.devicePixelRatio || 1, width = canvas.clientWidth, height = canvas.clientHeight;
  canvas.width = Math.round(width*dpr); canvas.height = Math.round(height*dpr);
  const context=canvas.getContext("2d");context.setTransform(dpr,0,0,dpr,0,0);return {context,width,height};
}

function driverExtents() {
  const xs=[],ys=[];driver.demo.samples.forEach(s=>{if(valid(s.reference_east_m)&&valid(s.reference_north_m)){xs.push(Number(s.reference_east_m));ys.push(Number(s.reference_north_m));}});
  return [Math.min(...xs),Math.max(...xs),Math.min(...ys),Math.max(...ys)];
}

function drawDriverMap(index) {
  const canvas=el("driver-map"),{context:ctx,width,height}=canvasSetup(canvas),[xmin,xmax,ymin,ymax]=driverExtents();
  const spanX=Math.max(1,xmax-xmin),spanY=Math.max(1,ymax-ymin),scale=Math.min(width*.78/spanX,height*.64/spanY),toXY=(x,y)=>[width/2+(x-(xmin+xmax)/2)*scale,height*.42-(y-(ymin+ymax)/2)*scale];
  ctx.fillStyle="#091522";ctx.fillRect(0,0,width,height);
  ctx.strokeStyle="rgba(85,113,141,.11)";ctx.lineWidth=1;for(let x=-height;x<width+height;x+=55){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x+height,height);ctx.stroke();}
  drawPath(ctx,"reference_east_m","reference_north_m",driver.demo.samples.length,toXY,"#172a3c",20,[]);drawPath(ctx,"reference_east_m","reference_north_m",driver.demo.samples.length,toXY,"#344d65",2,[9,12]);drawPath(ctx,"east_m","north_m",index+1,toXY,"#4ca5ff",4,[]);
  const s=driver.demo.samples[index],[x,y]=toXY(s.east_m,s.north_m),radius=Math.max(12,Math.min(70,(Number(s.uncertainty_m)||0)*scale));ctx.beginPath();ctx.arc(x,y,radius,0,Math.PI*2);ctx.fillStyle=s.in_outage?"rgba(255,180,92,.13)":"rgba(76,165,255,.12)";ctx.fill();ctx.strokeStyle=s.in_outage?"rgba(255,180,92,.55)":"rgba(76,165,255,.5)";ctx.setLineDash([4,4]);ctx.stroke();ctx.setLineDash([]);
  const heading=(Number(s.heading_deg)||0)*Math.PI/180;ctx.save();ctx.translate(x,y);ctx.rotate(heading);ctx.beginPath();ctx.moveTo(0,-15);ctx.lineTo(10,11);ctx.lineTo(0,7);ctx.lineTo(-10,11);ctx.closePath();ctx.fillStyle="#fff";ctx.shadowColor="#4ca5ff";ctx.shadowBlur=18;ctx.fill();ctx.restore();
  function drawPath(c,kx,ky,count,convert,color,lineWidth,dash){c.beginPath();c.setLineDash(dash);let start=false;driver.demo.samples.slice(0,count).forEach(p=>{if(!valid(p[kx])||!valid(p[ky]))return;const [px,py]=convert(p[kx],p[ky]);start?c.lineTo(px,py):(c.moveTo(px,py),start=true)});c.strokeStyle=color;c.lineWidth=lineWidth;c.lineCap="round";c.lineJoin="round";c.stroke();c.setLineDash([]);}
}

function renderDriver(index) {
  if(!driver.demo)return;driver.index=Math.max(0,Math.min(driver.demo.samples.length-1,Number(index)||0));const s=driver.demo.samples[driver.index];
  const phase=s.in_outage?"outage":s.phase==="recovery"?"recovery":"aided",state=el("driver-state");state.className=`driver-state ${phase}`;
  if(phase==="outage"){el("driver-message").textContent="Satellite positioning unavailable";el("driver-submessage").textContent="Continuum is estimating motion from the recorded IMU stream.";}
  else if(phase==="recovery"){el("driver-message").textContent="Satellite positioning restored";el("driver-submessage").textContent="The estimator is validating returning location fixes.";}
  else{el("driver-message").textContent="Positioning available";el("driver-submessage").textContent="GNSS and inertial estimates are running together.";}
  el("driver-speed").textContent=fmt(Number(s.speed_mps)*3.6,0);el("driver-mode").textContent=s.mode.replaceAll("_"," ");el("driver-mode").style.color=phase==="outage"?"var(--amber)":phase==="recovery"?"var(--blue-2)":"var(--green)";el("driver-heading").textContent=`${fmt(s.heading_deg,0)}°`;el("driver-uncertainty").textContent=`±${fmt(s.uncertainty_m)} m`;el("driver-gnss").textContent=s.in_outage?"Withheld":s.gnss_delivered?"New fix":"Monitoring";drawDriverMap(driver.index);
}

initDriver();
