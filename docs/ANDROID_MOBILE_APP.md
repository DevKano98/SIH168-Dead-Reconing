# Continuum IDR — Native Android Mobile Application

The Continuum IDR Android app is a production-grade native application built in Kotlin. It runs the entire navigation fallback pipeline on-device in real time without network connectivity.

---

## 1. Android Application Architecture

The application is structured around a foreground recording service, an on-device tree runner, a zero-dependency vector map canvas, a cooperative BLE manager, and an automotive cockpit UI.

```
android/app/src/main/
├── AndroidManifest.xml                  # Permissions & service declarations (Android 14/15 FGS)
├── assets/
│   ├── motion_portable.json             # Serialized ML model weights
│   └── sample_road_pack.json            # Electronic City Corridor offline vector road network
├── java/ai/continuum/idr/
│   ├── MainActivity.kt                  # Automotive Cockpit HUD UI & telemetry receiver
│   ├── TrackingService.kt               # Foreground service & JSONL event logger
│   ├── ContinuumLocationEngine.kt       # Drop-in Android location fallback engine
│   ├── PortableTreeRunner.kt            # Zero-dependency on-device tree runner
│   ├── SystemMockRelay.kt               # Android OS GPS Mock Provider (feeds Google Maps)
│   ├── TrafficBleManager.kt             # Cooperative BLE V2V mesh hazard transport
│   ├── MapView.kt                       # Offline vector road network canvas with touch gestures
│   └── RoadGraphPack.kt                 # Road topology parser & spatial matcher
└── res/
    ├── drawable/                        # Custom automotive UI shape drawables (cards, pills, buttons)
    └── values/styles.xml                # App theme definitions
```

---

## 2. Automotive Cockpit HUD User Interface

