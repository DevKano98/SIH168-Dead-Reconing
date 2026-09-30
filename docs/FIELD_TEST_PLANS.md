# Continuum IDR — Field Test Plans & Operational Protocols

This document defines standardized, repeatable physical road-testing protocols for validating the Continuum IDR dead-reckoning engine across demanding Indian road and operational conditions.

---

## 1. Safety, Legal, and Scientific Integrity Rules

> [!CAUTION]
> **Safety First**: Test operators must NEVER interact with mobile devices or test ruts while driving. All operations must be controlled by a passenger or configured beforehand. Comply strictly with all local traffic laws and speed regulations.

> [!IMPORTANT]
> **Evidence Boundary & Provenance Declaration**:
> 1. Unreferenced phone recordings are classified as **`telemetry only, not accuracy validated`**.
> 2. Tests evaluated against an independent dual-frequency RTK GNSS receiver (e.g. u-blox F9P, Oxford OxTS) are labeled **`external_reference`**.
> 3. Synthetic simulator replays are labeled **`synthetic_ground_truth`** with the mandatory disclaimer: *"Demonstrates simulator behavior only. Does not demonstrate real-road accuracy."*
> 4. BLE operates exclusively as a **short-range ad-hoc beacon (~10–30 meters line-of-sight)**. Never claim cellular-range or 10 km mesh capabilities without physical relay nodes present.

---

## 2. Test Plan Catalog

### Protocol 1: Open-Sky Highway Baseline
- **Target Condition**: Continuous high-speed cruise (60–90 km/h) under unobstructed sky.
- **Objective**: Verify GNSS healthy state stability, zero false-positive outage triggering, and steady-state ML speed estimator tracking.
- **Duration**: Minimum 10 minutes (approx. 10–15 km).
- **Procedure**:
  1. Affix phone securely to windshield / dashboard mount.
  2. In Continuum IDR app, select Profile `CAR`, Route `Highway Cruise`.
  3. Start trip and drive continuous highway corridor.
  4. Stop trip and inspect logs.
- **Acceptance Criteria**:
  - `gnss_coverage_pct` > 98%.
  - `outage_episodes_count` = 0.
  - Zero `OUT_OF_ORDER_IMU` anomalies.
  - Average IMU rate >= 9.0 Hz (target 10.0 Hz).

---

### Protocol 2: Urban Arterial, Traffic Congestion & ZUPT Hysteresis
- **Target Condition**: Dense city traffic with frequent traffic lights, bumper-to-bumper crawl (< 5 km/h), and complete standstills.
- **Objective**: Verify Zero-Velocity Update (ZUPT) hysteresis filter and gyro bias drift suppression during prolonged vehicle idling.
- **Duration**: 15–25 minutes.
- **Procedure**:
  1. Select Profile `CAR`, Route `Stop & Go Traffic`.
  2. Start trip at intersection.
  3. Cycle through stop-and-go events (minimum 5 complete stops lasting > 15 seconds each).
  4. Verify that estimated speed locks to exactly 0.0 m/s when stopped, preventing forward creep.
- **Acceptance Criteria**:
  - `speed_mps` drops to 0.0 m/s during stops without oscillation.
  - Gyro online bias estimator updates during confirmed ZUPT intervals.
  - No runaway position drift while stationary at red lights.

---

### Protocol 3: Rough Roads, Patched Asphalt & Speed Breakers
- **Target Condition**: Indian urban road ruts, patched asphalt sections, unpaved cobblestones, and successive speed humps.
- **Objective**: Verify shock disturbance rejection, vertical acceleration spike filtering, and surface anomaly classification (`SPEED_BREAKER`, `POTHOLE`).
- **Duration**: 5–10 minutes.
- **Procedure**:
  1. Select Profile `CAR`, Route `Potholes & Patched` or `Speed Breakers`.
  2. Traverse known speed breakers at speeds of 15–30 km/h.
  3. Observe real-time HUD and surface event classification.
- **Acceptance Criteria**:
  - Surface events properly tagged with `POTHOLE` or `SPEED_BREAKER` and severity metric [0.0–1.0].
  - Shocks do NOT falsely trigger ZUPT stops or corrupt longitudinal dead-reckoning speed.

---

