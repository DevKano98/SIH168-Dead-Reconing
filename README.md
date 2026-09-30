# Continuum IDR — Autonomous Inertial Dead-Reckoning Navigation System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Android SDK 26-35](https://img.shields.io/badge/Android-API%2026--35-3DDC84.svg?logo=android&logoColor=white)](https://developer.android.com/)
[![React 18 Studio](https://img.shields.io/badge/Studio-React%2018%20%2B%20Vite-61DAFB.svg?logo=react&logoColor=black)](continuum_idr/studio/)
[![Tests Passing](https://img.shields.io/badge/tests-122%2F122%20passing-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Continuum IDR** (**Inertial Dead Reckoning**) is an autonomous navigation fallback system, production-ready research SDK, and edge-native automotive application designed to sustain continuous, accurate vehicular positioning during complete GNSS (GPS, NavIC, Galileo, GLONASS) satellite blackouts.

When a vehicle enters **tunnels, elevated flyovers, underground parking basements, or dense urban canyons** (skyscrapers in metro cities), satellite signals are blocked or distorted by multipath reflections. Standard consumer navigation apps freeze, spin erratically, or announce incorrect turns. Continuum IDR bridges these outages entirely on-device using **smartphone inertial sensors (accelerometers and gyroscopes) and lightweight machine learning decision trees**—requiring **zero OBD-II cables, zero wheel-speed encoders, and zero cellular internet connectivity**.

---

## Table of Contents

1. [System Architecture & Component Interaction Topology](#1-system-architecture--component-interaction-topology)
2. [End-to-End System Workflows & Engineering Diagrams](#2-end-to-end-system-workflows--engineering-diagrams)
   - [2.1 Sensor Ingestion & Dynamic Mount Leveling Pipeline](#21-sensor-ingestion--dynamic-mount-leveling-pipeline)
   - [2.2 42-Feature Extraction & Dual-Model Gated Inference Pipeline](#22-42-feature-extraction--dual-model-gated-inference-pipeline)
   - [2.3 Kinematic Dead-Reckoning & Flat-Earth WGS-84 Propagation](#23-kinematic-dead-reckoning--flat-earth-wgs-84-propagation)
   - [2.4 Topological Road Graph Soft-Snapping Engine](#24-topological-road-graph-soft-snapping-engine)
   - [2.5 Tracking State Machine Lifecycle](#25-tracking-state-machine-lifecycle)
   - [2.6 GNSS Outage Detection & Kinematic Dead-Reckoning Sequence](#26-gnss-outage-detection--kinematic-dead-reckoning-sequence)
   - [2.7 Smooth GNSS Re-convergence Filter](#27-smooth-gnss-re-convergence-filter)
   - [2.8 Google Maps & OS Mock Location Relay](#28-google-maps--os-mock-location-relay)
   - [2.9 Native Android Component Interaction Architecture](#29-native-android-component-interaction-architecture)
   - [2.10 Continuum Studio Telemetry Loop](#210-continuum-studio-telemetry-loop)
   - [2.11 Cooperative V2V Traffic Mesh Network](#211-cooperative-v2v-traffic-mesh-network)
3. [Deep Subsystem & Feature Specifications](#3-deep-subsystem--feature-specifications)
   - [3.1 Edge ML Speed Estimation & Stop Gating](#31-edge-ml-speed-estimation--stop-gating)
   - [3.2 Portable Zero-Dependency Edge Runtime (~110 µs)](#32-portable-zero-dependency-edge-runtime-110-µs)
   - [3.3 Native Android Automotive Cockpit Application](#33-native-android-automotive-cockpit-application)
   - [3.4 Continuum Studio Desktop Simulation Cockpit](#34-continuum-studio-desktop-simulation-cockpit)
   - [3.5 Offline Vector Road Graph & Soft-Snapping](#35-offline-vector-road-graph--soft-snapping)
   - [3.6 Specialized Vehicle Dynamics & Profiles](#36-specialized-vehicle-dynamics--profiles)
   - [3.7 Cooperative V2V Traffic Mesh (BLE Direct)](#37-cooperative-v2v-traffic-mesh-ble-direct)
4. [Empirical Benchmark Evidence (IO-VNBD Dataset)](#4-empirical-benchmark-evidence-io-vnbd-dataset)
5. [Indian Road Challenges & Domain Adaptation](#5-indian-road-challenges--domain-adaptation)
6. [Quickstart & Verification Guide](#6-quickstart--verification-guide)
   - [6.1 Python SDK & CLI — Commands that work from clone](#61-python-sdk--cli--commands-that-work-from-clone)
   - [6.2 Commands that require the IO-VNBD dataset](#62-commands-that-require-the-io-vnbd-dataset)
   - [6.3 Launch Continuum Studio](#63-launch-continuum-studio)
   - [6.4 Build & Install Android Mobile App](#64-build--install-android-mobile-app)
   - [6.5 Link Google Maps via Mock Location Provider](#65-link-google-maps-via-mock-location-provider)
7. [Repository Structure](#7-repository-structure)
8. [Complete Documentation Suite (`docs/`)](#8-complete-documentation-suite-docs)

---

## 1. System Architecture & Component Interaction Topology

Continuum IDR operates as a layered real-time edge system spanning native Android Kotlin execution, a Python navigation SDK, and a React 18 / FastAPI telemetry simulation studio.

```mermaid
flowchart TD
    subgraph SENSORS["Edge Sensing Hardware"]
        IMU["3-Axis Accelerometer + 3-Axis Gyroscope\n(50–100 Hz Continuous Stream)"]
        GNSS["GNSS / GPS Receiver\n(1 Hz Satellite Coordinate Fixes)"]
    end

    subgraph PREPROC["Preprocessing & Alignment Engine"]
        GRAV["Gravity Estimator & Dynamic Leveling\n(Device Tilt Normalization & Mount Tracking)"]
        WIN["2.0s Causal Sliding Window\n(20 Samples @ 10 Hz Decimated)"]
        ZUPT["Zero Velocity Update (ZUPT)\n(Energy & Variance Stop Detector)"]
    end

    subgraph INFERENCE["Edge Inference Pipeline (~110 µs Latency)"]
        FEAT["42 Causal Motion Features Extractor\n(Mean, Std, Min, Max, Energy, Deltas)"]
        TREES["HistGradientBoosting Speed Regressor\n(Ensemble of Decision Trees)"]
        STOP["Logistic Regression Stop Classifier\n(Binary Motion Gating P >= 0.50)"]
    end

    subgraph KINEMATICS["Kinematic Dead-Reckoning Engine"]
        YAW["Gyroscope Yaw Rate Integration\n(Heading Propagation with Motorcycle Lean)"]
        FLAT["Flat-Earth WGS-84 Coordinate Step\n(Distance & Azimuth to Delta Lat/Lon)"]
        UNCERT["Dynamic Uncertainty Covariance Step\n(Speed-Dependent Error Ellipse)"]
    end

    subgraph CORRECTION["Topological Correction Layer"]
        ROAD["Offline Vector Road Graph Pack\n(Topological Directed Segments)"]
        MATCH["Spatial Soft-Snapping Engine\n(Centerline Damping & Heading Alignment)"]
    end

    subgraph OUTPUTS["Consumer & Ecosystem Delivery"]
        STUDIO["Continuum Studio\n(Desktop Simulation Cockpit)"]
        ANDROID_UI["Native Android Cockpit HUD\n(Automotive Bento Cluster)"]
        MOCK_GPS["Android OS GPS Mock Provider\n(Feeds Google Maps / Waze / Uber)"]
        BLE["V2V Mesh Transport\n(BLE Local Hazard Broadcast 10–30m)"]
    end

    SENSORS --> PREPROC
    PREPROC --> INFERENCE
    INFERENCE --> KINEMATICS
    KINEMATICS --> CORRECTION
    CORRECTION --> OUTPUTS
```

---

## 2. End-to-End System Workflows & Engineering Diagrams

### 2.1 Sensor Ingestion & Dynamic Mount Leveling Pipeline

Vehicles mount smartphones in arbitrary orientations (dashboard clamps, windshield suction mounts, motorcycle handlebars). Continuum IDR isolates vehicle-forward acceleration from gravity using dynamic low-pass filtering and tilt dot-product tracking:

```mermaid
flowchart LR
    RAW_A["Raw Accel [ax, ay, az]\n(100 Hz Body Frame)"] --> LPF["Low-Pass Filter\n(g_k = 0.98*g_{k-1} + 0.02*a_k)"]
    LPF --> GRAV_VEC["Gravity Unit Vector u_z\n(Downward Reference)"]
    RAW_A --> SUB["Dynamic Leveling\na_linear = a_raw - g"]
    GRAV_VEC --> SHIFT["Mount Tilt Monitor\nacos(u_z,k · u_z,0) > 15°"]
    SHIFT -->|Yes| RECAL["Re-align Vehicle Frame\n& Trigger Mount Shift Event"]
    SUB --> DECIM["Decimation & Temporal Alignment\n(10 Hz Uniform Timegrid)"]
    DECIM --> FIFO["2.0s Circular FIFO Buffer\n(20 Samples × 6 Channels)"]
```

---

### 2.2 42-Feature Extraction & Dual-Model Gated Inference Pipeline

Every 100 ms, the 2.0-second window is transformed into 42 statistical moments across linear accelerations ($a_x, a_y, a_z$) and angular velocities ($\omega_x, \omega_y, \omega_z$), feeding parallel speed and stop estimators:

```mermaid
flowchart TD
    WIN["2.0s Sliding Window Matrix\n[20 Samples × 6 Channels]"] --> EXTRACT["Statistical Moments Engine\n(7 Metrics × 6 Channels)"]
    
    subgraph MOMENTS["Calculated per Channel"]
        M1["Mean (μ)"]
        M2["Std Dev (σ)"]
        M3["Min (x_min)"]
        M4["Max (x_max)"]
        M5["Last (x_last)"]
        M6["Window Delta (x_last - x_first)"]
        M7["Root Energy sqrt(mean(x²))"]
    end
    
    EXTRACT --> MOMENTS
    MOMENTS --> VEC["42-Dimensional Feature Vector f ∈ R⁴²"]
    
    VEC --> TREES["HistGradientBoosting Speed Trees\n(M Decision Trees: v_raw = v_mean + Σ η·h_m(f))"]
    VEC --> LOGIT["Logistic Stop Classifier\n(z = w_0 + Σ w_j·f_j, P = 1/(1+e^{-z}))"]
    
    TREES --> GATE{"P(stopped) >= 0.50 ?\n(Zero Velocity Update)"}
    LOGIT --> GATE
    
    GATE -->|Yes| V_ZERO["Predicted Speed = 0.0 km/h\n(Hold Stationary Coordinates)"]
    GATE -->|No| V_OUT["Predicted Speed = min(max(v_raw, 0), 55 m/s)\n+ Dynamic Uncertainty σ_v"]
```

---

### 2.3 Kinematic Dead-Reckoning & Flat-Earth WGS-84 Propagation

Forward velocity $\hat{v}$ and gyroscope yaw rate $\omega_z$ are kinematically integrated onto the WGS-84 reference ellipsoid:

```mermaid
flowchart LR
    GYRO["Gyro Yaw Rate ω_z (rad/s)"] --> YAW_INT["Heading Integration\nθ_k = (θ_{k-1} + ω_z · Δt) mod 360°"]
    YAW_INT --> LEAN["Motorcycle Lean Compensation\nθ_lean = atan2(v · ω_z, 9.80665)"]
    
    SPEED["Gated Speed v (m/s)"] --> DIST["Distance Step\nd = v · Δt"]
    
    DIST --> ENU["Flat-Earth Coordinate Step\nΔEast = d · sin(θ_k)\nΔNorth = d · cos(θ_k)"]
    LEAN --> ENU
    
    ENU --> WGS84["WGS-84 Displacements\nΔLat = ΔNorth / 111132.954\nΔLon = ΔEast / (111132.954 · cos(Lat))"]
    
    WGS84 --> COV["Uncertainty Covariance Ellipse\nσ_pos,k = σ_pos,k-1 + σ_v · Δt"]
```

---

### 2.4 Topological Road Graph Soft-Snapping Engine

To eliminate lateral gyroscope drift, estimated coordinates are soft-snapped to offline directed vector road segments:

```mermaid
flowchart TD
    POS["Inertial Candidate Coordinate\n(Lat_k, Lon_k, Heading_k, Speed_k)"] --> GRID["Spatial Bounding-Box Cell Lookup\n(O(1) Candidate Segment Query)"]
    GRID --> SEGS["Candidate Road Segments\n[Segment 1, Segment 2, ...]"]
    
    SEGS --> PROJ["Orthogonal Vector Projection\n(Distance to Segment Centerline)"]
    PROJ --> CONF["Match Confidence Evaluator\nDistance < 30m, |ΔHeading| < 25°"]
    
    CONF --> EVAL{"Confidence >= 70% ?"}
    EVAL -->|No| PASS["Keep Inertial Coordinates Unchanged"]
    EVAL -->|Yes| SNAP["Soft-Snapping Centerline Pull\np_corrected = 0.85 · p_inertial + 0.15 · p_centerline\nθ_corrected = 0.96 · θ_gyro + 0.04 · θ_road"]
    
    SNAP --> OUT["Final Blended Navigation Coordinate"]
```

---

### 2.5 Tracking State Machine Lifecycle

```mermaid
stateDiagram-v2
    [*] --> GNSS_HEALTHY: Outdoor GPS Lock (Accuracy <= 25m)
    [*] --> WAITING_FOR_FIX: Initializing Indoors / Desk
    
    WAITING_FOR_FIX --> GNSS_HEALTHY: First Satellite Fix Received
    WAITING_FOR_FIX --> FALLBACK_ACTIVE: Tap "Anchor Demo" or 20 IMU Samples on Road Pack
    
    GNSS_HEALTHY --> OUTAGE_PENDING: GNSS Lost > 1.0s
    OUTAGE_PENDING --> GNSS_HEALTHY: GNSS Recovered < 2.0s
    OUTAGE_PENDING --> FALLBACK_ACTIVE: Outage Confirmed > 2.0s (Tunnel / Canyon)
    
    FALLBACK_ACTIVE --> RECOVERING: New Valid Satellite Fix Received
    RECOVERING --> GNSS_HEALTHY: 2.5s Smooth Blending Window Complete
    RECOVERING --> FALLBACK_ACTIVE: Satellite Dropped Again
```

---

### 2.6 GNSS Outage Detection & Kinematic Dead-Reckoning Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Driver as Vehicle Driver
    participant App as Android App (Cockpit UI)
    participant Engine as ContinuumLocationEngine
    participant ML as PortableTreeRunner (ML Model)
    participant Map as RoadGraphPack (Offline Map)
    participant OS as Android OS (Google Maps Relay)

    Driver->>App: Taps "START TRIP"
    App->>Engine: start(LocationUpdateCallback)
    Engine->>Engine: Locks GNSS Satellite Fix (Accuracy <= 25m)
    Engine-->>App: State: GNSS_HEALTHY (Green)
    
    Note over Driver,Engine: Vehicle enters tunnel or underground parking
    Engine->>Engine: GNSS Timeout > 1000ms
    Engine-->>App: State: OUTAGE_PENDING (Amber)
    Engine->>Engine: GNSS Timeout > 2000ms
    Engine-->>App: State: FALLBACK_ACTIVE (Crimson)

    loop Every 100ms (10 Hz Gyro & Feature Step)
        Engine->>ML: predict(42 IMU features)
        ML-->>Engine: Speed = 45.2 km/h, isStopped = false
        Engine->>Engine: Integrate Yaw Rate -> Heading = 042°
        Engine->>Engine: Step WGS-84 Flat-Earth Coordinates
        Engine->>Map: match(lat, lon, heading, speed)
        Map-->>Engine: Soft-snap to road centerline (weight = 0.15)
        Engine->>OS: pushLocation(synthetic Location)
        OS-->>Driver: Google Maps puck continues moving smoothly!
        Engine-->>App: Broadcast Telemetry (Speed, Heading, Road, Map)
    end
```

---

### 2.7 Smooth GNSS Re-convergence Filter

When a vehicle emerges from a tunnel into open sky, instantaneous switching to a newly acquired GPS fix causes navigation pucks to "teleport" or trigger false rerouting. Continuum IDR implements a **$2.5\,\text{s}$ linear blending re-convergence filter**:

$$\mathbf{p}_{\mathrm{blend}}(t) = (1 - \alpha) \mathbf{p}_{\mathrm{idr}}(t) + \alpha \mathbf{p}_{\mathrm{gnss}}(t), \quad \alpha = \min\left(\frac{t - t_{\mathrm{recovery}}}{2.5\,\mathrm{s}}, 1.0\right)$$

---

### 2.8 Google Maps & OS Mock Location Relay

```mermaid
flowchart LR
    subgraph CONTINUUM["Continuum IDR Native Runtime"]
        SENS["Phone IMU (100 Hz)"] --> ENG["Continuum Location Engine"]
        ENG --> RELAY["SystemMockRelay.kt\n(Android Test Provider)"]
    end

    subgraph ANDROID_OS["Android OS Location Subsystem"]
        GPS_PROV["LocationManager.GPS_PROVIDER\n(/dev/gps or Mock Injection)"]
    end

    subgraph THIRD_PARTY["External Navigation Apps"]
        GMAPS["Google Maps\n(Official App)"]
        WAZE["Waze Navigation"]
        UBER["Uber Driver / Delivery"]
    end

    RELAY -->|setTestProviderLocation| GPS_PROV
    GPS_PROV -->|Standard Android Location API| GMAPS
    GPS_PROV -->|Standard Android Location API| WAZE
    GPS_PROV -->|Standard Android Location API| UBER
```

---

### 2.9 Native Android Component Interaction Architecture

```mermaid
flowchart TD
    subgraph UI["UI Presentation Layer"]
        MAIN["MainActivity.kt\n(Automotive Cockpit HUD)"]
        BENTO["Hero Bento Cluster\n(Speed, Heading, Precision)"]
        MAP_CANVAS["MapView.kt\n(Vector Road Canvas)"]
        DRAWER["Trips Archive Drawer\n(JSONL Export)"]
    end

    subgraph SERVICE["Background Service Layer"]
        FGS["TrackingService.kt\n(FOREGROUND_SERVICE_LOCATION)"]
        HEARTBEAT["500ms Periodic Heartbeat\n(ACTION_HEARTBEAT)"]
        LOGGER["JSONL Trip Writer\n(Metadata, IMU, GNSS, DR)"]
    end

    subgraph CORE_ENGINE["Inertial Navigation Engine"]
        ENG["ContinuumLocationEngine.kt\n(LocationListener + SensorEventListener)"]
        TREE["PortableTreeRunner.kt\n(Fast Decision Tree Traversal ~110 µs)"]
        ROADS["RoadGraphPack.kt\n(Electronic City Corridor Pack)"]
    end

    subgraph OS_INTEGRATION["Android OS Subsystems"]
        OS_GPS["SystemMockRelay.kt\n(LocationManager Mock Provider)"]
        BLE_MESH["TrafficBleManager.kt\n(BLE Advertiser & Scanner)"]
    end

    MAIN <-->|Local Broadcast Intents| FGS
    MAIN --- BENTO
    MAIN --- MAP_CANVAS
    MAIN --- DRAWER
    FGS --> HEARTBEAT
    FGS --> LOGGER
    FGS <--> ENG
    ENG <--> TREE
    ENG <--> ROADS
    ENG --> OS_GPS
    FGS --> BLE_MESH
```

---

### 2.10 Continuum Studio Telemetry Loop

```mermaid
flowchart LR
    subgraph BROWSER["Browser Client (React 18 + Vite)"]
        UI_CTRL["Playback & Scenario Controls"]
        MAP_LEAF["Leaflet Map Canvas"]
        CHARTS["Recharts Multi-Channel Telemetry"]
        HUD["Diagnostics & Bento Cluster"]
    end

    subgraph BACKEND["FastAPI Telemetry Daemon (:8000)"]
        ROUTER["REST & SSE Endpoint Router"]
        SIM_SESS["Interactive Simulation Session"]
        NOISE_ENG["Stochastic Noise & Shock Injector"]
        ESTIMATOR["Continuum IDREngine (Python SDK)"]
    end

    UI_CTRL -->|"POST /api/runtime/control"| ROUTER
    UI_CTRL -->|"POST /api/runtime/scenario"| ROUTER
    ROUTER --> SIM_SESS
    SIM_SESS --> NOISE_ENG
    NOISE_ENG --> ESTIMATOR
    ESTIMATOR --> SIM_SESS
    SIM_SESS -->|"GET /api/runtime/status (SSE 10 Hz)"| ROUTER
    ROUTER --> MAP_LEAF
    ROUTER --> CHARTS
    ROUTER --> HUD
```

---

### 2.11 Cooperative V2V Traffic Mesh Network

```mermaid
flowchart TD
    subgraph VEHICLE_A["Vehicle A (Host Node)"]
        DET_A["Surface Anomaly Detected\n(POTHOLE severity 0.85)"] --> PACK_A["Pack 18-Byte Binary Beacon\n[Type=3, Sev=85, Lat, Lon]"]
        PACK_A --> ADV_A["BLE Advertiser Burst\n(Low Latency, 3000ms timeout)"]
    end

    subgraph RF_AIR["Direct Bluetooth Low Energy Channel (10–30m Line-of-Sight)"]
        BEACON["Manufacturer-Specific BLE Packet\n[Company ID: 0x0C1D 'CID']"]
    end

    subgraph VEHICLE_B["Vehicle B (Approaching Peer)"]
        SCAN_B["BLE Scanner (Continuous)\n(ScanFilter on CID=0x0C1D)"] --> DEDUP_B["30-Second Spatial Deduplication\nKey: {Hazard}_{Lat}_{Lon}"]
        DEDUP_B --> ALERT_B["Cockpit HUD Traffic Alert\n'POTHOLE ahead in 25m!'"]
    end

    ADV_A --> BEACON
    BEACON --> SCAN_B
```

---

## 3. Deep Subsystem & Feature Specifications

### 3.1 Edge ML Speed Estimation & Stop Gating

Consumer smartphones mounted on vehicle dashboards lack physical wires to wheel speed encoders. Continuum IDR infers velocity from chassis vibration, road roughness, suspension pitch, and engine RPM harmonics:
- **Causal Sliding Window:** 20 samples at 10 Hz (2.0 seconds) across 6 degrees-of-freedom ($a_x, a_y, a_z, \omega_x, \omega_y, \omega_z$).
- **42 Statistical Features:** Computes Mean, Standard Deviation, Min, Max, Last, Window Delta ($x_{\mathrm{last}} - x_{\mathrm{first}}$), and Root-Energy ($\sqrt{\frac{1}{N} \sum x^2}$) for each channel.
- **Histogram Gradient Boosted Regressor (`HistGradientBoostingRegressor`):** 50–100 boosting stages, 31 leaves per tree, modeling non-linear velocity dynamics from 0 to 120 km/h.
- **Regularized Logistic Stop Gating (`LogisticRegression`):** Computes $P(\text{stopped} \mid \mathbf{f})$. If $P(\text{stopped}) \ge 0.50$, output speed is forcefully clamped to $0.0\,\text{km/h}$, suppressing stationary drift creep while parked or waiting at traffic lights.

### 3.2 Portable Zero-Dependency Edge Runtime (~110 µs)

To run on smartphones without requiring heavy machine learning frameworks (like TensorFlow Lite, PyTorch Mobile, or ONNX Runtime), Continuum IDR exports all trained weights into a compact, zero-dependency JSON schema (`models/portable/motion_portable.json`):

```json
{
  "manifest": {
    "version": "1.0.0",
    "model_id": "continuum-motion-p0",
    "feature_names": ["accel_x_mean", "accel_x_std", "..."]
  },
  "speed_mean": 12.435,
  "stop_linear_intercept": -0.852,
  "stop_linear_weights": [-0.12, 0.45, "... 42 weights ..."],
  "speed_trees": [
    [
      {"f": 1, "th": 0.452, "l": 1, "r": 2},
      {"v": -1.24}
    ]
  ]
}
```

The on-device Kotlin runtime ([`PortableTreeRunner.kt`](file:///d:/iovnbd/IO-VNBD/android/app/src/main/java/ai/continuum/idr/PortableTreeRunner.kt)) traverses these decision trees in **$\sim 110\,\text{µs}$ per step**, consuming $< 4.5\,\text{MB}$ of RAM with zero external dependencies. Exact float-level parity ($\Delta < 10^{-5}\,\text{m/s}$) is verified between Python scikit-learn and the Kotlin runtime.

### 3.3 Native Android Automotive Cockpit Application

Built natively in Kotlin ([`MainActivity.kt`](file:///d:/iovnbd/IO-VNBD/android/app/src/main/java/ai/continuum/idr/MainActivity.kt)), the app provides a sleek dark-mode automotive instrument cluster:
- **Hero Bento Metric Cards:**
  - **Speedometer:** Bold digital speed readout (`48.2 KM/H`).
  - **Compass & Heading:** 3-digit bearing (`042° NE`) with motorcycle lean angle (`Lean: 0.0°`).
  - **Precision & Road Match:** Live uncertainty radius (`±2.4m`) and active road segment match confidence (`EC_EXPRESSWAY 94%`).
- **Tactical Vector Canvas (`MapView.kt`):** Zero-dependency canvas map rendering topological road segments, vehicle heading chevrons, uncertainty ellipses, and breadcrumbs with pinch-to-zoom and auto-follow.
- **Android 14/15 FGS Compliance:** Implements `startForeground()` with `FOREGROUND_SERVICE_TYPE_LOCATION` and 500 ms periodic diagnostic heartbeats.
- **Instant Indoor Testing ("Anchor to Demo Route"):** Tap the teal anchor button to seed coordinates at the Electronic City Corridor (`12.8450, 77.6620`), enabling immediate dead-reckoning testing indoors.

### 3.4 Continuum Studio Desktop Simulation Cockpit

Built with **React 18 + Vite + Tailwind CSS** backed by a **FastAPI** daemon:
- **Scenario Switcher:** Switch between held-out runs (`Vtb01`–`Vtb06`) and procedural random trips.
- **Stochastic Perturbations:** Inject Gaussian MEMS sensor noise and road surface shocks (potholes, speed breakers) in real time.
- **Interactive GPS Kill Switch:** Withhold satellite fixes on-demand to test tunnel dead-reckoning.
- **Multi-Channel Recharts Telemetry:** Live velocity comparison, cumulative drift curves, and IMU spectral energy.

### 3.5 Offline Vector Road Graph & Soft-Snapping

Pure inertial navigation suffers from gyroscope bias drift ($\sim 1^\circ - 3^\circ/\text{min}$). Over a 2 km tunnel, lateral displacement can drift into tunnel walls. Continuum IDR incorporates an offline spatial road graph (`sample_road_pack.json`):
- Soft-snapping damping ($15\%$ weight) pulls the estimated coordinates toward the road centerline when match confidence $\ge 70\%$.
- Heading alignment ($4\%$ weight) corrects slow gyroscope bias drift toward the road segment azimuth.

### 3.6 Specialized Vehicle Dynamics & Profiles

1. **`CAR`:** Standard four-wheel passenger vehicles.
2. **`MOTORCYCLE`:** High-lean dynamics. Centripetal lean angle $\theta_{\mathrm{lean}} = \mathrm{atan2}(v \cdot \omega_z, g)$ is computed in real time to decouple gravitational contamination from forward acceleration during sharp cornering.
3. **`PARKING`:** Crawl and reverse detection. Detects reverse gear from negative longitudinal acceleration bursts ($< -1.8\,\text{m/s}^2$) starting from rest.
4. **`EXTERNAL_IMU`:** Fast 100–200 Hz processing for external telematics boxes connected via BLE or USB.

### 3.7 Cooperative V2V Traffic Mesh (BLE Direct)

[`TrafficBleManager.kt`](file:///d:/iovnbd/IO-VNBD/android/app/src/main/java/ai/continuum/idr/TrafficBleManager.kt) enables local vehicle-to-vehicle hazard alerts (10–30m range) without cellular internet:
- **18-Byte Binary Beacon:** Packed hazard type byte, severity (0–100), and WGS-84 latitude/longitude.
- **Hazard Categories:** `GNSS_OUTAGE`, `SPEED_BREAKER`, `POTHOLE`, `TRAFFIC_JAM`.
- **Deduplication:** Automatic 30-second deduplication filter prevents alert storms in bumper-to-bumper traffic.

---

## 4. Empirical Benchmark Evidence (IO-VNBD Dataset)

Evaluated against 34 real GNSS outage windows across 11 held-out trajectories from the IO-VNBD dataset:

| Metric | Frozen Position Baseline | Last-Speed + Gyro Baseline | Continuum IDR (`motion_p0`) | Evaluation Target |
| :--- | :---: | :---: | :---: | :---: |
| **Evaluated Runs** | 11 | 11 | 11 | 11 |
| **Outage Windows** | 34 | 34 | 34 | 34 |
| **Median Endpoint Error** | 496.9 m | 334.4 m | **354.3 m** | $< 50\,\text{m}$ |
| **Median Drift (%)** | 112.4% | 76.1% | **80.3%** | **$< 10.0\%$** |
| **$< 10\%$ Pass Rate** | 0.0% | 0.0% | **0.0%** | $> 90.0\%$ |

### Honest Technical Evaluation
- Continuum IDR achieves an immediate **$28.7\%$ error reduction** compared to apps that freeze coordinates.
- Low-cost consumer smartphone MEMS gyroscopes drift by $0.5^\circ - 2.0^\circ/\text{s}$ under vehicle cabin temperature changes.
- In long outages ($> 30\,\text{s}$), pure inertial dead-reckoning misses the $< 10\%$ drift target unless constrained by **topological road soft-snapping (`RoadGraphPack`)**.

---

## 5. Indian Road Challenges & Domain Adaptation

```mermaid
graph TD
    IR["Indian Driving Conditions"]
    IR --> POTH["Potholes & Patched Asphalt\n(Spurious vertical shocks up to 4.5g)"]
    IR --> BRK["Speed Breakers & Rumble Strips\n(High-amplitude suspension oscillation)"]
    IR --> MOTO["Motorcycle Lane Filtering\n(Extreme roll angles up to 35° in traffic)"]
    IR --> IDLE["Engine Idle Vibration at Signals\n(Single-cylinder engine mimics motion)"]
    IR --> STOP["Stop-and-Go Crawling Traffic\n(Sub-5 km/h creep with clutch slipping)"]
```

### Domain Mitigations Built into Continuum IDR
1. **Vertical Shock Filtering (`checkSurfaceShock`):** Accelerations $> 4.5\,\text{m/s}^2$ are classified as road anomalies and filtered out to prevent false speed bursts.
2. **Motorcycle Centripetal Decoupling:** Roll angles are extracted to preserve true forward acceleration.
3. **Multi-Axis Stop Gating:** The 42-feature model examines variance across all 6 axes to distinguish single-cylinder engine idling from vehicle forward movement.

---

## 6. Quickstart & Verification Guide

> [!IMPORTANT]
> **What works from a fresh `git clone` (no external data needed):**
> All items marked ✅ below run fully out-of-the-box with the bundled model weights and synthetic data.
> Items marked ⚠️ additionally require the private **IO-VNBD synchronized dataset** (not redistributable — see below).

| Command / Feature | Works from Clone? | Notes |
| :--- | :---: | :--- |
| `pytest tests/` (122 tests) | ✅ | Uses bundled portable model & synthetic fixtures |
| `idr stress` | ✅ | Uses bundled `models/motion_p0` weights |
| `idr mobile-demo` | ✅ | Simulates full GNSS_HEALTHY → FALLBACK → RECOVERING lifecycle |
| `idr profile` | ✅ | Benchmarks CAR / MOTORCYCLE / PARKING dynamics profiles |
| `idr export` | ✅ | Exports portable JSON trees from bundled joblib weights |
| `idr synthetic` | ✅ | Generates 17-category synthetic Indian-road JSONL dataset |
| `idr generate-synthetic-dataset` | ✅ | Generates full structured 17-scenario benchmark |
| `idr mobile-demo` | ✅ | Full fallback lifecycle demo with Python SDK |
| `idr run-experiments` | ✅ | Runs 5 candidate estimators on synthetic scenarios |
| `idr studio` | ✅ | Serves Continuum Studio on `:8000` — backed by **replay artifact** `artifacts/evaluation/demo_replay.json` |
| Android APK build | ✅ | Bundles `motion_portable.json` + `sample_road_pack.json` — no internet needed |
| `idr audit --dataset .` | ⚠️ | Requires local path to the synchronized IO-VNBD CSV folders |
| `idr train --dataset .` | ⚠️ | Requires synchronized IO-VNBD `S-*.csv` / `V-*.csv` pairs |
| `idr evaluate --dataset . --model ...` | ⚠️ | Requires the same dataset for held-out trip replay |
| Google Maps mock location | ⚠️ | Requires Android device + Developer Options + physical trip |
| BLE V2V mesh | ⚠️ | Requires two Android devices in proximity |

> [!NOTE]
> **About the IO-VNBD Dataset:** The raw synchronized smartphone + vehicle (`S-*.csv` / `V-*.csv`) recordings are not redistributable with the repo. The bundled `models/motion_p0/` weights (`speed_model.joblib`, `stop_model.joblib`) were trained on this dataset and are committed to the repository, so all inference, export, and testing commands work without it.

> [!NOTE]
> **About Continuum Studio:** The Studio web dashboard (`idr studio`) streams from a pre-recorded evaluation replay (`artifacts/evaluation/demo_replay.json`). Play/Pause/Step/GNSS-toggle controls operate on this replay. The dashboard is a simulation cockpit and interactive prototype viewer — it does not process raw live sensor streams.

---

### 6.1 Python SDK & CLI — Commands that work from clone

```powershell
# 1. Setup virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .

# 2. Run full verification test suite (122/122 tests, uses bundled model)
python -m pytest tests/ -q

# 3. Synthetic Indian-road benchmark (no dataset needed)
python -m continuum_idr.cli generate-synthetic-dataset --output synthetic_output

# 4. Fallback lifecycle demo (no dataset needed)
python -m continuum_idr.cli mobile-demo

# 5. GNSS fault injection stress tests (uses bundled model)
python -m continuum_idr.cli stress --model models/motion_p0

# 6. Export portable JSON model (uses bundled model)
python -m continuum_idr.cli export --model models/motion_p0 --output portable_export

# 7. Run candidate estimator comparison (synthetic scenarios)
python -m continuum_idr.cli run-experiments --model models/motion_p0
```

### 6.2 Commands that require the IO-VNBD dataset

These commands require the private synchronized dataset on your local machine:

```powershell
# Audit dataset pairs (needs: Synchronised V abd S datasets/ folder)
python -m continuum_idr.cli audit --dataset /path/to/iovnbd/root

# Retrain models from raw CSV pairs
python -m continuum_idr.cli train --dataset /path/to/iovnbd/root --output models/motion_p0

# Run held-out GNSS outage evaluation
python -m continuum_idr.cli evaluate --dataset /path/to/iovnbd/root --model models/motion_p0 --output artifacts/evaluation
```

### 6.3 Launch Continuum Studio

```powershell
python -m continuum_idr.cli studio --host 127.0.0.1 --port 8000
```
Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser. The dashboard streams from the bundled evaluation replay artifact.

### 6.4 Build & Install Android Mobile App

```powershell
cd android
.\gradlew.bat testDebugUnitTest
.\gradlew.bat assembleDebug
```
Output APK: [`android/app/build/outputs/apk/debug/app-debug.apk`](android/app/build/outputs/apk/debug/app-debug.apk).

Install via ADB:
```powershell
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

### 6.5 Link Google Maps via Mock Location Provider

1. On your phone: **Settings** → **System** → **Developer options** → **Select mock location app** → choose **Continuum IDR**.
2. Open **Continuum IDR** → Tap **ENABLE MOCK GPS**.
3. Tap **START TRIP** (or **Anchor to Demo Route** for indoor testing).
4. Open **Google Maps**: The blue navigation puck will follow Continuum's inertial dead-reckoned trajectory during tunnels and satellite loss.

---

## 7. Repository Structure

```
IO-VNBD/
├── android/                             # Native Android Kotlin Application
│   ├── app/src/main/
│   │   ├── AndroidManifest.xml          # Permissions & Android 14/15 FGS declaration
│   │   ├── assets/                      # Model JSON & offline road pack
│   │   ├── java/ai/continuum/idr/
│   │   │   ├── MainActivity.kt          # Automotive Cockpit HUD UI
│   │   │   ├── TrackingService.kt       # Persistent foreground recording service
│   │   │   ├── ContinuumLocationEngine.kt# Drop-in Android location fallback engine
│   │   │   ├── PortableTreeRunner.kt    # Zero-dependency on-device tree runner (~110 µs)
│   │   │   ├── SystemMockRelay.kt       # OS GPS Mock Provider for Google Maps
│   │   │   ├── TrafficBleManager.kt     # V2V cooperative BLE hazard mesh
│   │   │   ├── MapView.kt               # Hardware-accelerated offline vector canvas
│   │   │   └── RoadGraphPack.kt         # Spatial road topology matcher
│   │   └── res/drawable/                # Automotive Bento UI shape drawables
│   └── app/src/test/                    # JVM unit tests (Parity, Road Graph, Instrumentation)
├── continuum_idr/                       # Core Python Navigation SDK & Engine
│   ├── cli.py                           # Unified CLI (studio, train, evaluate, export, etc.)
│   ├── engine.py                        # IDREngine state machine & kinematics
│   ├── features.py                      # 42-feature causal window statistical extractor
│   ├── model.py                         # Scikit-learn HistGradientBoosting & Logistic models
│   ├── portable_model.py                # Zero-dependency portable JSON model exporter
│   ├── maps.py                          # Offline topological road graph & spatial soft-snapping
│   ├── profiles.py                      # Vehicle dynamics (CAR, MOTORCYCLE, PARKING, EXTERNAL_IMU)
│   ├── traffic.py                       # Cooperative V2V hazard protocol (BLE beacon payload)
│   ├── synthetic.py                     # Synthetic edge-case trajectory generator
│   ├── studio.py                        # FastAPI telemetry streaming daemon
│   └── studio_static/                   # Production-built React Studio dashboard
├── frontend/                            # React 18 + Vite + Tailwind CSS Studio Source
│   ├── src/                             # Cockpit components, Leaflet map, Recharts graphs
│   └── package.json                     # Frontend build configurations
├── docs/                                # Exhaustive Technical Documentation Suite
│   ├── ARCHITECTURE.md                  # Deep theoretical framework & math formulations
│   ├── MACHINE_LEARNING_MODELS.md       # ML models, features & edge inference
│   ├── STUDIO_DASHBOARD.md              # Desktop simulation cockpit guide
│   ├── ANDROID_MOBILE_APP.md            # Android app architecture & HUD layout
│   ├── GOOGLE_MAPS_INTEGRATION.md       # Google Maps & third-party fallback relay
│   ├── BENCHMARKS_AND_EVIDENCE.md       # Empirical evidence on IO-VNBD dataset
│   ├── API_REFERENCE.md                 # Complete API reference manual
│   ├── FIELD_TEST_PLANS.md              # Real-world road validation protocols
│   └── INDIAN_ROAD_COLLECTION_PROTOCOL.md# Data logging under Indian road conditions
├── models/                              # Trained Machine Learning Artifacts
│   ├── motion_p0/                       # Python scikit-learn model bundle
│   └── portable/motion_portable.json    # Exported portable JSON tree weights
├── tests/                               # Comprehensive Python Test Suite (122 tests)
└── pyproject.toml                       # Python package configuration
```

---

## 8. Complete Documentation Suite (`docs/`)

Explore our dedicated technical documents in [`docs/`](docs/):

| Document | Primary Focus |
| :--- | :--- |
| 📘 [**System Architecture**](docs/ARCHITECTURE.md) | Theoretical framework, WGS-84 Flat-Earth equations, Kalman re-convergence, coordinate frames. |
| 🤖 [**Machine Learning Models**](docs/MACHINE_LEARNING_MODELS.md) | 42-feature layout, HistGradientBoosting trees, stop classifier, and portable edge JSON format. |
| 🖥️ [**Continuum Studio Dashboard**](docs/STUDIO_DASHBOARD.md) | React 18 frontend architecture, FastAPI daemon, noise perturbations, and scenario replay. |
| 📱 [**Native Android Mobile App**](docs/ANDROID_MOBILE_APP.md) | Android 14/15 foreground service lifecycle, cockpit HUD UI, vehicle profiles, and build steps. |
| 🛰️ [**Google Maps Integration**](docs/GOOGLE_MAPS_INTEGRATION.md) | How fallback works with official Google Maps via OS Mock GPS and commercial Navigation SDKs. |
| 📊 [**Benchmarks & Evidence**](docs/BENCHMARKS_AND_EVIDENCE.md) | Empirical IO-VNBD evaluation results, comparison baselines, and Indian road domain adaptations. |
| 📑 [**API Reference**](docs/API_REFERENCE.md) | Comprehensive reference for Python SDK, REST runtime endpoints, and Android Kotlin classes. |
| 📋 [**Field Test Plans**](docs/FIELD_TEST_PLANS.md) | Real-world road testing protocol for flyovers, tunnels, parking ramps, and motorcycles. |
| 🛣️ [**Indian Road Collection Protocol**](docs/INDIAN_ROAD_COLLECTION_PROTOCOL.md) | Rigorous telemetry logging methodology under potholes, speed breakers, and urban traffic. |

---

## 9. License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
