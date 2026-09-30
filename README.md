# Continuum IDR

Continuum IDR is a research SDK and demonstration application for vehicle navigation during temporary GNSS loss. It accepts ordered smartphone IMU samples and optional GNSS fixes, then produces position, speed, heading, uncertainty, tracking mode, and health information.

The repository includes:

- a Python navigation SDK and trained motion-model bundle;
- a quality-gated IO-VNBD outage evaluator with two comparison baselines;
- Continuum Studio, a synchronized desktop replay and driver-facing view;
- an integrated developer documentation portal;
- a portable JSON tree runner and Kotlin Android integration source;
- experimental road matching, vehicle profile, scheduling, calibration, and wheel-odometry modules.

## Current evidence

The checked-in evaluation artifact is `iovnbd-vtb-heldout-p0`. It evaluates 34 GNSS-outage windows from the held-out IO-VNBD `Vtb*` family.

| Metric | Current artifact |
| --- | ---: |
| Held-out runs | 11 |
| Evaluated outages | 34 |
| Median endpoint error | 354.3 m |
| Median drift | 80.3% |
| Under-10% target pass rate | 0.0% |
| Frozen-position median error | 496.9 m |
| Last-speed-plus-gyro median error | 334.4 m |

The engine reduces median error relative to the frozen-position baseline, but it is worse than the last-speed-plus-gyro baseline on the overall median and does not meet the supplied drift target. These results are preliminary evidence, not a production-accuracy claim.

## Run the prototype

Python 3.10 or later is required.

```powershell
python -m pip install -e .
python -m pytest tests/
python -m continuum_idr.cli studio --artifacts artifacts/evaluation --port 8000
```

Open:

- Studio replay: `http://127.0.0.1:8000/`
- SDK documentation: `http://127.0.0.1:8000/docs`
- synchronized driver view: `http://127.0.0.1:8000/mobile`

Studio and the driver view share one server-side replay clock. Play, pause, seek, replay speed, and restart controls operate on the same saved SDK trace. The interface clearly labels it as a recorded evaluation; it does not present browser playback as live phone inference.

The new **interactive backend** is available separately at `/api/runtime`. It
processes raw recorded sensor events through the running SDK, with actual GPS
withholding/restoration, pause/step/restart, and session export. The existing HTML
has not yet been connected to it. See [runtime API](docs/RUNTIME_API.md) and the
[Antigravity frontend handoff](ANTIGRAVITY_FRONTEND_PROMPT.md). Restart the server
after updating backend code. Neither mode uses live phone sensors.

## Python SDK quickstart

```python
from continuum_idr import (
    EngineConfig,
    GNSSFix,
    IDREngine,
    IMUSample,
    MotionModelBundle,
)

model = MotionModelBundle.load("models/motion_p0")
engine = IDREngine(EngineConfig(imu_rate_hz=10.0), model)

engine.on_gnss(
    GNSSFix(
        timestamp_s=100.0,
        latitude_deg=52.4001,
        longitude_deg=-1.5002,
        speed_mps=12.5,
        course_deg=92.0,
        horizontal_accuracy_m=3.5,
    )
)

state = engine.on_imu(
    IMUSample(
        timestamp_s=100.1,
        accel_mps2=(0.12, 0.05, 9.81),
        gyro_radps=(0.001, -0.015, 0.002),
        gravity_mps2=(0.0, 0.0, 9.81),
    )
)

print(state.tracking_mode, state.latitude_deg, state.longitude_deg)
```

The runtime API has no reference trajectory or true-speed argument. Evaluation reference data remains outside the SDK.

## Reproduce the evidence

```powershell
python -m continuum_idr.cli audit --dataset . --output artifacts/audit/pairs.json
python -m continuum_idr.cli train --dataset . --output models/motion_p0
python -m continuum_idr.cli evaluate --dataset . --model models/motion_p0 --output artifacts/evaluation
python -m continuum_idr.cli replay --dataset . --model models/motion_p0
```

Evaluation output includes `summary.json`, per-outage CSV metrics, a selected replay JSON, trajectory and error plots, and a generated results report.

## Additional tools

```powershell
# Export the zero-dependency portable tree bundle
python -m continuum_idr.cli export --model models/motion_p0 --output models/portable/motion_portable.json

# Generate regional road map pack from GeoJSON or preset Indian corridor
python -m continuum_idr.cli convert-map-pack --input indian_corridor --output android/app/src/main/assets/sample_road_pack.json

# Generate deterministic multi-stage parity fixture
python -m continuum_idr.parity

# Generate any of 20 deterministic synthetic evaluation scenarios
python -m continuum_idr.cli synthetic --scenario list
python -m continuum_idr.cli synthetic --scenario tunnel_total_gnss_blackout_60s --duration 60 --output artifacts/synthetic/tunnel.jsonl

# Ingest, audit, and validate phone-recorded trip logs (Schema 1.0.0)
python -m continuum_idr.cli validate-phone-log artifacts/synthetic/tunnel.jsonl
python -m continuum_idr.cli phone-report artifacts/synthetic/tunnel.jsonl --output artifacts/reports/tunnel_report.md

# Run localized cooperative V2X traffic gateway
python -m continuum_idr.cli traffic-gateway --host 127.0.0.1 --port 8080

# Run defined GNSS corruption scenarios
python -m continuum_idr.cli stress --model models/motion_p0 --duration 15.0

# Measure the high-rate scheduler path on this computer
python -m continuum_idr.cli benchmark-scheduler --samples 500

# Inspect a vehicle profile
python -m continuum_idr.cli profile --profile motorcycle
```

