# Continuum IDR — Android Source & Application Project

This directory contains a complete, verified Gradle Android application project and Kotlin location engine for Continuum IDR. The application runs on-device dead reckoning, renders offline vector road maps, exchanges cooperative BLE hazard beacons, and logs Schema 1.0.0 trip files in a foreground service.

## Included Modules & Components

| Component | Path | Purpose |
| :--- | :--- | :--- |
| **Location Engine** | `app/src/main/java/ai/continuum/idr/ContinuumLocationEngine.kt` | Fuses IMU & GNSS, handles 2.0s causal feature extraction (6 channels $\times$ 7 stats = 42 features), alignment estimation, tilt-shift detection ($>15^\circ$), gradual recovery blending, vehicle profiles (`CAR`, `MOTORCYCLE`, `PARKING`, `EXTERNAL_IMU`), and topological map snapping. |
| **Portable Tree Runner** | `app/src/main/java/ai/continuum/idr/PortableTreeRunner.kt` | Evaluates trained `HistGradientBoosting` speed trees and `LogisticRegression` stop classifier directly from JSON without Python dependencies. |
| **Road Graph Pack** | `app/src/main/java/ai/continuum/idr/RoadGraphPack.kt` | Ingests offline topological road network packs, spatial cell indexing, candidate search, cross-track error, and ambiguity scoring. |
| **Offline Map Canvas** | `app/src/main/java/ai/continuum/idr/MapView.kt` | Zero-dependency offline vector canvas rendering topological roads, vehicle heading arrow, trajectory trail, uncertainty circle, and scale bar. |
| **Cooperative BLE V2V** | `app/src/main/java/ai/continuum/idr/TrafficBleManager.kt` | Localized Vehicle-to-Vehicle (V2V) hazard broadcasting and scanning over Bluetooth Low Energy. |
| **Foreground Service** | `app/src/main/java/ai/continuum/idr/TrackingService.kt` | Foreground trip recorder writing Schema 1.0.0 JSONL logs with Line 1 metadata, model SHA-256 hash, and raw sensors. |
| **Activity UI** | `app/src/main/java/ai/continuum/idr/MainActivity.kt` | Telemetry HUD (speed, bearing, accuracy, lat/lon, road match, motorcycle lean angle), profile selector, interactive map view, and trip log exporter (`Intent.ACTION_SEND`). |
| **Unit Tests** | `app/src/test/java/ai/continuum/idr/ParityTest.kt` | Validates speed prediction, stop classification, and uncertainty against golden multi-stage fixture `parity_fixture.json`. |
| **Unit Tests** | `app/src/test/java/ai/continuum/idr/RoadGraphPackTest.kt` | Validates geographic projection, spatial candidate queries, and parallel-road ambiguity detection. |

---

## Build and Test Instructions

Prerequisites: Android SDK Platform 35 or 36, Android Build-Tools 35.0.0, and Java 17.

```powershell
# Run Kotlin JVM unit tests
.\gradlew.bat testDebugUnitTest

# Assemble installable Debug APK
.\gradlew.bat assembleDebug
```

The compiled APK will be created at:
```
android/app/build/outputs/apk/debug/app-debug.apk
```
(Current build size: ~1.09 MB; includes pre-packaged `motion_portable.json` and `sample_road_pack.json`).

---

## Trip Recording & Export Workflow

1. Install the APK on an Android 8.0+ (API 26+) device.
2. Grant Location, Notification, and Bluetooth permissions when prompted.
3. Select the vehicle profile (`CAR`, `MOTORCYCLE`, `PARKING`, `EXTERNAL_IMU`).
4. Tap **Start Trip**. A persistent foreground notification confirms tracking.
5. Accelerate straight ($v > 2\text{ m/s}$) for initial orientation calibration.
6. The app continuously displays real-time speed, heading, uncertainty, road match status, and offline vector map.
7. Tap **Stop Trip**.
8. Trip logs are saved as `continuum_YYYYMMDD_HHMMSS.jsonl` under `Android/data/ai.continuum.idr/files/trips/`.
9. Tap **Export** next to any recorded trip to share via Gmail, Google Drive, or retrieve using `adb pull`:
   ```powershell
   adb pull /sdcard/Android/data/ai.continuum.idr/files/trips/ ./my_trips/
   ```

---

## Field Validation Protocol & Ingestion

Recorded trips can be ingested directly into the Python evaluation stack:
```powershell
# Audit trip data quality, sensor sampling rate, and latency gaps
python -m continuum_idr.cli validate-phone-log path/to/trip.jsonl

# Generate formal Markdown field evaluation report
python -m continuum_idr.cli phone-report path/to/trip.jsonl --output report.md
```

See [`docs/INDIAN_ROAD_COLLECTION_PROTOCOL.md`](../docs/INDIAN_ROAD_COLLECTION_PROTOCOL.md) for detailed test procedures across Indian road topologies, motorcycle lean cornering, and multi-level parking structures.
