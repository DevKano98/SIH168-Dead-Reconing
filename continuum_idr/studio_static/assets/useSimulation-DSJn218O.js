import{c as p,r as t}from"./index-Cgf9vepX.js";/**
 * @license lucide-react v0.469.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const D=p("Pause",[["rect",{x:"14",y:"4",width:"4",height:"16",rx:"1",key:"zuxfzm"}],["rect",{x:"6",y:"4",width:"4",height:"16",rx:"1",key:"1okwgv"}]]);/**
 * @license lucide-react v0.469.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const G=p("Play",[["polygon",{points:"6 3 20 12 6 21 6 3",key:"1oa8hb"}]]);/**
 * @license lucide-react v0.469.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _=p("RotateCcw",[["path",{d:"M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8",key:"1357e3"}],["path",{d:"M3 3v5h5",key:"1xhq8a"}]]);/**
 * @license lucide-react v0.469.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const I=p("Satellite",[["path",{d:"M13 7 9 3 5 7l4 4",key:"vyckw6"}],["path",{d:"m17 11 4 4-4 4-4-4",key:"rchckc"}],["path",{d:"m8 12 4 4 6-6-4-4Z",key:"1sshf7"}],["path",{d:"m16 8 3-3",key:"x428zp"}],["path",{d:"M9 21a6 6 0 0 0-6-6",key:"1iajcf"}]]);/**
 * @license lucide-react v0.469.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const q=p("StepForward",[["line",{x1:"6",x2:"6",y1:"4",y2:"20",key:"fy8qot"}],["polygon",{points:"10,4 20,12 10,20",key:"1mc1pf"}]]);async function A(){const s=await fetch("/api/runtime",{method:"GET",headers:{Accept:"application/json"},cache:"no-store"});if(!s.ok){let e=`Runtime error (${s.status})`;try{const r=await s.json();r.detail&&(e=r.detail)}catch{}throw new Error(e)}return s.json()}async function F(s,e=null){const r={action:s};e!=null&&(r.value=e);const i=await fetch("/api/runtime/control",{method:"POST",headers:{"Content-Type":"application/json",Accept:"application/json"},body:JSON.stringify(r)});if(!i.ok){let c=`Control failed (${i.status})`;try{const u=await i.json();u.detail&&(c=u.detail)}catch{}throw new Error(c)}return i.json()}async function L(){const s=await fetch("/api/summary",{method:"GET",headers:{Accept:"application/json"},cache:"no-store"});if(!s.ok){let e=`Summary error (${s.status})`;try{const r=await s.json();r.detail&&(e=r.detail)}catch{}throw new Error(e)}return s.json()}function N(s=250){const[e,r]=t.useState(null),[i,c]=t.useState("connecting"),[u,f]=t.useState(null),[w,C]=t.useState(!1),y=t.useRef(!1),h=t.useRef(null),o=t.useRef(!0),l=t.useCallback(async()=>{if(o.current){if(y.current){h.current=setTimeout(l,150);return}try{const a=await A();o.current&&(r(a),c("connected"),f(null))}catch(a){o.current&&(c("error"),f(a.message||"Unable to connect to Continuum Python SDK runtime"))}finally{o.current&&(h.current=setTimeout(l,s))}}},[s]);t.useEffect(()=>(o.current=!0,l(),()=>{o.current=!1,h.current&&clearTimeout(h.current)}),[l]);const n=t.useCallback(async(a,z=null)=>{if(!y.current){y.current=!0,C(!0),c("syncing");try{const g=await F(a,z);o.current&&(r(g),c("connected"),f(null))}catch(g){o.current&&f(`Action "${a}" failed: ${g.message}`)}finally{y.current=!1,o.current&&C(!1)}}},[]),d=t.useCallback(()=>n("play"),[n]),k=t.useCallback(()=>n("pause"),[n]),b=t.useCallback(()=>{e&&(e.completed||(e.playing?k():d()))},[e,d,k]),S=t.useCallback((a=25)=>n("step",a),[n]),m=t.useCallback(a=>n("gnss",a),[n]),x=t.useCallback(()=>{e&&m(!e.gnss_enabled)},[e,m]),R=t.useCallback(()=>n("restart"),[n]),j=t.useCallback(()=>n("randomize"),[n]),E=t.useCallback(a=>{n("noise",a)},[n]),P=t.useCallback(a=>{n("scenario",a)},[n]),T=t.useCallback(a=>n("rate",a),[n]),M=t.useCallback(()=>{f(null),c("connecting"),l()},[l]);return{snapshot:e,connectionStatus:i,errorMessage:u,isControlInFlight:w,play:d,pause:k,togglePlay:b,step:S,setGnss:m,toggleGnss:x,restart:R,randomize:j,toggleNoise:E,setScenario:P,setRate:T,retryConnection:M}}export{D as P,_ as R,I as S,G as a,q as b,L as f,N as u};
