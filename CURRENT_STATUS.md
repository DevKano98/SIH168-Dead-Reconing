# Continuum IDR — Current Status

**Updated:** 2026-09-30

**Canonical experiment:** `iovnbd-vtb-heldout-p0`

## Physical Validation Readiness & Measured Performance Analysis Update — 2026-09-30

The physical validation, field ingestion, reference evaluation, candidate comparison architectures, and Android instrumentation have been implemented:

1. **17-Category Synthetic Indian-Road Benchmark Pack (`idr generate-synthetic-dataset`)**:
   - Generates deterministic, randomized scenarios across 17 distinct operational conditions (smooth highway, city roads, stop-go, intersections, rough/patched roads, potholes, speed breakers, engine idle, sudden braking, tunnels, multipath, parking ramps, reverse crawl, motorcycle lean/vibration, mount shifts, 100/200 Hz IMU).
   - Generates JSONL trip logs and standardized `dataset_manifest.json` with mandatory simulator notice: *"Synthetic results demonstrate simulator behavior only. They do not demonstrate real-road accuracy."*

2. **Folder-Level Field Ingestion & Split Tooling (`idr validate-field-folder`)**:
   - Audits entire directories of on-device recorded JSONL trips.
   - Computes data quality audits, sensor rate distributions (mean/median/p10/p90 Hz), route/surface event coverage, and source domain breakdowns.
   - Generates grouped train/val/test splits grouped strictly by vehicle/device to prevent data leakage.

3. **Ground-Truth Reference Trajectory Evaluation Engine (`idr evaluate-reference`)**:
   - Evaluates estimated trips against external CSV/JSONL reference tracks (e.g. RTK GNSS).
   - Computes endpoint error, drift % of distance traveled, max/RMSE horizontal error, speed/heading RMSE, along-track and cross-track errors, and outage recovery settling time.
   - Exports point-by-point error CSVs and Markdown evaluation reports with strict provenance labeling (*telemetry only*, *external_reference*, or *synthetic_ground_truth*).

4. **Candidate Architecture Comparison Framework (`idr run-experiments`)**:
   - Systematically benchmarks 5 candidate architectures (`direct_speed_model`, `last_speed_gyro`, `map_matched`, `calibrated_alignment`, `disturbance_filter`).
   - Generates publication-grade Markdown tables and JSON summaries.
   - Strictly preserves historical IO-VNBD benchmark figures (80.32% median drift, 0% <10% pass rate, 354.25m error) and highlights the physical validation boundary.

5. **Android App Performance Instrumentation & BLE Test Mode**:
   - Microsecond inference latency (`lastInferenceLatencyUs`, `avgInferenceLatencyUs`), map-match latency, and heap memory tracking (`EngineDiagnostics`).
   - In-app route category selector dropdown before recording.
   - Live telemetry and performance HUD in `MainActivity`.
   - BLE test hazard generators (`generateTestHazard`), relay statistics counters (sent, received, relayed, duplicates, expired) and HUD with mandatory local range disclaimer notice: *"BLE operates within direct ~10-30m local line-of-sight only, not long-range cellular."*
   - Closing diagnostics record logged to JSONL upon trip completion.

6. **Windows ADB Automation Tooling**:
   - `tools/adb/device_validate.ps1` and `tools/adb/device_validate.bat` for connection testing, APK installation, hardware/sensor profiling, trip log pulling, and logcat diagnostics capture.
   - Comprehensive test protocols in `docs/FIELD_TEST_PLANS.md` and verification gates in `docs/DEVICE_VALIDATION_CHECKLIST.md`.

7. **Verification & Baseline Invariants**:
   - Python test suite: 122/122 tests passing.
   - Kotlin unit tests: `ParityTest`, `RoadGraphPackTest`, `InstrumentationTest` passing 100% via `./gradlew.bat testDebugUnitTest`.
   - Android debug APK built cleanly (`1,102,666 bytes`, SHA-256: `6d894a740ffb5c35a82e8d9b764cb4282ceb5d8b0535003e985361f16aa7ffaa`).
   - Model weights hash `c98f71fd9b20af88f3079a00bf66377d5c055262a6367e4dd1cd009152a96072` verified in APK assets.
   - Historical IO-VNBD benchmark figures (80.32% median drift, 0% <10% pass rate) strictly preserved.

## Interactive backend & frontend update — 2026-09-30

The new `/api/runtime` API processes raw recorded IMU/GNSS through a running SDK.
Manual GPS disable/restore gates actual estimator input; pause, step, speed,
restart, shared session telemetry, and JSON export are implemented. Reference
data is used only for scoring. This is recorded sensor input, not live phone sensing.

**Frontend implementation:** The frontend in `continuum_idr/studio_static/`
(`index.html`, `app.js`, `mobile.html`, `mobile.js`, `docs.html`, `style.css`)
has been completely rebuilt and connected to `/api/runtime` and `/api/runtime/control`.
Legacy `/api/session` and `/api/demo` have been eliminated from the interactive workspace.
Serial polling at 250ms, manual GPS withholding, live metric canvas rendering with scale bar,
mobile driver view synchronization, and developer portal documentation are verified.

Verification: 110 Python unit and integration tests passed (including runtime, parity, 20 synthetic scenarios, phone ingestion, and traffic gateway). Android Gradle unit tests (ParityTest, RoadGraphPackTest) passed with 100% success rate. The debug APK builds cleanly with embedded trained model weights and offline regional road pack.

