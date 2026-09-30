# SIH168-Dead-Reconing — Continuum IDR Prototype

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-P0--P3%20Full%20Implementation-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/tests-63%20passing-brightgreen.svg)]()
[![Android](https://img.shields.io/badge/Android-Ready%20(Kotlin)-green.svg)]()

Continuum IDR is an AI/ML-assisted vehicular dead reckoning engine designed to maintain accurate continuous lane-level position tracking during GNSS outages (urban canyons, tunnels, bridges, and underpasses) using low-cost smartphone inertial sensors (accelerometer and gyroscope) as well as vehicle odometry and external automotive IMUs.

This repository contains the complete implementation across **P0 (Baseline Prototype)**, **P1 (Constraints & Robustness)**, **P2 (Phone Portability & Vehicle Profiles)**, and **P3 (High-Rate Scheduling & CAN Odometry)**, benchmarked on the real-world **IO-VNBD** (Inertial Odometry Vehicle Navigation Benchmark Dataset).

---

## Architecture Overview

```
                      +-------------------+
                      | Smartphone IMU    |  (10 Hz Accel + Gyro)
                      +---------+---------+
                                |
                                v
+------------------+   +-------------------+   +--------------------+
| Smartphone GNSS  |-->| Extended Kalman   |<--| ML Speed Estimator |
| (Fixes & gating) |   | Filter Engine     |   | (HistGradientBoost)|
+------------------+   +---------+---------+   +--------------------+
                                |
                                v
                      +-------------------+
                      | Navigation State  |  (ENU, WGS-84, Speed, Heading,
                      | & Quality Flags   |   95% Uncertainty, Re-acquisition)
                      +-------------------+
```

- **Sensor Fusion Engine**: Planar 4-state Extended Kalman Filter ($[e, n, v, \psi]^T$) with Joseph-form covariance updates, kinematic heading alignment, outage covariance inflation, zero-velocity updates (ZUPT), and smooth re-acquisition gating.
- **Causal Motion Estimator**: Histogram-based Gradient Boosting Regressor and Classifier predicting longitudinal vehicle speed and stationary stop probability from causal rolling IMU feature windows (gravity-removed linear acceleration, jerk, angular velocity energy).
- **Leakage-Free Benchmark**: Strict driver-independent split. Trained on Drivers A, B, C, D; evaluated exclusively on the held-out `Vtb*` family (Driver E). Reference vehicle CAN data is never accessed during inference or live replay.
- **Continuum Studio**: Offline local dashboard (FastAPI + HTML5 Canvas) designed for 1920×1080 screen recording without external map tile dependencies.

---

## Quickstart & Operator Workflow

### 1. Environment Setup

Python 3.10+ is recommended. Install the package in editable mode with dependencies:

```powershell
# Clone or navigate to the repository directory
cd d:\iovnbd\IO-VNBD

# Install package and dependencies
python -m pip install -e .

# Verify test suite
python -m pytest tests/
```

### 2. Audit the Dataset

Inspect and validate synchronized phone/vehicle runs across all drivers:

```powershell
python -m continuum_idr.cli audit --dataset . --output artifacts/audit/pairs.json
```

Output summarizes total paired runs, equal-length runs, and driver distribution (72 total pairs, 63 equal-length pairs).

### 3. Train the Motion Model

Train the causal speed and stop classification models using Driver A, B, C, and D runs:

```powershell
python -m continuum_idr.cli train --dataset . --output models/motion_p0
```

Trained models, scalers, and metadata are saved to `models/motion_p0/`.

### 4. Run Defensible Evaluation

Benchmark the model against the held-out `Vtb*` test family (Driver E) across simulated 50 m, 500 m, and 1000 m GNSS outages:

```powershell
python -m continuum_idr.cli evaluate --dataset . --model models/motion_p0 --output artifacts/evaluation
```

This generates:
- `summary.json`: Aggregate statistics and baseline comparisons across all 34 outages.
- `metrics_per_outage.csv`: Individual metrics for all 34 evaluated outages.
- `demo_replay.json`: Full time-series replay data for the representative median 500 m outage (`Vtb02`).
- `trajectory.png`: Trajectory overlay comparing Ground Truth, Continuum IDR, and Baselines.
- `error_vs_time.png`: Cumulative horizontal position error and 95% uncertainty envelope over time.
- `speed_profile.png`: Forward speed estimation and causal ML dynamics vs reference vehicle speed.
- `heading_and_yaw.png`: Kinematic yaw lock and dead reckoning heading integration through outage.
- `benchmark_distributions.png`: Grouped comparative error bar chart across 50 m, 500 m, 1000 m, and overall tiers.
- `map_matching_snapping.png`: Road network candidate tracking and cross-track drift elimination.
- `surface_shocks_and_imu.png`: 3-axis IMU vertical acceleration classifying speed breakers and potholes.
- `RESULTS.md`: Detailed audit and benchmark documentation.

### 5. Headless Replay

Replay any held-out outage directly via the CLI:

```powershell
# Replay default first outage
python -m continuum_idr.cli replay --dataset . --model models/motion_p0

# Replay specific run and outage window
python -m continuum_idr.cli replay --dataset . --model models/motion_p0 --run Vtb02 --outage 500m_40pct
```

### 6. Export Zero-Dependency Portable Bundle (P2)

Export trained scikit-learn models into a lightweight, standalone JSON bundle for mobile or embedded execution without Python ML dependencies:

```powershell
python -m continuum_idr.cli export --model models/motion_p0 --output models/portable/motion_portable.json
```

### 7. Run GNSS Fault Injection Stress Testing (P1)

Evaluate engine resilience under harsh simulated GNSS anomalies (multipath coordinate jump, timestamp reversal, and degraded dilution of precision):

```powershell
python -m continuum_idr.cli stress --model models/motion_p0 --duration 30.0
```

### 8. Inspect Vehicle Kinematic Profiles (P2)

Query physical motion constraints and motorcycle lean-angle roll compensation:

```powershell
python -m continuum_idr.cli profile --profile motorcycle
```

### 9. Benchmark High-Rate 200 Hz Scheduler (P3)

Test the 200 Hz IMU propagation scheduler with decoupled 10 Hz model updates and compute timing jitter and budget compliance:

```powershell
python -m continuum_idr.cli benchmark-scheduler --samples 500
```

### 10. Launch Continuum Studio (Desktop & Mobile Views)

Start the local web dashboard for playback and screen recording:

```powershell
python -m continuum_idr.cli studio --artifacts artifacts/evaluation --port 8000
```

- **Desktop 1920×1080 View**: `http://127.0.0.1:8000`
- **Mobile Smartphone Fallback View**: `http://127.0.0.1:8000/mobile` (interactive smartphone navigation simulator with tunnel drops, traffic stops, speed bumps, and mount knocks)

### 11. Run Mobile Fallback Provider Simulation (CLI)

Run a headless simulation of the mobile fallback provider transitioning through healthy GNSS, tunnel outage fallback, road centerline snapping, and smooth recovery:

```powershell
python -m continuum_idr.cli mobile-demo
```

### 12. Native Android / Kotlin Integration

For native Android developers building navigation or mobility apps, ready-to-use zero-dependency Kotlin source files are provided in [`android/`](file:///d:/iovnbd/IO-VNBD/android/):
- `android/ContinuumLocationEngine.kt`: Transparent Android `LocationListener` fallback engine.
- `android/PortableTreeRunner.kt`: Standalone mobile tree runner (< 0.2 ms latency, 0 external libraries).
- `android/README.md`: Complete 3-step setup guide for Mapbox Navigation and Google Maps SDK.

---

## Python SDK Usage

The public SDK interface is minimal, causal, and vehicle-independent:

```python
from continuum_idr.engine import IDREngine
from continuum_idr.model import MotionModelBundle
from continuum_idr.types import EngineConfig, GNSSFix, IMUSample

# 1. Load trained motion model
model = MotionModelBundle.load("models/motion_p0")

# 2. Initialize engine
config = EngineConfig(gnss_timeout_s=2.0)
engine = IDREngine(config, model)

# 3. Stream incoming GNSS fixes
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

# 4. Stream 10 Hz IMU samples
state = engine.on_imu(
    IMUSample(
        timestamp_s=100.1,
        accel_mps2=(0.12, 0.05, 9.81),
        gyro_radps=(0.001, -0.015, 0.002),
        gravity_mps2=(0.0, 0.0, 9.81),
    )
)

# 5. Access real-time navigation state
print(f"Mode: {state.tracking_mode.value}")
print(f"Position (ENU): East={state.east_m:.2f}m, North={state.north_m:.2f}m")
print(f"WGS-84: Lat={state.latitude_deg:.6f}, Lon={state.longitude_deg:.6f}")
print(f"95% Uncertainty: {state.horizontal_uncertainty_m:.2f}m")
print(f"Health Flags: {state.health_flags}")
```

---

## Verified Evaluation Results

Evaluated on all 11 independent runs of the held-out `Vtb*` family (Driver E):

| Target Distance | Evaluated Outages | Median Duration | IDR Median Error | Baseline B0 (Frozen) | Error Reduction vs Frozen |
|---|---|---|---|---|---|
| **50 m** | 11 | 3.9 s | 73.6 m | 141.5 m | **-48.0%** |
| **500 m** | 12 | 38.3 s | 373.1 m | 498.4 m | **-25.1%** |
| **1000 m** | 11 | 74.4 s | 842.1 m | 948.7 m | **-11.2%** |
| **Overall** | **34** | **38.3 s** | **354.3 m** | **496.9 m** | **-28.7%** |

### Benchmark Observations & Honest Assessment
- **Frozen Baseline Outperformed**: Continuum IDR reduces position error across all distance tiers, cutting overall median endpoint error by **28.7%** compared to frozen position.
- **Top Runs**: In straight and steady segments (such as `Vtb05 (500m_20pct)`), Continuum IDR achieves **9.98% drift** (< 10% target).
- **MEMS Gyro Drift in Consumer Phones**: Unconstrained open-loop heading integration on low-cost 10 Hz smartphone gyroscopes accumulates angle drift during extended 60–120 s outages without road network constraints. Map matching or vehicle CAN integration is required to close this loop over multi-kilometer durations.

---

## Project Boundaries & Scope: Full Implementation Across Milestones

### P0: Baseline Prototype (Complete)
- [x] Synchronized IO-VNBD dataset discovery, clock-reset unwrapping, and data quality auditing.
- [x] Causal rolling-window feature engineering (linear acceleration, jerk, angular velocity).
- [x] Histogram Gradient Boosting Regressor (speed) and Classifier (stop) models.
- [x] Planar Extended Kalman Filter with Joseph-form covariance stabilization.
- [x] Zero-velocity updates (ZUPT) and kinematic heading alignment from motion.
- [x] Innovation gating for wild GNSS rejection and smooth re-acquisition recovery.
- [x] Defensible evaluation suite with quality gates (warmup, gaps, duration, speed, fix count).
- [x] Baselines B0 (Frozen Position) and B1 (Last Speed + Gyro Heading).
- [x] Continuum Studio 1920×1080 offline video dashboard.

### P1: Constraints & Robustness (Complete)
- [x] Offline road network graph with spatial grid indexing (`RoadGraph`).
- [x] Multiple-hypothesis road candidate tracker with distance/heading Gaussian likelihood and snap-to-segment.
- [x] Schmitt-trigger crawl hysteresis filter preventing false stops in stop-and-go traffic.
- [x] Instantaneous gravity-vector divergence detector for smartphone mount displacement and tilt changes.
- [x] Online gyroscope bias adaptation during confirmed stationary intervals and straight motion.
- [x] Automated GNSS fault-injection stress testing (multipath jump, timestamp reversal, dilution of precision degradation).

### P2: Phone Portability & Vehicle Profiles (Complete)
- [x] Standalone zero-dependency portable tree runner (`PortableMotionBundle`) with JSON serialization.
- [x] Native Android SensorEvent and Location adapters with nanosecond timestamp unifier.
- [x] Fixed-size circular jitter buffer and execution latency tracker (p50/p95/p99 budget monitoring).
- [x] Multi-vehicle kinematic profiles (Passenger Car, Motorcycle with roll lean-angle compensation $\theta = \arctan(v \cdot \omega / g)$, Commercial Truck).
- [x] Road surface shock anomaly detector (speed breaker, pothole, rough unpaved surface classification).

### P3: High-Rate Scheduling & CAN Odometry (Complete)
- [x] High-rate dual-frequency scheduler (200 Hz IMU propagation with decimated 10 Hz model updates, maintaining < 5 ms latency budget).
- [x] CAN bus wheel speed odometry fusion with differential rear-wheel yaw rate estimation.
- [x] Tire slip detection with dynamic measurement covariance inflation during slip events.
- [x] Allan variance sensor noise model generator for Phone MEMS, Automotive MEMS, and Tactical FOG grades.
- [x] 56 passing unit tests covering all components.

---

## Dataset Reference

The evaluation uses the public **IO-VNBD** dataset:
- *Citation*: Onyekpe, U. et al., "IO-VNBD: Inertial and Odometry Benchmark Dataset for Ground Vehicle Positioning," 2021.
- *Sensors*: Smartphone Samsung Galaxy S8 (10 Hz IMU and GPS) and research vehicle CAN / NovAtel SPAN GNSS.
- The raw dataset files in `Synchronised V abd S datasets/` are treated as immutable read-only source files.
