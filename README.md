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

# Run defined GNSS corruption scenarios
python -m continuum_idr.cli stress --model models/motion_p0 --duration 15.0

# Measure the high-rate scheduler path on this computer
python -m continuum_idr.cli benchmark-scheduler --samples 500

# Inspect a vehicle profile
python -m continuum_idr.cli profile --profile motorcycle
```

Throughput checks demonstrate software timing on the measured computer. They do not establish external-IMU navigation accuracy.

## Android source integration

The [`android/`](android/) directory contains Kotlin source and an integration guide. It is a source package, not a published or device-certified Android SDK. Validate accuracy, latency, memory, thermal behaviour, and battery use on the target phone before deployment claims.

## Repository guide

| Path | Purpose |
| --- | --- |
| `continuum_idr/` | Python SDK, evaluation, CLI, and Studio server |
| `continuum_idr/studio_static/` | Studio, driver view, and developer portal |
| `models/motion_p0/` | Trained research model and manifest |
| `models/portable/` | Portable JSON model representation |
| `artifacts/evaluation/` | Current checked-in metrics, replay, and figures |
| `android/` | Kotlin integration source |
| `docs/idr/` | Product, architecture, evaluation, and roadmap documents |
| `tests/` | Unit and integration tests |

## Supported scope and limitations

- The primary evidence uses approximately 10 Hz smartphone data from IO-VNBD.
- The evaluated profile assumes a mounted phone in a passenger vehicle.
- Handheld phones, pockets, motorcycles, Indian roads, external IMUs, and lane-level accuracy require separate reference-based validation.
- GNSS consistency checks are not a universal jamming or spoofing detector.
- Road matching and auxiliary modules require their own end-to-end accuracy evidence.
- A known initial absolute state is required for trustworthy latitude and longitude through an outage.

See [CURRENT_STATUS.md](CURRENT_STATUS.md) for the canonical project status and [artifacts/evaluation/RESULTS.md](artifacts/evaluation/RESULTS.md) for the generated evaluation report.
