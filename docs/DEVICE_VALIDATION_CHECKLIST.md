# Continuum IDR — Android Physical Device Validation Checklist

This checklist defines the operational verification gates required before and after conducting live in-vehicle road evaluations using the Continuum IDR Android application.

---

## Phase 1: Pre-Flight Hardware & Device Configuration

| Gate | Check Item | Verification Command / Step | Expected Status | Checked |
| :--- | :--- | :--- | :--- | :--- |
| **1.1** | ADB Connection | `.\tools\adb\device_validate.ps1 -Action check` | Device listed in `device` state | [ ] |
| **1.2** | Sensor Suite Audit | `.\tools\adb\device_validate.ps1 -Action info` | Gyroscope, Accelerometer, Gravity active | [ ] |
| **1.3** | APK Build & Integrity | `.\tools\adb\device_validate.ps1 -Action install` | APK installs cleanly with runtime permissions | [ ] |
| **1.4** | Model Asset Hash | Inspect `device_profile.json` | Matches `c98f71fd9b20af...` | [ ] |
| **1.5** | Battery Optimization | Settings -> Battery -> Apps -> Continuum IDR | Set to **Unrestricted** (prevents background throttle) | [ ] |
| **1.6** | Location Permissions | Settings -> Apps -> Continuum IDR -> Permissions | "Allow all the time", High Accuracy GNSS enabled | [ ] |
| **1.7** | Bluetooth Permissions | Settings -> Apps -> Continuum IDR -> Nearby Devices | Allowed (Scan, Advertise, Connect) | [ ] |

---

## Phase 2: In-Vehicle Mount & Sensor Calibration

| Gate | Check Item | Protocol Standard | Expected Indicator | Checked |
| :--- | :--- | :--- | :--- | :--- |
| **2.1** | Rigid Cradle Mount | Solid dashboard or windshield cradle (no flopping/wobbling) | Stable gravity vector ($~9.81\text{ m/s}^2$) | [ ] |
| **2.2** | Vehicle Profile | In-app selector dropdown | `CAR`, `MOTORCYCLE`, or `PARKING` | [ ] |
| **2.3** | Route Category | In-app route dropdown | Select specific target operational category | [ ] |
| **2.4** | Initial Sky View | Open sky prior to trip start | State Badge shows `GNSS_HEALTHY` (Green) | [ ] |
| **2.5** | Offline Road Pack | Embedded assets: `sample_road_pack.json` | Vector road centerline overlays visible on MapView | [ ] |

---

## Phase 3: Live Driving & Outage Execution

| Step | Action | Expected Application Reaction | Pass / Fail |
| :--- | :--- | :--- | :--- |
| **3.1** | Tap **"Start Trip"** | Status updates to `"Recording sensors and GNSS..."` | [ ] |
| **3.2** | Stop-and-Go Crawl | State badge remains green; vehicle speed drops smoothly to 0.0 m/s without forward drift | [ ] |
| **3.3** | Pothole / Speed Breaker | App surfaces detected anomaly event with severity level | [ ] |
| **3.4** | Enter Tunnel / Outage | After 2.0s without fix, badge transitions to `FALLBACK_ACTIVE` (Red); continuous 10 Hz dead reckoning | [ ] |
| **3.5** | Exit Tunnel / Recovery | Upon satellite recovery, badge transitions to `RECOVERING` (Amber) then `GNSS_HEALTHY` (Green); smooth blend | [ ] |
| **3.6** | BLE Hazard Broadcast | Tap **"Trigger Pothole (BLE)"**; Relay HUD increments Sent count | [ ] |
| **3.7** | Tap **"Stop Trip"** | Status confirms trip saved; JSONL entry added to list | [ ] |

---

## Phase 4: Data Offload, Ingestion & Quality Gates

Run the post-flight automation script:

```powershell
# 1. Pull recorded trip logs
.\tools\adb\device_validate.ps1 -Action pull

# 2. Audit sensor data quality
idr validate-phone-log artifacts/device_validation/trips/<trip_file>.jsonl

# 3. Generate Markdown validation report
idr phone-report artifacts/device_validation/trips/<trip_file>.jsonl --output artifacts/device_validation/reports/trip_report.md
```

### Quality Gate Pass Criteria:
- [ ] **Line 1 Metadata**: Schema version `1.0.0`, vehicle profile and route category present.
- [ ] **IMU Sampling Frequency**: Average IMU rate $\ge 9.0\text{ Hz}$ (target 10.0 Hz).
- [ ] **Maximum Timestamp Latency**: Max inter-sample gap $< 0.250\text{ s}$.
- [ ] **Zero Desync Anomalies**: No `OUT_OF_ORDER_IMU` or `INVALID_IMU` tags.
- [ ] **Diagnostics Record**: App writes closing diagnostics record with inference latency and memory metrics.

---

## Phase 5: Scientific Integrity & Evaluation Boundary

> [!IMPORTANT]
> - If an independent dual-frequency RTK GNSS truth file was collected, evaluate via:
>   `idr evaluate-reference <trip.jsonl> --reference <rtk_truth.csv> --output-report <report.md>`
> - If NO independent ground-truth was logged, the report MUST state:
>   **"Telemetry only, not accuracy validated."**
> - Historical IO-VNBD benchmark figures (80.32% median drift, 0% pass rate below 10%) must remain visible in documentation.
