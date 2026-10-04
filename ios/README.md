# Continuum IDR — iOS Reference Application & CoreMotion Fallback Engine

**Continuum IDR** is a 100% offline, hardware-free Edge Dead-Reckoning navigation engine and reference application for iOS. It takes over the exact millisecond GPS signals drop out (tunnels, double-decker flyovers, underground parking), utilizing exclusively the 6-DoF accelerometer and gyroscope sensors already inside the iPhone.

---

## 📱 Features

- **Sub-Microsecond Edge ML Speed Regressor:** Evaluates gradient-boosted decision trees (`HistGradientBoosting`) and Logistic Regression Zero-Velocity Updates (ZUPT) from a 42-moment IMU window in **<100 µs** in pure Swift.
- **Indian Road Surface & Dynamics Adaptation:**
  - Dynamic $a_z$ vertical jerk filter to reject pothole ($<-4.0\ \text{m/s}^2$) and speed breaker ($>4.5\ \text{m/s}^2$) shocks.
  - Motorcycle roll-lean angle decoupling: $\theta = \arctan(v \cdot \omega / g)$.
  - Basement parking crawl and reverse gear detection.
- **Offline Vector Road Map Canvas:** Hardware-accelerated SwiftUI `Canvas` rendering road networks, dynamic uncertainty ellipses, heading cones, and breadcrumb trails.
- **Cooperative V2V Mesh (BLE):** Broadcasts and receives 18-byte ad-hoc peer-to-peer hazard beacons over Bluetooth Low Energy without cellular data.
- **Smooth Re-convergence Blending:** 2.5-second exponential decay filter smoothly merges dead-reckoned positions back into satellite fixes when exiting tunnels.
- **Schema 1.0.0 JSONL Trip Recorder:** Cryptographically verifiable telemetry logging with SHA-256 model hashing and one-tap Share Sheet export.

---

## 🏗️ Architecture & Project Structure

```
ios/
├── ContinuumIDR.xcodeproj/          # Full Xcode Project (iOS 16+)
│   └── project.pbxproj
├── Package.swift                    # Swift Package Manager (SPM) manifest
├── ContinuumIDR/
│   ├── App/
│   │   └── ContinuumIDRApp.swift    # SwiftUI App Lifecycle Entry Point
│   ├── Core/
│   │   ├── ContinuumLocationEngine.swift  # 10 Hz Dead-Reckoning & Fallback Engine
│   │   ├── PortableTreeRunner.swift       # Zero-dependency Tree & ZUPT Evaluator
│   │   ├── RoadGraphPack.swift            # 2D Spatial Hash Grid & Map Matching
│   │   ├── TrafficBleManager.swift        # CoreBluetooth V2V Hazard Mesh
│   │   └── TripRecorder.swift             # Schema 1.0.0 JSONL Trip Logger
│   ├── Models/
│   │   ├── VehicleProfile.swift           # CAR, MOTORCYCLE, PARKING, EXTERNAL_IMU
│   │   ├── FallbackState.swift            # GNSS_HEALTHY, FALLBACK_ACTIVE, RECOVERING
│   │   ├── EngineDiagnostics.swift        # Latency & Memory Telemetry Struct
│   │   ├── TrafficHazardReport.swift      # BLE Hazard Data & Stats
│   │   └── MapMatchResult.swift           # Snapped Lat/Lon & Road Heading
│   ├── Views/
│   │   ├── ContentView.swift              # Main Cockpit Dashboard
│   │   ├── BentoMetricCard.swift          # Reusable Metric Instrument Card
│   │   ├── OfflineMapView.swift           # Interactive Vector Road Canvas
│   │   └── TripHistoryView.swift          # Trip Browser with iOS Share Sheet
│   └── Resources/
│       ├── Info.plist                     # Permissions & Background Modes
│       ├── Assets.xcassets/               # Dark Mode Colors & App Icons
│       ├── motion_portable.json           # Trained Edge ML Model Bundle (887 KB)
│       ├── sample_road_pack.json          # Bangalore Electronic City Vector Map (26 KB)
│       └── parity_fixture.json            # Numerical Parity Checkpoints (68 KB)
└── ContinuumIDRTests/
    ├── ParityTests.swift                  # Python-Kotlin-Swift Numerical Verification (<1e-4)
    ├── RoadGraphPackTests.swift           # Spatial Hashing & Coordinate Projection Tests
    └── FeatureExtractionTests.swift       # 42-Moment IMU Window Unit Tests
```

---

## 🚀 How to Run

### Option 1: Classic Xcode Project (Recommended)
1. Open the project on macOS:
   ```bash
   open ios/ContinuumIDR.xcodeproj
   ```
2. Select your target device:
   - **Simulator:** `iPhone 15 Pro` or `iPhone 16`
   - **Physical Device:** Connect iPhone via USB/Wi-Fi with Developer Mode enabled.
3. Press **Cmd + R** to Build & Run.

### Option 2: Swift Package Manager
```bash
cd ios
swift test
```

---

## 🧪 Testing Indoors or on iOS Simulator

No vehicle or physical movement is required to verify all features:
1. Tap **"START TRIP"** in the cockpit.
2. Tap **"Anchor to Demo Route (Indoor Test)"**:
   - Immediately initializes navigation origin at **Electronic City Elevated Tollway, Bangalore** (`12.8450°N, 77.6620°E`).
   - Automatically activates **INERTIAL DEAD RECKONING (FALLBACK ACTIVE)** mode.
3. Tap **"Simulate 2s Step"**:
   - Injects forward velocity and slight curve.
   - Observes the speedometer, heading compass, uncertainty radius, vector road map, and breadcrumb trail updating in real time!
4. Tap **"Trigger Pothole"** or **"Trigger Outage"** to test BLE cooperative hazard broadcasting.
5. Tap **"STOP TRIP"** and export the resulting `.jsonl` file via the iOS Share Sheet.

---

## 🔒 Privacy Permissions Configured

In `ContinuumIDR/Resources/Info.plist`:
- `NSLocationWhenInUseUsageDescription`: Initial GNSS seed and accuracy validation.
- `NSLocationAlwaysAndWhenInUseUsageDescription`: Uninterrupted background dead-reckoning.
- `NSMotionUsageDescription`: 6-DoF accelerometer and gyroscope sensor streams.
- `NSBluetoothAlwaysUsageDescription` & `NSBluetoothPeripheralUsageDescription`: Peer-to-peer V2V hazard exchange.
- `UIBackgroundModes`: `location`, `bluetooth-central`, `bluetooth-peripheral`.

---

## 🔬 Mathematical Parity Verification

The Swift implementation has verified numerical parity with Python `scikit-learn` and Android Kotlin via `ParityTests.swift`:
- **Speed Prediction:** Maximum error $< 10^{-4}\ \text{m/s}$.
- **ZUPT Stop Probability:** Maximum error $< 10^{-4}$.
- **Discrete Stop Decision:** 100% state match.
- **Uncertainty Interval:** Exact bin lookup match.