The UI in [`MainActivity.kt`](file:///d:/iovnbd/IO-VNBD/android/app/src/main/java/ai/continuum/idr/MainActivity.kt) is styled as a sleek, dark-mode automotive instrument cluster:

```
┌────────────────────────────────────────────────────────┐
│ CONTINUUM IDR • SATELLITE FALLBACK SYSTEM              │
│ [● GNSS LOCKED (ACTIVE) / INERTIAL FALLBACK ACTIVE]   │
├──────────────┬──────────────┬──────────────────────────┤
│ SPEED (KM/H) │ HEADING      │ UNCERTAINTY              │
│    48.2      │   042° NE    │    ±2.4m                 │
│   KM / H     │  Lean: 0.0°  │ EC_EXPRESSWAY (94%)      │
├──────────────┴──────────────┴──────────────────────────┤
│ ┌────────────────────────────────────────────────────┐ │
│ │             OFFLINE VECTOR TACTICAL MAP            │ │
│ │  (Real-time vehicle marker, road graph, snapping) │ │
│ └────────────────────────────────────────────────────┘ │
│ [Anchor to Demo Route (Indoor)]  [Recenter Vehicle]   │
├────────────────────────────────────────────────────────┤
│ GOOGLE MAPS & NAVIGATION RELAY                         │
│ Push dead-reckoning directly to Android OS GPS provider│
│ [ENABLE MOCK GPS]  Status: Ready to feed Google Maps  │
├────────────────────────────────────────────────────────┤
│ VEHICLE PROFILE: [CAR ▼]     ROUTE: [Highway Cruise ▼] │
├────────────────────────────────────────────────────────┤
│ [     START TRIP     ]     [      STOP TRIP      ]    │
├────────────────────────────────────────────────────────┤
│ SYSTEM & INFERENCE TELEMETRY                           │
│ Inference: 112 µs • Heap: ~4.2 MB • IMU: 100 Hz (3,240)│
├────────────────────────────────────────────────────────┤
│ COOPERATIVE V2V TRAFFIC (BLE DIRECT 10–30M)           │
│ [Trigger Pothole (BLE)]     [Trigger Outage (BLE)]     │
├────────────────────────────────────────────────────────┤
│ RECORDED TRIPS ARCHIVE (JSONL EXPORT)                  │
│ continuum_20260930_210512.jsonl (142 KB)      [Export] │
└────────────────────────────────────────────────────────┘
```

### Component Details
1. **System State Ribbon:** Full-width pill badge displaying live engine state:
   - `● GNSS LOCKED (ACTIVE)` (Emerald Green `#059669`)
   - `● WAITING FOR GNSS LOCK (INDOOR)` (Amber `#D97706`)
   - `● INERTIAL DEAD RECKONING (FALLBACK ACTIVE)` (Crimson Red `#DC2626`)
   - `● RE-CONVERGING GNSS` (Blue `#2563EB`)
2. **Hero Bento Metric Cluster:**
   - **Speedometer:** Prominent bold digital display with clear unit formatting.
   - **Heading & Compass:** 3-digit bearing (`042°`), cardinal direction (`NE`), and motorcycle lean angle.
   - **Precision & Road Match:** Live accuracy radius (`±2.4m`) and active OSM road segment with match confidence percentage.
3. **Google Maps & Navigation Relay:**
   - One-tap toggle button to connect Continuum's dead-reckoned output directly to Android's OS GPS subsystem.
4. **Tactical Vector Canvas (`MapView.kt`):**
   - High-contrast road segments, vehicle heading chevron, uncertainty ellipse, and breadcrumb trails.
   - Touch gestures (pinch-to-zoom, pan, vehicle auto-follow).
   - "Anchor Demo" button for instant indoor desk testing.

---

## 3. Background Service Lifecycle & Android 14/15 Compatibility

In [`TrackingService.kt`](file:///d:/iovnbd/IO-VNBD/android/app/src/main/java/ai/continuum/idr/TrackingService.kt):
- Runs as a persistent foreground service with ongoing notification.
- **Android 14+ (API 34/35) Compliance:** Explicitly declares and invokes `startForeground()` with `ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION`.
- **Decoupled Bluetooth Permissions:** Core location tracking only requires `ACCESS_FINE_LOCATION` and `POST_NOTIFICATIONS`. If a user denies optional Bluetooth permissions, the location engine continues running normally.
- **500 ms Diagnostic Heartbeat:** Emits live sample counts and memory stats to the UI even before the first satellite fix arrives.

---

## 4. Vehicle Profiles & Specialized Kinematics

Continuum IDR includes four vehicle profiles:
1. **`CAR`:** Standard four-wheeled vehicular kinematics.
2. **`MOTORCYCLE`:** High-lean dynamics. The engine computes lean angle $\theta_{\text{lean}} = \operatorname{atan2}(v \cdot \omega_z, g)$ to compensate for lateral accelerometer centripetal contamination during sharp turns.
3. **`PARKING`:** Crawl and reverse detection. Detects reverse gear from negative longitudinal acceleration bursts ($< -1.8\,\text{m/s}^2$) starting from rest, enabling accurate parking garage tracking.
4. **`EXTERNAL_IMU`:** Configured for high-rate external BLE/USB inertial sensors sampling up to 200 Hz.

---

## 5. Cooperative V2V Traffic Mesh (BLE)

[`TrafficBleManager.kt`](file:///d:/iovnbd/IO-VNBD/android/app/src/main/java/ai/continuum/idr/TrafficBleManager.kt) provides vehicle-to-vehicle hazard warnings without cellular internet:
- **Range:** Direct 10–30 meters line-of-sight.
- **Payload:** 18-byte packed binary beacon containing hazard type, severity (0–100), and WGS-84 coordinates.
- **Hazard Types:** `GNSS_OUTAGE`, `SPEED_BREAKER`, `POTHOLE`, `TRAFFIC_JAM`.
- **Deduplication:** Automatic 30-second deduplication filter preventing duplicate alerts from nearby cars.

---

## 6. How to Build & Test the Android App

### Build Debug APK
```powershell
cd android
.\gradlew.bat assembleDebug
```
The output APK is generated at:
`android/app/build/outputs/apk/debug/app-debug.apk`

### Run JVM Unit Tests
```powershell
cd android
.\gradlew.bat testDebugUnitTest
```
Runs:
- `ParityTest.kt` (Python vs. Kotlin ML prediction parity)
- `RoadGraphPackTest.kt` (Topological spatial road snapping)
- `InstrumentationTest.kt` (Diagnostic metrics & data structures)