**Prototype status:** Complete, buildable Android app (`app-debug.apk`), verified Python research SDK, faithful portable-model execution, offline vector road map rendering, deterministic 20-scenario synthetic generator, cooperative V2X traffic gateway, and Indian-road field collection pipeline.

**Accuracy status:** The raw IO-VNBD benchmark achieves 80.32% median drift (0.0% under-10% pass rate). This is documented honestly without inflated claims. Physical phone deployment requires on-road empirical validation per `docs/INDIAN_ROAD_COLLECTION_PROTOCOL.md`.

## What can be demonstrated now

Continuum Studio provides one coherent prototype experience:

- `/` is the evaluation workspace. It replays real saved states from the Python SDK, shows the trajectory, modes, uncertainty, measured error, baselines, and complete held-out benchmark.
- `/mobile` is a driver-facing client synchronized to the same server-side replay clock.
- `/docs` is the SDK developer portal with a quickstart, contracts, guides, API reference, architecture, evaluation, and limitations.

Launch all three with:

```powershell
python -m continuum_idr.cli studio --artifacts artifacts/evaluation --port 8000
```

The replay is explicitly identified as recorded IO-VNBD evaluation evidence. It is not represented as live phone inference. The driver view contains no scripted pothole, lane, or mounting claims.

## Implemented components

### Core Python SDK

- Typed IMU, GNSS, configuration, and navigation-state contracts.
- Causal rolling IMU feature extraction and trained speed/stop model bundle.
- Planar position, speed, and heading estimator with GNSS gating.
- Dead-reckoning and recovery modes with uncertainty output.
- Out-of-order and gap handling, guarded zero-velocity updates, mount-change flagging, and optional gyro-bias adaptation.
- Optional interfaces for road graphs and wheel-speed measurements.

### Evaluation and evidence

- Dataset pair audit and model training commands.
- Deterministic GNSS outage construction with quality gates.
- Frozen-position and last-speed-plus-gyro baselines.
- Per-outage metrics, aggregate summary, selected replay, plots, and generated results report.
- Held-out `Vtb*` family separation recorded by the current model and evaluation artifacts.

### Portable and Android paths

- Portable JSON tree representation and dependency-free runner.
- Kotlin portable-tree runner and Android sensor/location integration source.
- Android source integration guide.

These files establish an integration path. They are not evidence of a published, device-certified Android SDK or measured battery performance.

### Experimental modules

- Road-graph candidate matching.
- Passenger-car, truck, and motorcycle profiles.
- Road-surface event classifier.
- High-rate propagation scheduler.
- Wheel-speed odometry and slip handling.
- Sensor noise profiles and calibration utilities.

Their unit tests establish component behaviour. Deployment and navigation accuracy still require end-to-end tests on representative hardware and reference data.

## Current measured results

The authoritative values below come from `artifacts/evaluation/summary.json`.

| Scope | Value |
| --- | ---: |
| Held-out runs declared by the artifact | 11 |
| Evaluated outage windows | 34 |
| Median endpoint error | 354.3 m |
| 95th-percentile endpoint error | 1072.3 m |
| Median drift | 80.3% |
| 95th-percentile drift | 271.4% |
| Under-10% pass rate | 0.0% |
| Last-speed-plus-gyro median endpoint error | 334.4 m |
| Frozen-position median endpoint error | 496.9 m |

### By outage distance

| Distance | Outages | Continuum median error | Last-speed median | Frozen median | Median drift | Under-10% pass rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 50 m | 11 | 73.6 m | 59.8 m | 72.2 m | 148.6% | 0.0% |
| 500 m | 12 | 431.9 m | 414.9 m | 496.9 m | 86.4% | 0.0% |
| 1000 m | 11 | 799.0 m | 800.7 m | 948.7 m | 80.0% | 0.0% |

The system improves the overall median relative to holding the last GNSS position, but it does not improve on the last-speed-plus-gyro baseline overall. The selected demonstration outage also performs worse than both baselines. This is visible in Studio.

## Verification commands

The project should be checked with:

```powershell
python -m compileall continuum_idr tests
python -m pytest tests/
node --check continuum_idr/studio_static/app.js
node --check continuum_idr/studio_static/mobile.js
node --check continuum_idr/studio_static/docs.js
```

The server exposes `/api/health`, `/api/demo`, `/api/summary`, and the synchronized `/api/session` control endpoints. Studio endpoint tests cover artifact loading, documentation and driver routes, replay synchronization, health output, and invalid control rejection.

## Known limitations

1. Smartphone IMU alone cannot uniquely determine arbitrary straight constant speed. Long outages retain substantial speed and heading ambiguity.
2. The phone reference used by P0 has finite accuracy and sparse updates. It is practical screening evidence rather than survey-grade truth.
3. The current estimator is planar and assumes a mounted passenger-car profile.
4. No current artifact proves lane-level accuracy, Indian-road transfer, motorcycle accuracy, handheld-phone operation, real external-IMU accuracy, or production Android performance.
5. The browser views replay saved desktop results. Live on-device inference remains a separate milestone.
6. Several older design documents describe planned contracts and may retain historical wording. This file, `README.md`, `summary.json`, and the generated results report are the current status sources.

## Highest-value next engineering milestone

Improve the estimator using the existing validation discipline before adding more presentation claims. Diagnose entry alignment, heading integration, sparse GNSS timing, and learned-speed bias on validation data; freeze the configuration; regenerate the held-out artifact once; then embed the verified runtime in a real Android application and measure it on a named device.
