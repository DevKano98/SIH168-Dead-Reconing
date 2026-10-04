import React, { useState, useMemo } from 'react';
import {
  Navigation,
  BookOpen,
  Search,
  Code2,
  Terminal,
  Cpu,
  Layers,
  ShieldAlert,
  ExternalLink,
  ChevronRight,
  Copy,
  Check,
  Smartphone,
  ArrowLeft,
} from 'lucide-react';

export function DocsApp() {
  const [searchQuery, setSearchQuery] = useState('');
  const [copiedSnippet, setCopiedSnippet] = useState(null);

  const copyCode = (code, id) => {
    navigator.clipboard.writeText(code);
    setCopiedSnippet(id);
    setTimeout(() => setCopiedSnippet(null), 2000);
  };

  const sections = [
    { id: 'overview', title: 'Overview & Boundaries', category: 'GET STARTED' },
    { id: 'quickstart', title: 'Quickstart & CLI', category: 'GET STARTED' },
    { id: 'runtime-api', title: 'Runtime HTTP API', category: 'INTERACTIVE RUNTIME' },
    { id: 'runtime-controls', title: 'Control Actions Contract', category: 'INTERACTIVE RUNTIME' },
    { id: 'python-sdk', title: 'Python Research SDK', category: 'CORE ENGINE' },
    { id: 'android-kotlin', title: 'Android Kotlin Engine', category: 'MOBILE EMBEDDED' },
    { id: 'portable-model', title: 'Portable Model Evaluation', category: 'MOBILE EMBEDDED' },
    { id: 'benchmark-limits', title: 'Evaluation & Known Limits', category: 'EVIDENCE' },
  ];

  const filteredSections = useMemo(() => {
    if (!searchQuery.trim()) return sections;
    const q = searchQuery.toLowerCase();
    return sections.filter((s) => s.title.toLowerCase().includes(q) || s.category.toLowerCase().includes(q));
  }, [searchQuery]);

  return (
    <div className="min-h-screen bg-canvas-base flex flex-col font-sans text-ink-primary">
      {/* Top Header */}
      <header className="bg-canvas-card border-b border-border-light sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-tech-blue flex items-center justify-center text-white">
                <Navigation className="w-4 h-4 transform -rotate-45" />
              </div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-base tracking-tight text-ink-primary">Continuum</span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-canvas-subtle border border-border-light text-ink-secondary">
                  Docs
                </span>
              </div>
            </div>
            <span className="hidden sm:inline text-xs text-ink-muted border-l border-border-light pl-4 font-mono">
              Continuum SDK Documentation
            </span>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <a
              href="/"
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-border-light bg-canvas-card hover:bg-canvas-subtle text-ink-secondary hover:text-ink-primary transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Studio</span>
            </a>
            <a
              href="/mobile"
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-border-light bg-canvas-card hover:bg-canvas-subtle text-ink-secondary hover:text-ink-primary transition-colors"
            >
              <span>Driver HUD</span>
              <ExternalLink className="w-3 h-3 opacity-60" />
            </a>
            <a
              href="https://github.com/DevKano98/SIH168-Dead-Reconing"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden md:flex items-center gap-1 px-3 py-1.5 rounded-lg bg-ink-primary text-white hover:bg-slate-800 transition-colors font-medium"
            >
              <span>GitHub</span>
              <ExternalLink className="w-3 h-3 opacity-80" />
            </a>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 flex-1 w-full grid grid-cols-1 md:grid-cols-12 gap-8">
        {/* Left Navigation Sidebar */}
        <aside className="md:col-span-3 space-y-6">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-3 text-ink-muted" />
            <input
              type="text"
              placeholder="Search documentation..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-canvas-card border border-border-light rounded-lg text-xs font-sans focus:outline-none focus:border-tech-blue shadow-sm"
            />
          </div>

          <nav className="space-y-4 text-xs">
            {['GET STARTED', 'INTERACTIVE RUNTIME', 'CORE ENGINE', 'MOBILE EMBEDDED', 'EVIDENCE'].map((cat) => {
              const catSections = filteredSections.filter((s) => s.category === cat);
              if (!catSections.length) return null;
              return (
                <div key={cat} className="space-y-1">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-ink-muted px-2 py-1">
                    {cat}
                  </div>
                  {catSections.map((sec) => (
                    <a
                      key={sec.id}
                      href={`#${sec.id}`}
                      className="block px-2.5 py-1.5 rounded-md text-ink-secondary hover:text-tech-blue hover:bg-canvas-subtle transition-colors font-medium"
                    >
                      {sec.title}
                    </a>
                  ))}
                </div>
              );
            })}
          </nav>

          <div className="p-3 bg-canvas-card border border-border-light rounded-xl text-xs space-y-1">
            <div className="text-[10px] text-ink-muted uppercase font-bold">SDK Version</div>
            <div className="font-mono font-semibold text-ink-primary">v0.3.0 (Interactive)</div>
            <div className="text-[11px] text-ink-faint">Smart India Hackathon SIH168</div>
          </div>
        </aside>

        {/* Right Content Area */}
        <main className="md:col-span-9 space-y-12 max-w-3xl">
          {/* Section: Overview */}
          <section id="overview" className="space-y-4 scroll-mt-20">
            <div className="text-xs font-bold text-tech-blue uppercase tracking-wider">
              CONTINUUM IDR RESEARCH SDK
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-ink-primary">
              Vehicle Dead Reckoning Navigation Fallback
            </h1>
            <p className="text-sm text-ink-secondary leading-relaxed">
              Continuum is an autonomous dead-reckoning engine designed for Smart India Hackathon SIH168.
              It fuses smartphone inertial sensors (accelerometers, gyroscopes) with learned longitudinal speed estimation,
              an Extended Kalman Filter (EKF), zero-velocity updates (ZUPT), and kinematic constraints to maintain position continuity when GNSS is lost.
            </p>

            {/* Research Boundary Warning Callout */}
            <div className="p-4 rounded-xl bg-tech-amber-subtle/50 border border-tech-amber-border space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-amber-900">
                <ShieldAlert className="w-4 h-4 text-tech-amber" />
                <span>Research Prototype & Evidence Boundary</span>
              </div>
              <p className="text-xs text-amber-950 leading-relaxed">
                This system runs real-time Python and Kotlin algorithmic pipelines on recorded vehicle trials (IO-VNBD dataset).
                It is <strong>NOT live smartphone sensing</strong> and <strong>NOT certified aviation/automotive navigation</strong>.
                Current held-out benchmark drift misses the &lt;10% target without external wheel odometry or road map-matching. We report all evaluation metrics transparently.
              </p>
            </div>
          </section>

          {/* Section: Quickstart & CLI */}
          <section id="quickstart" className="space-y-4 scroll-mt-20 border-t border-border-light pt-8">
            <h2 className="text-xl font-bold tracking-tight text-ink-primary">Quickstart & CLI Commands</h2>
            <p className="text-xs text-ink-secondary leading-relaxed">
              Continuum CLI provides dedicated commands for evaluation, simulation serving, and sensor calibration:
            </p>

            <div className="relative rounded-xl bg-slate-900 text-slate-100 p-4 font-mono text-xs overflow-x-auto shadow-card">
              <button
                onClick={() =>
                  copyCode(
                    '# 1. Run offline benchmark evaluation across all held-out runs\npython -m continuum_idr.cli evaluate\n\n# 2. Launch Continuum Studio interactive simulation server\npython -m continuum_idr.cli studio --port 8000',
                    'cli-code'
                  )
                }
                className="absolute top-3 right-3 p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                title="Copy code"
              >
                {copiedSnippet === 'cli-code' ? (
                  <Check className="w-3.5 h-3.5 text-tech-green" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
              </button>
              <pre className="text-slate-300">
                <span className="text-slate-500"># 1. Run offline benchmark evaluation across all held-out runs</span>{'\n'}
                <span className="text-tech-blue">python</span> -m continuum_idr.cli evaluate{'\n\n'}
                <span className="text-slate-500"># 2. Launch Continuum Studio interactive simulation server</span>{'\n'}
                <span className="text-tech-blue">python</span> -m continuum_idr.cli studio --port 8000
              </pre>
            </div>
          </section>

          {/* Section: Runtime HTTP Endpoints */}
          <section id="runtime-api" className="space-y-4 scroll-mt-20 border-t border-border-light pt-8">
            <h2 className="text-xl font-bold tracking-tight text-ink-primary">Runtime HTTP API</h2>
            <p className="text-xs text-ink-secondary leading-relaxed">
              The Studio backend provides deterministic, causal REST endpoints for telemetry streaming and interactive control:
            </p>

            <div className="border border-border-light rounded-xl overflow-hidden shadow-card">
              <table className="w-full text-xs text-left">
                <thead className="bg-canvas-subtle text-ink-muted uppercase text-[10px] font-semibold border-b border-border-light">
                  <tr>
                    <th className="px-4 py-2.5">Method</th>
                    <th className="px-4 py-2.5 font-mono">Endpoint</th>
                    <th className="px-4 py-2.5">Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-subtle font-mono text-xs">
                  <tr>
                    <td className="px-4 py-2.5 font-bold text-tech-blue">GET</td>
                    <td className="px-4 py-2.5 font-semibold text-ink-primary">/api/runtime</td>
                    <td className="px-4 py-2.5 font-sans text-ink-secondary">
                      Current session snapshot (tracking mode, speed, heading, error, samples).
                    </td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2.5 font-bold text-tech-green">POST</td>
                    <td className="px-4 py-2.5 font-semibold text-ink-primary">/api/runtime/control</td>
                    <td className="px-4 py-2.5 font-sans text-ink-secondary">
                      Executes interactive control actions (play, pause, step, gnss, rate, restart).
                    </td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2.5 font-bold text-tech-blue">GET</td>
                    <td className="px-4 py-2.5 font-semibold text-ink-primary">/api/summary</td>
                    <td className="px-4 py-2.5 font-sans text-ink-secondary">
                      Held-out benchmark summary (34 outages, baseline comparisons).
                    </td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2.5 font-bold text-tech-blue">GET</td>
                    <td className="px-4 py-2.5 font-semibold text-ink-primary">/api/health</td>
                    <td className="px-4 py-2.5 font-sans text-ink-secondary">
                      Server readiness and runtime initialization status.
                    </td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2.5 font-bold text-tech-blue">GET</td>
                    <td className="px-4 py-2.5 font-semibold text-ink-primary">/api/runtime/export</td>
                    <td className="px-4 py-2.5 font-sans text-ink-secondary">
                      Downloads full runtime session snapshot JSON.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          {/* Section: Control Actions Contract */}
          <section id="runtime-controls" className="space-y-4 scroll-mt-20 border-t border-border-light pt-8">
            <h2 className="text-xl font-bold tracking-tight text-ink-primary">Control Actions Contract</h2>
            <p className="text-xs text-ink-secondary leading-relaxed">
              POST requests to <code className="px-1.5 py-0.5 rounded bg-canvas-subtle font-mono text-tech-blue">/api/runtime/control</code> accept a JSON payload with an action and optional value:
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3.5 rounded-lg bg-canvas-card border border-border-light">
                <div className="font-mono font-bold text-ink-primary">action: "play" / "pause"</div>
                <p className="text-ink-secondary text-[11px] mt-1">
                  Starts or halts the real-time simulation clock.
                </p>
              </div>
              <div className="p-3.5 rounded-lg bg-canvas-card border border-border-light">
                <div className="font-mono font-bold text-ink-primary">action: "step", value: 25</div>
                <p className="text-ink-secondary text-[11px] mt-1">
                  Advances exactly N IMU samples forward (requires paused state).
                </p>
              </div>
              <div className="p-3.5 rounded-lg bg-canvas-card border border-border-light">
                <div className="font-mono font-bold text-ink-primary">action: "gnss", value: false</div>
                <p className="text-ink-secondary text-[11px] mt-1">
                  Withholds GNSS fixes to simulate tunnel or urban canyon blackout.
                </p>
              </div>
              <div className="p-3.5 rounded-lg bg-canvas-card border border-border-light">
                <div className="font-mono font-bold text-ink-primary">action: "restart"</div>
                <p className="text-ink-secondary text-[11px] mt-1">
                  Resets the session state, generating a fresh UUID and clean history.
                </p>
              </div>
            </div>
          </section>

          {/* Section: Python Research SDK */}
          <section id="python-sdk" className="space-y-4 scroll-mt-20 border-t border-border-light pt-8">
            <h2 className="text-xl font-bold tracking-tight text-ink-primary">Python Research SDK</h2>
            <p className="text-xs text-ink-secondary leading-relaxed">
              Integrate <code className="font-mono text-tech-blue">IDREngine</code> directly into your Python research pipelines:
            </p>

            <div className="relative rounded-xl bg-slate-900 text-slate-100 p-4 font-mono text-xs overflow-x-auto shadow-card">
              <button
                onClick={() =>
                  copyCode(
                    'from continuum_idr.engine import IDREngine\nfrom continuum_idr.model import MotionModelBundle\nfrom continuum_idr.types import EngineConfig, IMUSample, GNSSFix\n\n# Initialize model & engine\nmodel = MotionModelBundle.load("models/motion_p0")\nconfig = EngineConfig(imu_rate_hz=10.0, gnss_timeout_s=1.5)\nengine = IDREngine(model, config)\n\n# Feed IMU samples at 10 Hz\nstate = engine.on_imu(IMUSample(\n    timestamp_s=100.1,\n    accel_mps2=(0.1, 0.2, 9.8),\n    gyro_radps=(0.01, 0.02, -0.01)\n))\nprint(f"Tracking mode: {state.tracking_mode}, Speed: {state.speed_mps} m/s")',
                    'py-code'
                  )
                }
                className="absolute top-3 right-3 p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                title="Copy code"
              >
                {copiedSnippet === 'py-code' ? (
                  <Check className="w-3.5 h-3.5 text-tech-green" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
              </button>
              <pre className="text-slate-300">
                <span className="text-purple-400">from</span> continuum_idr.engine <span className="text-purple-400">import</span> IDREngine{'\n'}
                <span className="text-purple-400">from</span> continuum_idr.model <span className="text-purple-400">import</span> MotionModelBundle{'\n'}
                <span className="text-purple-400">from</span> continuum_idr.types <span className="text-purple-400">import</span> EngineConfig, IMUSample, GNSSFix{'\n\n'}
                <span className="text-slate-500"># Initialize model & engine</span>{'\n'}
                model = MotionModelBundle.load(<span className="text-green-400">"models/motion_p0"</span>){'\n'}
                config = EngineConfig(imu_rate_hz=<span className="text-amber-400">10.0</span>, gnss_timeout_s=<span className="text-amber-400">1.5</span>){'\n'}
                engine = IDREngine(model, config){'\n\n'}
                <span className="text-slate-500"># Feed IMU samples at 10 Hz</span>{'\n'}
                state = engine.on_imu(IMUSample({'\n'}
                {'    '}timestamp_s=<span className="text-amber-400">100.1</span>,{'\n'}
                {'    '}accel_mps2=(<span className="text-amber-400">0.1</span>, <span className="text-amber-400">0.2</span>, <span className="text-amber-400">9.8</span>),{'\n'}
                {'    '}gyro_radps=(<span className="text-amber-400">0.01</span>, <span className="text-amber-400">0.02</span>, -<span className="text-amber-400">0.01</span>){'\n'}
                )){'\n'}
                print(f<span className="text-green-400">"Tracking mode: {'{'}state.tracking_mode{'}'}, Speed: {'{'}state.speed_mps{'}'} m/s"</span>)
              </pre>
            </div>
          </section>

          {/* Section: Android Kotlin Engine */}
          <section id="android-kotlin" className="space-y-4 scroll-mt-20 border-t border-border-light pt-8">
            <h2 className="text-xl font-bold tracking-tight text-ink-primary">Android Kotlin Engine</h2>
            <p className="text-xs text-ink-secondary leading-relaxed">
              The Android app in <code className="font-mono text-tech-blue">android/app/src/main/java/ai/continuum/idr/</code> runs identical EKF and zero-dependency portable tree inference in pure Kotlin:
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3.5 rounded-lg bg-canvas-card border border-border-light">
                <div className="font-mono font-bold text-ink-primary">ContinuumLocationEngine.kt</div>
                <p className="text-ink-secondary text-[11px] mt-1">
                  Contains the Kotlin Extended Kalman Filter, sensor anomaly monitoring, and outage state machine.
                </p>
              </div>
              <div className="p-3.5 rounded-lg bg-canvas-card border border-border-light">
                <div className="font-mono font-bold text-ink-primary">PortableTreeRunner.kt</div>
                <p className="text-ink-secondary text-[11px] mt-1">
                  Evaluates 100 HistGradientBoosting decision trees in &lt;150 µs without Python or ONNX runtime.
                </p>
              </div>
            </div>
          </section>

          {/* Section: Known Limitations */}
          <section id="benchmark-limits" className="space-y-4 scroll-mt-20 border-t border-border-light pt-8">
            <h2 className="text-xl font-bold tracking-tight text-ink-primary">Evaluation & Known Limits</h2>
            <p className="text-xs text-ink-secondary leading-relaxed">
              Historical benchmark evaluation on the IO-VNBD dataset (Driver E) yields a median drift of <strong>80.32%</strong> across 34 blackout windows.
              The &lt;10% target is currently missed due to thermal bias accumulation in smartphone MEMS gyroscopes.
              Road-network map matching and cooperative vehicle-to-vehicle odometry are active development tracks to bridge this gap.
            </p>
          </section>
        </main>
      </div>
    </div>
  );
}
export default DocsApp;