### Protocol 4: Extended Tunnel & Underpass Total GNSS Blackout
- **Target Condition**: Multi-lane road tunnel or enclosed underpass exceeding 30 seconds of total satellite loss.
- **Objective**: Measure dead-reckoning endpoint error, drift % of distance traveled, and recovery settling time upon tunnel exit.
- **Duration**: Full tunnel transit (minimum 200m).
- **Procedure**:
  1. Select Profile `CAR`, Route `Underpass / Tunnel`.
  2. Maintain constant speed or normal traffic flow inside tunnel.
  3. Record entry timestamp, GNSS timeout, dead-reckoning propagation, and exit fix acquisition.
- **Acceptance Criteria**:
  - Engine immediately transitions from `GNSS_HEALTHY` -> `OUTAGE_PENDING` -> `FALLBACK_ACTIVE`.
  - Continuous 10 Hz planar trajectory propagation inside tunnel.
  - Smooth blended recovery transition upon satellite re-acquisition (`RECOVERING` -> `GNSS_HEALTHY`) without discontinuous visual jumps.
  - Export report via `idr evaluate-reference <trip.jsonl> --reference <rtk.csv>`.

---

### Protocol 5: Multi-Level Spiral Parking Garage & Reverse Crawl
- **Target Condition**: Enclosed multi-level concrete parking structure with tight spiral ramps and reverse parking crawl.
- **Objective**: Verify low-speed dead reckoning, reverse gear detection (negative velocity convention), and heading integration over continuous 360°/720° ramp rotations.
- **Duration**: 5–10 minutes.
- **Procedure**:
  1. Select Profile `PARKING`, Route `Parking Ramp & Reverse`.
  2. Descend/ascend at least 2 levels via spiral ramps.
  3. Perform a 3-point turn or reverse bay parking maneuver (< 5 km/h).
- **Acceptance Criteria**:
  - Reverse crawl correctly detected via negative longitudinal accelerometer jerk.
  - Continuous heading tracking throughout multi-turn spiral descent.

---

### Protocol 6: Motorcycle High-Lean & Engine Vibration
- **Target Condition**: Two-wheeler / scooter commute with handlebar/pocket mount, sharp cornering lean, and single-cylinder engine idling rumble.
- **Objective**: Verify lean-angle compensated yaw rate ($\theta = \arctan(v\omega / g)$) and vibration immunity.
- **Duration**: 10–20 minutes.
- **Procedure**:
  1. Secure phone in rigid handlebar cradle or rider chest pocket.
  2. Select Profile `MOTORCYCLE`, Route `Motorcycle High Lean`.
  3. Ride through roundabouts and sharp corner turns.
- **Acceptance Criteria**:
  - Lean angle computed and logged (`lean_angle_deg`).
  - High-frequency engine harmonics do not cause false velocity runaway.

---

### Protocol 7: External High-Rate IMU (100 Hz / 200 Hz)
- **Target Condition**: USB-OTG, Bluetooth SPP, or CAN-bus connected industrial IMU streaming at 100 Hz or 200 Hz.
- **Objective**: Validate high-frequency propagation scheduler, timestamp sub-millisecond jitter, and latency.
- **Procedure**:
  1. Select Profile `EXTERNAL_IMU`.
  2. Benchmark propagation scheduler throughput using `idr benchmark-scheduler --samples 5000`.
- **Acceptance Criteria**:
  - Propagation execution budget < 100 microseconds per sample.
  - Zero sample queue overflow or memory leak.

---

## 3. Data Processing & Ingestion Workflow

Once a field run is finished:

1. **Pull logs from device**:
   ```powershell
   .\tools\adb\device_validate.ps1 -Action pull
   ```
2. **Audit and validate field trip**:
   ```bash
   idr validate-phone-log artifacts/device_validation/trips/<trip_file>.jsonl
   ```
3. **Generate Markdown validation report**:
   ```bash
   idr phone-report artifacts/device_validation/trips/<trip_file>.jsonl --output artifacts/device_validation/reports/field_report.md
   ```
4. **Evaluate against reference trajectory (if RTK reference is available)**:
   ```bash
   idr evaluate-reference artifacts/device_validation/trips/<trip_file>.jsonl --reference data/reference/rtk_truth.csv --output-report artifacts/device_validation/reports/eval_report.md
   ```
