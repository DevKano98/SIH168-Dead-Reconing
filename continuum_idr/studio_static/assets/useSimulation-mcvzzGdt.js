import{c as p,r as t}from"./index-D2sy93KJ.js";/**
 * @license lucide-react v0.469.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const A=p("Pause",[["rect",{x:"14",y:"4",width:"4",height:"16",rx:"1",key:"zuxfzm"}],["rect",{x:"6",y:"4",width:"4",height:"16",rx:"1",key:"1okwgv"}]]);/**
 * @license lucide-react v0.469.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const F=p("Play",[["polygon",{points:"6 3 20 12 6 21 6 3",key:"1oa8hb"}]]);/**
 * @license lucide-react v0.469.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $=p("RotateCcw",[["path",{d:"M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8",key:"1357e3"}],["path",{d:"M3 3v5h5",key:"1xhq8a"}]]);/**
 * @license lucide-react v0.469.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const D=p("Satellite",[["path",{d:"M13 7 9 3 5 7l4 4",key:"vyckw6"}],["path",{d:"m17 11 4 4-4 4-4-4",key:"rchckc"}],["path",{d:"m8 12 4 4 6-6-4-4Z",key:"1sshf7"}],["path",{d:"m16 8 3-3",key:"x428zp"}],["path",{d:"M9 21a6 6 0 0 0-6-6",key:"1iajcf"}]]);/**
 * @license lucide-react v0.469.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const G=p("StepForward",[["line",{x1:"6",x2:"6",y1:"4",y2:"20",key:"fy8qot"}],["polygon",{points:"10,4 20,12 10,20",key:"1mc1pf"}]]);async function T(){const n=await fetch("/api/runtime",{method:"GET",headers:{Accept:"application/json"},cache:"no-store"});if(!n.ok){let e=`Runtime error (${n.status})`;try{const a=await n.json();a.detail&&(e=a.detail)}catch{}throw new Error(e)}return n.json()}async function M(n,e=null){const a={action:n};e!=null&&(a.value=e);const i=await fetch("/api/runtime/control",{method:"POST",headers:{"Content-Type":"application/json",Accept:"application/json"},body:JSON.stringify(a)});if(!i.ok){let c=`Control failed (${i.status})`;try{const u=await i.json();u.detail&&(c=u.detail)}catch{}throw new Error(c)}return i.json()}async function I(){const n=await fetch("/api/summary",{method:"GET",headers:{Accept:"application/json"},cache:"no-store"});if(!n.ok){let e=`Summary error (${n.status})`;try{const a=await n.json();a.detail&&(e=a.detail)}catch{}throw new Error(e)}return n.json()}const O="/api/runtime/export";function z(n=250){const[e,a]=t.useState(null),[i,c]=t.useState("connecting"),[u,f]=t.useState(null),[C,w]=t.useState(!1),y=t.useRef(!1),h=t.useRef(null),o=t.useRef(!0),l=t.useCallback(async()=>{if(o.current){if(y.current){h.current=setTimeout(l,150);return}try{const s=await T();o.current&&(a(s),c("connected"),f(null))}catch(s){o.current&&(c("error"),f(s.message||"Unable to connect to Continuum Python SDK runtime"))}finally{o.current&&(h.current=setTimeout(l,n))}}},[n]);t.useEffect(()=>(o.current=!0,l(),()=>{o.current=!1,h.current&&clearTimeout(h.current)}),[l]);const r=t.useCallback(async(s,P=null)=>{if(!y.current){y.current=!0,w(!0),c("syncing");try{const g=await M(s,P);o.current&&(a(g),c("connected"),f(null))}catch(g){o.current&&f(`Action "${s}" failed: ${g.message}`)}finally{y.current=!1,o.current&&w(!1)}}},[]),d=t.useCallback(()=>r("play"),[r]),m=t.useCallback(()=>r("pause"),[r]),S=t.useCallback(()=>{e&&(e.completed||(e.playing?m():d()))},[e,d,m]),b=t.useCallback((s=25)=>r("step",s),[r]),k=t.useCallback(s=>r("gnss",s),[r]),R=t.useCallback(()=>{e&&k(!e.gnss_enabled)},[e,k]),x=t.useCallback(()=>r("restart"),[r]),j=t.useCallback(s=>r("rate",s),[r]),E=t.useCallback(()=>{f(null),c("connecting"),l()},[l]);return{snapshot:e,connectionStatus:i,errorMessage:u,isControlInFlight:C,play:d,pause:m,togglePlay:S,step:b,setGnss:k,toggleGnss:R,restart:x,setRate:j,retryConnection:E}}export{O as E,F as P,$ as R,D as S,A as a,G as b,I as f,z as u};
