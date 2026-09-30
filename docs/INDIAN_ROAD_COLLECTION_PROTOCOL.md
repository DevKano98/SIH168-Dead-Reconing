# Indian Road Data Collection & Ground Truth Validation Protocol

## 1. Objective and Scope
This document specifies the standard operating procedure (SOP) for capturing, annotating, and benchmarking real-world vehicle inertial and GNSS sensor logs across Indian road conditions using the Continuum IDR Android reference app.

The target environment includes high-density traffic congestion, severe road roughness (unmarked speed humps, rumble strips, deep potholes), diverse vehicle dynamics (motorcycles with high roll lean angles, three-wheeled auto-rickshaws, passenger cars, commercial buses), and recurring GNSS denial environments (underpasses, multi-level elevated flyovers, tunnels, and basement parking garages).

---

## 2. Vehicle Class Specifications

| Class | Profile Identifier | Dynamics & Vibration Signature | Typical Outage Scenarios |
| :--- | :--- | :--- | :--- |
| **Two-Wheeler** | `MOTORCYCLE` | Roll lean angles up to 35° during cornering; high single-cylinder engine vibration (20–40 Hz); lane-filtering crawl | Under-flyover U-turns, short underpasses, tree-canopy shade |
| **Three-Wheeler** | `CAR` (or Custom) | Low mass, high roll compliance, rapid steer changes, pronounced chassis shudder | Flyover shadows, high-density market canyons |
| **Passenger Car** | `CAR` | 4-wheel independent suspension, standard passenger vehicle dynamics ($a_{\max} \approx 4\text{ m/s}^2$) | Underground tunnels, basement parking, elevated expressways |
| **Parking Maneuvers** | `PARKING` | Low speed crawl ($\le 1.5\text{ m/s}$), tight radius turning, reverse gear backing | Multi-level basement parking garages (complete GNSS denial) |
| **High-Rate External IMU** | `EXTERNAL_IMU` | Industrial IMU (100–200 Hz) via BLE/USB or Android high-rate sensor interface | Mixed urban and highway navigation |

---

## 3. Phone Mount Modes & Ground Truth Calibration

Each collection run must record the mount configuration in its trip notes:

1. **Rigid Dashboard / Windshield Cradle (Recommended Baseline)**:
   - Secured firmly using suction cup or mechanical clamp.
   - Eliminates relative phone-to-vehicle motion.
   - Enables clean alignment estimation from initial straight acceleration ($v > 2.0\text{ m/s}$).
2. **AC Vent Clamp / Magnetic Mount**:
   - Phone clamped to vent slats.
   - May experience slight vibration resonance during rough road traversal.
3. **Cup Holder / Center Console**:
   - Resting loosely in console or tray.
   - Engine tilt tracking detects slippage $> 15^\circ$ via gravity vector monitoring.
4. **Driver Trousers Pocket (Stress Test)**:
   - High biomechanical noise from pedal actuation and body movement.
   - Evaluates filter robustness against spurious acceleration.

---

## 4. Indian Road Topologies & Anomaly Signatures

1. **Speed Breakers & Rumble Strips**:
   - **Signature**: Sharp positive vertical linear acceleration spike ($a_z > 4.5\text{ m/s}^2$) followed by negative rebound ($a_z < -3.0\text{ m/s}^2$).
   - **Verification**: Android app flags `SPEED_BREAKER` anomaly with severity metric and logs exact timestamp.
2. **Potholes & Broken Asphalt**:
   - **Signature**: Rapid negative vertical acceleration drop ($a_z < -4.0\text{ m/s}^2$) followed by sharp impact spike.
   - **Verification**: Android app flags `POTHOLE` anomaly.
3. **Elevated Expressways & Lower-Deck Surface Roads (e.g. Bangalore Electronic City / Hosur Road)**:
   - **Challenge**: The surface road directly underlies the elevated concrete deck, creating severe multipath reflections and sky obstruction.
   - **Verification**: Road graph topology matching resolves horizontal lane separation and flags ambiguity between elevated and surface decks.
4. **Multi-Level Basement Parking Garages**:
   - **Challenge**: Immediate $100\%$ GNSS signal loss upon ramp descent; multi-point turns and reverse parking.
   - **Verification**: Parking profile applies low-speed crawl thresholding and reverse gear detection.

---

## 5. Step-by-Step Collection Checklist

### Pre-Drive Preparation
1. Ensure the Android device has at least **200 MB** of free internal storage.
2. Verify battery level $\ge 50\%$ or connect to vehicle USB power.
3. Open **Continuum IDR** on the phone.
4. Confirm permissions: **Fine Location**, **Foreground Service**, and **Bluetooth** (for cooperative traffic sharing).
5. Select the appropriate **Vehicle Profile** (`CAR`, `MOTORCYCLE`, `PARKING`, `EXTERNAL_IMU`).
6. Verify that the offline map canvas displays the regional road pack (e.g. `sample_road_pack.json`).

### Collection Execution
1. Tap **Start Trip**.
2. Verify notification banner appears: *"Continuum IDR recording — Capturing phone sensors, GNSS, and road topology"*.
3. Begin drive with a steady straight acceleration ($v > 2\text{ m/s}$) for at least 5 seconds so the engine can calibrate forward orientation.
4. Note key landmarks or timestamps during the drive (tunnel entry, ramp departure, speed breaker crossings).
5. Upon reaching the destination or completing the test episode, tap **Stop Trip**.

### Post-Drive Validation
1. Verify the trip file is listed in the app: `continuum_YYYYMMDD_HHMMSS.jsonl`.
2. Tap **Export** to share the log via email, Google Drive, or transfer via USB `adb pull`.
3. In the development terminal, run the validation tool:
   ```powershell
   python -m continuum_idr.cli validate-phone-log path/to/continuum_YYYYMMDD_HHMMSS.jsonl
   ```
4. Generate the formal Markdown field evaluation report:
   ```powershell
   python -m continuum_idr.cli phone-report path/to/continuum_YYYYMMDD_HHMMSS.jsonl --output artifacts/reports/field_report.md
   ```

---

## 6. Audit Criteria & Pass/Fail Thresholds

| Metric | Target | Failure Action |
| :--- | :--- | :--- |
| **Line 1 Metadata** | Valid JSON with `type: "metadata"`, `version: "1.0.0"`, and valid `model_hash` | Reject file; recorder aborted early |
| **IMU Sampling Rate** | $10.0\text{ Hz} \pm 1.5\text{ Hz}$ (or $200\text{ Hz} \pm 20\text{ Hz}$ for high-rate) | Check battery optimization / sensor throttling |
| **Sensor Latency Gap** | Max gap $< 0.250\text{ s}$ | Inspect Android OS background killing |
| **Monotonicity** | Strictly increasing sensor timestamps ($t_k > t_{k-1}$) | Reject run if clock jumps backwards |
| **GNSS Outage Drift** | Target drift rate $< 25\%$ (without map) or $< 10\%$ (with road snapping) | Analyze gyro drift bias and wheel-hop shocks |