Throughput checks demonstrate software timing on the measured computer. They do not establish external-IMU navigation accuracy.

## Android Application & Build Artifacts

The [`android/`](android/) directory is a verified, standalone Gradle Android application project:
- **Build output:** `android/app/build/outputs/apk/debug/app-debug.apk` (1,102,666 bytes, SHA-256: `6d894a740ffb5c35a82e8d9b764cb4282ceb5d8b0535003e985361f16aa7ffaa`)
- **Model verification:** Packages trained `motion_portable.json` (SHA-256: `c98f71fd9b20af88f3079a00bf66377d5c055262a6367e4dd1cd009152a96072`, verified byte-exact parity with Python bundle).
- **Offline road maps:** Vector `MapView` renders topological road segments, vehicle heading, breadcrumb trail, uncertainty ellipse, and scale bar completely offline.
- **On-device dead reckoning:** `ContinuumLocationEngine` handles causal 2-second IMU windowing, tree inference, alignment estimation, tilt shift detection ($>15^\circ$), gradual GNSS recovery blending, motorcycle lean angle compensation, parking crawl/reverse heuristics, and road snapping.
- **Performance instrumentation:** Microsecond latency timers (`lastInferenceLatencyUs`, `avgInferenceLatencyUs`), map-match latency, and heap memory tracking (`EngineDiagnostics`).
- **Cooperative traffic sharing:** `TrafficBleManager` provides Bluetooth Low Energy (BLE) peer-to-peer hazard beaconing (`GNSS_OUTAGE`, `SPEED_BREAKER`, `POTHOLE`, `TRAFFIC_JAM`), controlled test generators, and relay statistics HUD (Notice: direct ~10–30m local line-of-sight only, not cellular range).
- **Foreground trip recorder:** `TrackingService` logs Schema 1.0.0 JSONL trip files with Line 1 metadata, vehicle profile, route category, model SHA-256 hash, raw IMU/GNSS, and closing diagnostics.
- **Unit test suite:** `android/app/src/test/java/ai/continuum/idr/` executes `ParityTest`, `RoadGraphPackTest`, and `InstrumentationTest` with 100% pass rate.

Build, test, and validation commands:
```powershell
cd android
.\gradlew.bat testDebugUnitTest    # Runs Kotlin unit tests
.\gradlew.bat assembleDebug         # Produces debug APK
cd ..

# Automate device checks, installation, profiling, and log extraction:
.\tools\adb\device_validate.ps1 -Action all
```

## Repository guide

| Path | Purpose |
| --- | --- |
| `continuum_idr/` | Python SDK, evaluation, CLI, synthetic generator, traffic gateway, Studio |
| `continuum_idr/synthetic_dataset.py` | 17-category synthetic Indian-road expansion generator |
| `continuum_idr/reference_eval.py` | Ground-truth reference trajectory evaluation engine (RTK GNSS / CSV) |
| `continuum_idr/experiments.py` | Comparative estimator candidate architecture benchmarking suite |
| `continuum_idr/studio_static/` | Studio, driver view, and developer portal |
| `models/motion_p0/` | Trained research model and manifest |
| `models/portable/` | Portable JSON model representation (`motion_portable.json`) |
| `artifacts/evaluation/` | Checked-in IO-VNBD metrics, replay, and figures |
| `android/` | Complete Android Gradle project and Kotlin application source |
| `tools/adb/` | Windows ADB automation tools (`device_validate.ps1`, `device_validate.bat`) |
| `docs/FIELD_TEST_PLANS.md` | Repeatable protocols for highway, urban, potholes, tunnels, parking, bikes, external IMUs |
| `docs/DEVICE_VALIDATION_CHECKLIST.md` | Pre-flight and post-flight operational verification gates |
| `docs/INDIAN_ROAD_COLLECTION_PROTOCOL.md` | Field data collection & testing protocol for Indian road conditions |
| `docs/idr/` | Product, architecture, evaluation, and roadmap documents |
| `tests/` | Python unit and integration test suite (122 passing tests) |

## Supported scope and limitations

- The primary evidence uses approximately 10 Hz smartphone data from IO-VNBD.
- The evaluated profile assumes a mounted phone in a passenger vehicle.
- Handheld phones, pockets, motorcycles, Indian roads, external IMUs, and lane-level accuracy require separate reference-based validation.
- GNSS consistency checks are not a universal jamming or spoofing detector.
- Road matching and auxiliary modules require their own end-to-end accuracy evidence.
- A known initial absolute state is required for trustworthy latitude and longitude through an outage.

See [CURRENT_STATUS.md](CURRENT_STATUS.md) for the canonical project status and [artifacts/evaluation/RESULTS.md](artifacts/evaluation/RESULTS.md) for the generated evaluation report.
