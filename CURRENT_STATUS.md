# Continuum IDR — Current Status

**Updated:** 2026-09-30

**Canonical experiment:** `iovnbd-vtb-heldout-p0`

**Prototype status:** Working research SDK, evaluator, synchronized replay application, developer portal, and Android source integration

**Accuracy status:** The current held-out artifact does not meet the supplied under-10% drift target

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
