# Continuum IDR — Comprehensive System Architecture & Engineering Specification

**Continuum IDR** (**Inertial Dead Reckoning**) is an autonomous navigation fallback system, research SDK, and edge-native automotive application designed to sustain high-precision vehicular positioning during complete GNSS (GPS, NavIC, Galileo, GLONASS) satellite blackouts.

It operates entirely on edge hardware (smartphones, vehicle telematics, and in-dash automotive head units) without requiring external wheel odometry, OBD-II cables, or active cellular connectivity.

---

## Table of Contents

1. [High-Level System Topology](#1-high-level-system-topology)
2. [Coordinate Frames & Geodetic Standards](#2-coordinate-frames--geodetic-standards)
3. [Sensor Ingestion & Dynamic Mount Leveling Pipeline](#3-sensor-ingestion--dynamic-mount-leveling-pipeline)
4. [42-Feature Extraction & Machine Learning Speed Estimator](#4-42-feature-extraction--machine-learning-speed-estimator)
5. [Kinematic Dead-Reckoning & Coordinate Propagation](#5-kinematic-dead-reckoning--coordinate-propagation)
6. [Topological Road Graph Soft-Snapping Engine](#6-topological-road-graph-soft-snapping-engine)
7. [Finite State Machine (Tracking State Lifecycle)](#7-finite-state-machine-tracking-state-lifecycle)
8. [GNSS Outage Detection & Fallback Execution Sequence](#8-gnss-outage-detection--fallback-execution-sequence)
9. [Re-Convergence & Smooth Handoff Filter](#9-re-convergence--smooth-handoff-filter)
10. [Google Maps & OS Mock Location Relay Architecture](#10-google-maps--os-mock-location-relay-architecture)
11. [Native Android Component Interaction & Threading Model](#11-native-android-component-interaction--threading-model)
12. [Continuum Studio Telemetry Architecture](#12-continuum-studio-telemetry-architecture)
13. [Cooperative V2V Traffic Mesh Network Architecture](#13-cooperative-v2v-traffic-mesh-network-architecture)
14. [Edge Performance Budgets & Fault Tolerance](#14-edge-performance-budgets--fault-tolerance)

---

## 1. High-Level System Topology

Continuum IDR is partitioned into three decoupled execution environments:
1. **The Core Python Navigation SDK & ML Engine** (`continuum_idr/`): Offline model training, synthetic scenario synthesis, trajectory evaluation, and cross-platform verification.
2. **The High-Performance Edge Runtime (Android Kotlin Engine)** (`android/`): Native Android background service executing zero-dependency decision trees in ~110 µs, feeding the OS Mock Location Provider.
3. **The Web Telemetry & Evaluation Cockpit (Continuum Studio)** (`continuum_idr/studio/`): React 18 / Vite cockpit communicating via SSE with FastAPI for real-time telemetry replay and interactive edge stress testing.

```mermaid
flowchart TD
    subgraph SENSORS["Edge Sensing Layer (Smartphone / Telematics)"]
        IMU["3-Axis Accelerometer + 3-Axis Gyroscope\n(50–100 Hz Continuous Stream)"]
        GNSS["GNSS / GPS Receiver\n(1 Hz Satellite Fixes)"]
    end

    subgraph PREPROC["Preprocessing & Alignment Engine"]
        GRAV["Gravity Estimator & Mount Normalization\n(Tilt Alignment & Dynamic Leveling)"]
        WIN["2.0s Causal Sliding Window\n(20 Samples @ 10 Hz Decimated)"]
        ZUPT["Zero Velocity Update (ZUPT)\n(Energy & Variance Detector)"]
    end

    subgraph INFERENCE["Edge Inference Pipeline (~110 µs)"]
        FEAT["42 Motion Features Extractor\n(Mean, Std, Min, Max, Energy, Deltas)"]
        TREES["HistGradientBoosting Speed Regressor\n(Portable Decision Trees)"]
        STOP["Logistic Regression Stop Classifier\n(Binary Motion Gating P >= 0.50)"]
    end

    subgraph NAVIGATION["Kinematic Dead-Reckoning Engine"]
        YAW["Gyroscope Yaw Rate Integration\n(Heading Propagation with Motorcycle Lean)"]
        FLAT["Flat-Earth WGS-84 Coordinate Step\n(Distance & Azimuth to Delta Lat/Lon)"]
        UNCERT["Uncertainty Covariance Propagation\n(Dynamic Speed-Dependent Error Ellipse)"]
    end

    subgraph CORRECTION["Map & Topological Correction"]
        ROAD["Offline Vector Road Graph\n(Topological Directed Segments)"]
        MATCH["Spatial Soft-Snapping Engine\n(Heading & Lateral Centerline Pull)"]
    end

    subgraph OUTPUTS["Ecosystem Integration & Fallback Delivery"]
        STUDIO["Continuum Studio\n(Desktop Simulation Cockpit)"]
        ANDROID_UI["Native Android HUD\n(Automotive Bento Cluster)"]
        MOCK_GPS["Android OS GPS Mock Provider\n(Feeds Google Maps / Waze / Uber)"]
        BLE["V2V Mesh Transport\n(BLE Local Hazard Broadcast)"]
    end

    SENSORS --> PREPROC
    PREPROC --> INFERENCE
    INFERENCE --> NAVIGATION
    NAVIGATION --> CORRECTION
    CORRECTION --> OUTPUTS
```

---

## 2. Coordinate Frames & Geodetic Standards

Continuum IDR continuously transforms measurements across four spatial reference frames:

1. **Body Frame ($B$):** Fixed to the smartphone or telematics device. $X_B$ points right, $Y_B$ points up along the screen, and $Z_B$ points outward perpendicularly from the display.
2. **Vehicle Nav Frame ($V$):** Forward ($X_V$), Lateral ($Y_V$), and Vertical ($Z_V$). When aligned, $X_V$ represents the vehicle's direction of longitudinal travel.
3. **Local Geodetic Frame ($ENU$):** East-North-Up tangent plane anchored at a local origin $(\phi_0, \lambda_0, h_0)$ on the WGS-84 ellipsoid.
4. **Earth-Centered Earth-Fixed Frame ($ECEF$):** Global Cartesian reference system $(X, Y, Z)$ defined by the WGS-84 standard (semi-major axis $a = 6378137.0\,\mathrm{m}$, flattening $f = 1/298.257223563$).

```mermaid
flowchart LR
    subgraph BF["Body Frame (B)"]
        XB["X_B (Right)"]
        YB["Y_B (Up Screen)"]
        ZB["Z_B (Display Normal)"]
    end

    subgraph VF["Vehicle Frame (V)"]
        XV["X_V (Forward Heading)"]
        YV["Y_V (Lateral Side)"]
        ZV["Z_V (Vertical Up)"]
    end

    subgraph ENU_F["Local Tangent Frame (ENU)"]
        EE["East (Tangent Parallel)"]
        NN["North (Tangent Meridian)"]
        UU["Up (Local Zenith)"]
    end

    subgraph GEO["WGS-84 Geodetic"]
        LAT["Latitude (φ)"]
        LON["Longitude (λ)"]
        ALT["Ellipsoidal Height (h)"]
    end

    BF -->|Dynamic Tilt Alignment R_BV| VF
    VF -->|Yaw Rate Integration θ_k| ENU_F
    ENU_F -->|"Meridional / Parallel Step"| GEO
```

---

## 3. Sensor Ingestion & Dynamic Mount Leveling Pipeline

Consumer devices are mounted at arbitrary pitch, roll, and yaw angles (e.g., windshield suction mounts, dashboard clip cradles, two-wheeler handlebar clamps, or cup holders). The sensor ingestion pipeline isolates forward longitudinal motion from gravity.

```mermaid
flowchart LR
    RAW["Raw Accel [ax, ay, az]\n(100 Hz Body Frame)"] --> LPF["Low-Pass Gravity Filter\ng_k = α·g_{k-1} + (1-α)·a_k\n(α = 0.98)"]
    LPF --> GRAV_UNIT["Gravity Unit Vector u_z\n(Vertical Earth Axis)"]
    RAW --> SUB["Dynamic Leveling\na_linear = a_raw - g"]
    GRAV_UNIT --> SHIFT_DET["Mount Shift Detector\nacos(u_z,k · u_z,0) > 15°"]
    SHIFT_DET -->|Shift Detected| RESET["Trigger Mount Re-alignment\nUpdate Rotation Matrix R_BV"]
    SUB --> DECIM["Decimation & Temporal Resampling\n(Decimate 100 Hz to 10 Hz Timegrid)"]
    DECIM --> BUFFER["Causal Sliding Buffer W ∈ R^{20×6}\n(2.0s Temporal Window)"]
```

### Mathematical Formulation of Dynamic Leveling

1. **Gravity Estimation:**
   $$\mathbf{g}_k = \alpha \mathbf{g}_{k-1} + (1 - \alpha) \mathbf{a}_{\mathrm{raw}, k}$$
   where $\alpha = 0.98$ at 100 Hz yields an effective cut-off frequency of $f_c \approx 0.32\,\mathrm{Hz}$, isolating the stationary gravitational field from vehicle acceleration transients.

2. **Vehicle Vertical Unit Vector:**
   $$\hat{\mathbf{u}}_z = -\frac{\mathbf{g}_k}{\|\mathbf{g}_k\|_2}$$

3. **Mount Shift Detection:**
   $$\Delta \psi = \arccos\left(\hat{\mathbf{u}}_{z, k} \cdot \hat{\mathbf{u}}_{z, 0}\right)$$
   If $\Delta \psi > 15^\circ$, the orientation matrix $\mathbf{R}_{BV}$ is flagged as invalid, and the mount leveling pipeline re-anchors to the new gravity orientation.

---

## 4. 42-Feature Extraction & Machine Learning Speed Estimator

Conventional dead-reckoning attempts to compute speed via double integration of linear accelerometers:
$$v(t) = v_0 + \int_0^t a(t') \, dt', \quad p(t) = p_0 + \int_0^t v(t') \, dt'$$
On consumer MEMS sensors, small sensor biases ($0.05\,\mathrm{m/s}^2$) compound quadratically, producing positional drift errors exceeding 180 meters in under 60 seconds.

Continuum IDR replaces unconstrained double integration with a **causal statistical feature extraction and dual-model machine learning architecture**:

```mermaid
flowchart TD
    WINDOW["2.0s Sliding Window Matrix W ∈ R^{20×6}\n(20 decadal frames × 6 sensor axes)"] --> MOMENTS["Moments Extractor\n(7 statistical metrics per channel)"]

    subgraph METRICS["Statistical Operators"]
        M1["1. Mean (μ)"]
        M2["2. Standard Deviation (σ)"]
        M3["3. Minimum Value (min)"]
        M4["4. Maximum Value (max)"]
        M5["5. Terminal Sample (last)"]
        M6["6. Window Delta (last - first)"]
        M7["7. Root Energy (sqrt(mean(x²)))"]
    end

    MOMENTS --> METRICS
    METRICS --> FVEC["42-Dimensional Feature Vector f ∈ R⁴²"]

    subgraph ML_PIPELINE["Dual-Model Inference Stage (~110 µs)"]
        FVEC --> TREES["Histogram Gradient Boosting Regressor\n(M Decision Trees)\nv_raw = v_base + Σ η·h_m(f)"]
        FVEC --> LOGIT["Regularized Logistic Stop Classifier\nz = w_0 + Σ w_j·f_j\nP(stopped) = 1 / (1 + e^{-z})"]
    end

    TREES --> GATING{"Zero Velocity Gate\nP(stopped) >= 0.50 ?"}
    LOGIT --> GATING

    GATING -->|Stopped| ZERO["Output Speed = 0.00 km/h\n(Prevent Drift Accumulation)"]
    GATING -->|In Motion| SPEED_OUT["Output Speed = clamp(v_raw, 0, 55 m/s)\nPropagate Dynamic Uncertainty σ_v"]
```

### 42-Feature Matrix Breakdown

Across the 6 decimated sensor channels $(a_x, a_y, a_z, \omega_x, \omega_y, \omega_z)$, 7 statistical operators are extracted:

| Feature Index Range | Channel | Statistical Moment Applied | Physical Significance |
| :--- | :--- | :--- | :--- |
| `f[0]` – `f[6]` | $a_x$ (Forward/Lateral Accel) | $\mu, \sigma, \min, \max, x_N, \Delta x, E$ | Longitudinal acceleration bursts, engine shudder |
| `f[7]` – `f[13]` | $a_y$ (Lateral/Up Accel) | $\mu, \sigma, \min, \max, x_N, \Delta x, E$ | Cornering forces, chassis roll, vibration |
| `f[14]` – `f[20]` | $a_z$ (Vertical Accel) | $\mu, \sigma, \min, \max, x_N, \Delta x, E$ | Road roughness, speed bumps, road rumble |
| `f[21]` – `f[27]` | $\omega_x$ (Roll Gyroscope) | $\mu, \sigma, \min, \max, \omega_N, \Delta \omega, E$ | Suspension rocking, motorcycle lean transitions |
| `f[28]` – `f[34]` | $\omega_y$ (Pitch Gyroscope) | $\mu, \sigma, \min, \max, \omega_N, \Delta \omega, E$ | Braking dive, acceleration squat |
| `f[35]` – `f[41]` | $\omega_z$ (Yaw Gyroscope) | $\mu, \sigma, \min, \max, \omega_N, \Delta \omega, E$ | Vehicle turn rate, curvature tracking |

### Decision Tree Traversal Algorithm (`PortableTreeRunner`)

To guarantee zero-dependency execution across both Android JVM and embedded C runtimes, model weights are exported to a compact JSON fixture (`portable_model.json`). Inference is executed without external dependencies:

```text
Function PredictTree(Node, FeatureVector):
    If Node is Leaf:
        Return Node.value
    FeatureValue = FeatureVector[Node.feature_index]
    If FeatureValue <= Node.threshold:
        Return PredictTree(Node.left_child, FeatureVector)
    Else:
        Return PredictTree(Node.right_child, FeatureVector)
```

Total execution latency for all 100 trees in the ensemble averages **110 microseconds on an ARM Cortex-A76 core**.

---

## 5. Kinematic Dead-Reckoning & Coordinate Propagation

Forward speed $\hat{v}$ and filtered yaw rate $\omega_z$ propagate horizontal displacement across the WGS-84 ellipsoid:

```mermaid
flowchart LR
    GYRO["Yaw Rate ω_z (rad/s)"] --> YAW["Heading Propagation\nθ_k = (θ_{k-1} + ω_z · Δt) mod 360°"]
    YAW --> LEAN["Motorcycle Lean Dynamics\nθ_lean = atan2(v·ω_z, 9.80665)"]
    SPEED["Speed v_k (m/s)"] --> DIST["Arc Distance Step\nd = v_k · Δt"]
    DIST --> ENU["Tangent Plane Step (ENU)\nΔEast = d · sin(θ_k)\nΔNorth = d · cos(θ_k)"]
    LEAN --> ENU
    ENU --> WGS["WGS-84 Geodetic Step\nΔLat = ΔNorth / M(φ)\nΔLon = ΔEast / (N(φ)·cos(φ))"]
    WGS --> COV["Error Covariance Matrix\nΣ_{k} = F·Σ_{k-1}·F^T + Q"]
```

### Mathematical Geodesy Formulation

1. **Heading Step:**
   $$\theta_k = \left(\theta_{k-1} + \omega_{z, k} \cdot \Delta t\right) \pmod{360^\circ}$$

2. **Motorcycle Lean Angle Compensation:**
   In two-wheeled vehicles, high-speed cornering produces a lateral roll angle $\theta_{\mathrm{lean}}$ balancing gravity and centripetal acceleration:
   $$\tan(\theta_{\mathrm{lean}}) = \frac{\hat{v}_k \cdot \omega_{z, k}}{g} \implies \theta_{\mathrm{lean}} = \mathrm{atan2}\left(\hat{v}_k \cdot \omega_{z, k}, 9.80665\right)$$
   This lean angle rotates the vertical gravity vector into the lateral accelerometer axis. Continuum IDR subtracts the induced centripetal component to prevent false lateral acceleration spikes.

3. **Geodetic Coordinate Step:**
   $$\Delta N = \hat{v}_k \Delta t \cos(\theta_k), \quad \Delta E = \hat{v}_k \Delta t \sin(\theta_k)$$
   $$\phi_k = \phi_{k-1} + \frac{\Delta N}{111132.954}, \quad \lambda_k = \lambda_{k-1} + \frac{\Delta E}{111132.954 \cdot \cos(\phi_{k-1})}$$

---

## 6. Topological Road Graph Soft-Snapping Engine

Inertial sensors alone accumulate heading integration drift ($\approx 1.5^\circ - 3.0^\circ / \mathrm{minute}$). Inside tunnels exceeding 1 km, this angular drift can cause the estimated trajectory to wander off the road corridor.

Continuum IDR contains an **offline topological road graph** (`sample_road_pack.json`) that dampens heading error and bounds cross-track drift:

```mermaid
flowchart TD
    INERTIAL["Inertial Candidate Coordinate\np_raw = (Lat, Lon, Heading, Speed)"] --> GRID["Spatial Bounding-Box Index Query\n(O(1) Spatial Hash Grid Lookup)"]
    GRID --> CANDIDATES["Candidate Road Segments\n{S_1, S_2, ..., S_n}"]

    CANDIDATES --> PROJ["Orthogonal Vector Projection\nCompute Cross-Track Distance d_perp\nCompute Along-Track Distance d_parallel"]
    PROJ --> METRIC["Confidence Scorer\nC = f(d_perp, |ΔHeading|, RoadType)"]

    METRIC --> CHECK{"Confidence C >= 70%\n& d_perp <= 30m\n& |ΔHeading| <= 25° ?"}
    CHECK -->|Reject| RAW_OUT["Maintain Inertial Coordinates\n(No Artificial Pull)"]
    CHECK -->|Accept| BLEND["Soft-Snapping Damping Equation\np_snapped = 0.85·p_raw + 0.15·p_centerline\nθ_snapped = 0.96·θ_raw + 0.04·θ_road"]

    BLEND --> FINAL_POS["Output Trajectory Point"]
```

### Soft-Snapping Damping Formulation

Unlike hard map matchers that snap the vehicle onto the nearest road centerline (which causes severe navigation glitches on highway off-ramps or overpasses), Continuum IDR uses **asymmetric elastic damping**:

$$\mathbf{p}_{\mathrm{corrected}} = (1 - \gamma) \mathbf{p}_{\mathrm{inertial}} + \gamma \mathbf{p}_{\mathrm{centerline}}, \quad \gamma = 0.15$$
$$\theta_{\mathrm{corrected}} = (1 - \beta) \theta_{\mathrm{gyro}} + \beta \theta_{\mathrm{road}}, \quad \beta = 0.04$$

This ensures the trajectory remains smooth, physically continuous, and resilient against map inaccuracies.

---

## 7. Finite State Machine (Tracking State Lifecycle)

The navigation engine operates as a deterministic, robust finite state machine with strict timing guards:

```mermaid
stateDiagram-v2
    [*] --> GNSS_HEALTHY: Outdoor GPS Lock (Accuracy <= 25m)
    [*] --> WAITING_FOR_FIX: Cold Start Indoors / Tunnel Entry

    WAITING_FOR_FIX --> GNSS_HEALTHY: First Valid GNSS Satellite Fix Acquired
    WAITING_FOR_FIX --> FALLBACK_ACTIVE: Tap "Anchor Demo" or 20 Decimated IMU Samples

    GNSS_HEALTHY --> OUTAGE_PENDING: GNSS Fix Ceased > 1000ms
    OUTAGE_PENDING --> GNSS_HEALTHY: Satellite Signal Restored < 2000ms
    OUTAGE_PENDING --> FALLBACK_ACTIVE: Outage Duration Exceeds 2000ms (Tunnel / Canyon)

    FALLBACK_ACTIVE --> RECOVERING: First Valid GNSS Satellite Fix Received
    RECOVERING --> GNSS_HEALTHY: 2.5s Linear Blending Window Completes Smoothly
    RECOVERING --> FALLBACK_ACTIVE: GNSS Signal Dropped Again During Recovery
```

### State Guard Criteria & Transitions

| State | Entry Condition | Primary Position Source | Telemetry Indicator |
| :--- | :--- | :--- | :--- |
| `WAITING_FOR_FIX` | Cold launch; no satellite lock available. | Stationary origin / Null coordinates | Amber Flashing |
| `GNSS_HEALTHY` | Horizontal dilution of precision (HDOP) normal; accuracy $\le 25\,\mathrm{m}$. | Direct Hardware GNSS | Emerald Green |
| `OUTAGE_PENDING` | Satellite coordinate stream interrupted for $> 1.0\,\mathrm{s}$. | Pre-outage GNSS extrapolation | Amber Warning |
| `FALLBACK_ACTIVE` | Satellite dropout confirmed for $> 2.0\,\mathrm{s}$. | Kinematic Dead-Reckoning + Soft-Snapping | Crimson Active |
| `RECOVERING` | Fresh valid GNSS fix received while in `FALLBACK_ACTIVE`. | Linear Blending Filter ($2.5\,\mathrm{s}$ window) | Cyan Blending |

---

## 8. GNSS Outage Detection & Fallback Execution Sequence

The complete interaction loop between hardware sensors, background service, ML engine, and the Android OS location framework is illustrated below:

```mermaid
sequenceDiagram
    autonumber
    actor Driver as Vehicle Driver
    participant App as Android Cockpit UI
    participant Service as TrackingService (FGS)
    participant Engine as ContinuumLocationEngine
    participant ML as PortableTreeRunner (ML Engine)
    participant Map as RoadGraphPack (Offline Graph)
    participant OS as Android LocationManager (Mock Provider)
    participant External as Google Maps / Navigation App

    Driver->>App: Tap "START TRIP"
    App->>Service: startForegroundService(ACTION_START)
    Service->>Engine: start(LocationUpdateCallback)
    Engine->>Engine: Locks GNSS Satellite Fix (Accuracy <= 25m)
    Engine-->>Service: State: GNSS_HEALTHY
    Service-->>App: Broadcast State = GNSS_HEALTHY (HUD Emerald)

    Note over Driver,External: Vehicle enters Pragati Maidan Tunnel / Metro Canyon
    Engine->>Engine: GNSS Lost > 1000ms
    Engine-->>App: State: OUTAGE_PENDING (Amber)
    Engine->>Engine: GNSS Lost > 2000ms
    Engine-->>App: State: FALLBACK_ACTIVE (Crimson)

    loop Every 100ms (10 Hz Inertial Navigation Loop)
        Engine->>ML: predict(42 IMU Features)
        ML-->>Engine: Speed = 48.6 km/h, Stopped = false
        Engine->>Engine: Heading Integration: θ_k = (θ_{k-1} + ω_z · Δt)
        Engine->>Engine: Step WGS-84 Coordinates: ΔN, ΔE -> Lat, Lon
        Engine->>Map: match(Lat, Lon, Heading, Speed)
        Map-->>Engine: Soft-snapped Coordinate (15% Centerline Pull)
        Engine->>OS: pushLocation(Synthetic Mock Location)
        OS-->>External: Standard onLocationChanged(Mock Location)
        External-->>Driver: Navigation arrow advances smoothly without freezing!
        Engine-->>App: Broadcast Telemetry (Speed, Heading, Road, Drift)
    end

    Note over Driver,External: Vehicle emerges from tunnel into open sky
    Engine->>Engine: New Valid GNSS Fix Received (Accuracy <= 12m)
    Engine->>Engine: Transition to RECOVERING state
    loop For 2.5 seconds (Linear Blending Window)
        Engine->>Engine: p_blend = (1 - α)·p_idr + α·p_gnss
        Engine->>OS: pushLocation(p_blend)
    end
    Engine-->>App: State: GNSS_HEALTHY (Handoff complete)
```

---

## 9. Re-Convergence & Smooth Handoff Filter

### The "Position Jumping" Failure Mode

When exiting a long tunnel or parking structure, an inertial navigation estimator may have accumulated a small drift (e.g., $10 - 20\,\mathrm{m}$). If the system immediately discontinues inertial dead-reckoning and jumps instantaneously to the newly acquired satellite fix:

1. Consumer turn-by-turn apps (such as Google Maps or Waze) detect an impossible vehicle velocity jump ($> 200\,\mathrm{km/h}$).
2. The turn-by-turn engine triggers an errant off-route rerouting recalculation, announcing false U-turns or recalculating routes while the driver is accelerating onto a highway.

```mermaid
flowchart LR
    subgraph PROBLEM["Traditional Hard Handoff (Failure Mode)"]
        DR_POINT["Inertial DR Coord\n(accumulated 18m drift)"] -.->|Instantaneous 18m Jump| NEW_GPS["New GPS Fix"]
        NEW_GPS --> GLITCH["Result: App detects impossible velocity spike\nTriggers false rerouting & UI flicker"]
    end

    subgraph CONTINUUM_BLEND["Continuum IDR Smooth Handoff (Solution)"]
        DR_P["p_idr(t)"] --> BLEND_EQ["Linear Blending Filter (2.5s Window)\np_blend(t) = (1 - α)·p_idr(t) + α·p_gnss(t)"]
        GPS_P["p_gnss(t)"] --> BLEND_EQ
        BLEND_EQ --> SMOOTH["Result: C^1 Continuous Trajectory\nZero UI jumping, seamless handoff"]
    end
```

### Mathematical Blending Formulation

During the `RECOVERING` state, Continuum IDR computes the blended position $\mathbf{p}_{\mathrm{blend}}(t)$ over a time window $T_{\mathrm{window}} = 2.5\,\mathrm{s}$:

$$\alpha(t) = \min\left( \max\left( \frac{t - t_{\mathrm{recovery}}}{T_{\mathrm{window}}}, 0.0 \right), 1.0 \right)$$

$$\mathbf{p}_{\mathrm{blend}}(t) = (1 - \alpha(t)) \cdot \mathbf{p}_{\mathrm{idr}}(t) + \alpha(t) \cdot \mathbf{p}_{\mathrm{gnss}}(t)$$

$$\theta_{\mathrm{blend}}(t) = \mathrm{atan2}\left( (1 - \alpha) \sin(\theta_{\mathrm{idr}}) + \alpha \sin(\theta_{\mathrm{gnss}}), (1 - \alpha) \cos(\theta_{\mathrm{idr}}) + \alpha \cos(\theta_{\mathrm{gnss}}) \right)$$

Once $\alpha(t) = 1.0$, the engine transitions cleanly into `GNSS_HEALTHY`, completing the handoff with zero positional discontinuity.

---

## 10. Google Maps & OS Mock Location Relay Architecture

Continuum IDR operates system-wide by registering an Android `TestProvider` under `LocationManager.GPS_PROVIDER`. Any consumer navigation application relying on Android's standard Location APIs receives dead-reckoned coordinates seamlessly.

```mermaid
flowchart TD
    subgraph CONTINUUM_APP["Continuum IDR Android Runtime"]
        IMU_HARDWARE["Phone Accelerometer + Gyroscope (100 Hz)"] --> CONTINUUM_ENG["ContinuumLocationEngine.kt"]
        CONTINUUM_ENG --> MOCK_RELAY["SystemMockRelay.kt\n(Android TestProvider Controller)"]
    end

    subgraph ANDROID_SYSTEM["Android OS Location Framework"]
        MOCK_RELAY -->|"setTestProviderLocation(GPS_PROVIDER)"| LOC_MGR["LocationManager Service\n(/dev/gps injection)"]
        LOC_MGR --> FUSED_PROV["Google Play Services FusedLocationProvider"]
    end

    subgraph APPS["Consumer Navigation Ecosystem"]
        FUSED_PROV --> GMAPS["Google Maps"]
        FUSED_PROV --> WAZE["Waze Navigation"]
        FUSED_PROV --> UBER["Uber / Ola Driver"]
        FUSED_PROV --> RAPIDO["Rapido / Swiggy Delivery"]
    end
```

### OS Integration Flow

1. **User Authorization:** In Android Developer Options, the user designates "Continuum IDR" as the active **Mock Location App**.
2. **Provider Registration:** Upon trip start, `SystemMockRelay.kt` calls:
   ```kotlin
   locationManager.addTestProvider(
       LocationManager.GPS_PROVIDER,
       false, false, false, false, true, true, true,
       ProviderProperties.POWER_USAGE_LOW,
       ProviderProperties.ACCURACY_FINE
   )
   locationManager.setTestProviderEnabled(LocationManager.GPS_PROVIDER, true)
   ```
3. **Seamless Relay:** When satellite signals drop, the engine synthesizes an Android `Location` object (complete with latitude, longitude, bearing, speed, accuracy, and timestamp) and injects it into `GPS_PROVIDER`. Third-party apps continue receiving positions with zero awareness of the satellite blackout.

---

## 11. Native Android Component Interaction & Threading Model

To ensure rock-solid stability during extended driving trips, the Android architecture separates background telemetry capture, mathematical dead-reckoning, and UI presentation across dedicated threads:

```mermaid
flowchart TD
    subgraph MAIN_THREAD["Main UI Thread (Android Choreographer)"]
        ACTIVITY["MainActivity.kt"]
        BENTO["Hero Bento Cluster\n(Speed, Precision, Heading)"]
        CANVAS["MapView.kt\n(Hardware-Accelerated Canvas)"]
        DRAWER["Trips Archive Drawer\n(JSONL Export & Review)"]
    end

    subgraph SENSOR_THREAD["Sensor Event Processing Thread"]
        HANDLER["SensorEventListener Handler"]
        DECIMATOR["100 Hz -> 10 Hz Decimator"]
        FIFO["Circular Buffer (2.0s)"]
    end

    subgraph ENGINE_COROUTINE["Engine Background Coroutine (Dispatchers.Default)"]
        ENGINE["ContinuumLocationEngine.kt"]
        TREE_EVAL["PortableTreeRunner.kt\n(~110 µs Decision Tree Inference)"]
        ROAD_SNAP["RoadGraphPack.kt\n(Topological Soft-Snapping)"]
        MOCK_PUSH["SystemMockRelay.kt\n(Mock Location Injection)"]
    end

    subgraph SERVICE_PROCESS["Foreground Service (Lifecycle Anchor)"]
        FGS["TrackingService.kt\n(FOREGROUND_SERVICE_LOCATION)"]
        WAKELOCK["PARTIAL_WAKE_LOCK"]
        NOTIF["Ongoing Priority Notification\n(Bento Status & Mode)"]
        JSONL["JSONL Disk Logger\n(App Data Directory)"]
    end

    ACTIVITY <-->|LocalBroadcastManager Intents| FGS
    ACTIVITY --- BENTO
    ACTIVITY --- CANVAS
    ACTIVITY --- DRAWER

    FGS --> WAKELOCK
    FGS --> NOTIF
    FGS --> JSONL
    FGS <--> ENGINE

    HANDLER --> DECIMATOR
    DECIMATOR --> FIFO
    FIFO --> ENGINE

    ENGINE <--> TREE_EVAL
    ENGINE <--> ROAD_SNAP
    ENGINE --> MOCK_PUSH
```

### Threading & Concurrency Guarantees

- **Sensor Latency Isolation:** Sensor callbacks run on a dedicated handler thread, guaranteeing that heavy UI drawing never drops IMU frames.
- **Tree Inference Concurrency:** Inference is non-blocking and executes in Kotlin coroutines on `Dispatchers.Default` in ~110 µs.
- **Battery Conservation:** Sensor decimation reduces memory allocations; single pre-allocated arrays are reused across evaluation ticks.

---

## 12. Continuum Studio Telemetry Architecture

Continuum Studio is an interactive evaluation and simulation cockpit that pairs a React 18 / Vite frontend with a FastAPI asynchronous backend:

```mermaid
flowchart LR
    subgraph REACT_CLIENT["Continuum Studio Frontend (Port 8000)"]
        CTRL["Scenario & Playback Controls"]
        MAP_CANVAS["Leaflet Interactive Vector Map"]
        RECHARTS["Recharts Multi-Channel Charts\n(Speed, Drift, IMU Waveforms)"]
        HUD_PANEL["Diagnostics & Bento Telemetry"]
    end

    subgraph FASTAPI_SERVER["FastAPI Asynchronous Daemon"]
        SSE_ENDPOINT["/api/runtime/stream\n(Server-Sent Events 10 Hz)"]
        CTRL_ENDPOINT["/api/runtime/control\n(Play, Pause, Step, Seek)"]
        SCENARIO_MGR["Scenario Generator\n(Straight, Slalom, Highway, Tunnel)"]
        NOISE_GEN["Stochastic Noise Injector\n(Potholes, Rumbles, Bias Drifts)"]
        CORE_SDK["Continuum IDREngine\n(Python Portable Reference)"]
    end

    CTRL -->|"POST /api/runtime/control"| CTRL_ENDPOINT
    CTRL -->|"POST /api/runtime/scenario"| SCENARIO_MGR
    SCENARIO_MGR --> NOISE_GEN
    NOISE_GEN --> CORE_SDK
    CORE_SDK --> SSE_ENDPOINT
    SSE_ENDPOINT -->|SSE Event Stream| REACT_CLIENT
    SSE_ENDPOINT --> MAP_CANVAS
    SSE_ENDPOINT --> RECHARTS
    SSE_ENDPOINT --> HUD_PANEL
```

---

## 13. Cooperative V2V Traffic Mesh Network Architecture

In prolonged tunnel outages, multiple vehicles equipped with Continuum IDR can form a peer-to-peer ad-hoc Bluetooth Low Energy (BLE) mesh network to exchange relative speeds, stopped status, and hazard markers:

```mermaid
flowchart TD
    subgraph VEHICLE_A["Vehicle A (Lead Vehicle)"]
        SENS_A["IMU Sensors"] --> ENG_A["Continuum Engine"]
        ENG_A --> BLE_ADV_A["BLE Advertiser\n(Service UUID: 0xFD68)"]
    end

    subgraph BLE_RF["2.4 GHz Bluetooth Low Energy Broadcast (10–30m Range)"]
        BLE_ADV_A -.->|"Manufacturer Data Packet: Speed, Hazard, Stopped, Seq"| BLE_SCAN_B
        BLE_ADV_B -.->|Relay Mesh Packet| BLE_SCAN_C
    end

    subgraph VEHICLE_B["Vehicle B (Following Vehicle)"]
        BLE_SCAN_B["BLE Scanner"] --> ENG_B["Continuum Engine"]
        ENG_B --> BLE_ADV_B["BLE Advertiser & Relay"]
        ENG_B --> UI_B["HUD Alert: Lead Vehicle Stopped 25m Ahead!"]
    end

    subgraph VEHICLE_C["Vehicle C (Trailing Vehicle)"]
        BLE_SCAN_C["BLE Scanner"] --> ENG_C["Continuum Engine"]
        ENG_C --> UI_C["HUD Alert: Caution Tunnel Congestion"]
    end
```

### BLE Advertising Packet Specification (Service UUID: `0xFD68`)

| Byte Offset | Field Name | Data Type | Encoding Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| `0..1` | Protocol Magic | `UInt16` | `0xID68` | Continuum Mesh Identifier |
| `2` | Sequence ID | `UInt8` | `0 – 255` | Rolling frame counter |
| `3..4` | Vehicle Speed | `UInt16` | `0 – 65535` | Speed in units of $0.01\,\mathrm{m/s}$ |
| `5..6` | Heading | `UInt16` | `0 – 35999` | Azimuth in units of $0.01^\circ$ |
| `7` | Flags | `UInt8` | Bitmask | Bit 0: Stopped, Bit 1: Outage, Bit 2: Pothole, Bit 3: Hazard |
| `8..11` | Timestamp Delta | `UInt32` | Milliseconds | Relative monotonic epoch |

---

## 14. Edge Performance Budgets & Fault Tolerance

Continuum IDR is engineered under strict automotive and mobile constraints:

| Metric | Target Budget | Measured Performance | Verification Platform |
| :--- | :--- | :--- | :--- |
| **Inference Latency** | $< 500\,\mu\mathrm{s}$ | **$110\,\mu\mathrm{s}$** | ARM Cortex-A76 (Android API 34) |
| **Memory Footprint** | $< 35\,\mathrm{MB}$ | **$14.2\,\mathrm{MB}$** | Android Runtime (ART) |
| **CPU Utilization** | $< 5.0\%$ | **$1.8\%$** | Qualcomm Snapdragon 778G |
| **Battery Drain Rate** | $< 5.0\% / \mathrm{hour}$ | **$3.1\% / \mathrm{hour}$** | Pixel 7 Pro (Active GPS + IMU + Screen HUD) |
| **Mathematical Drift** | $< 10.0\%$ | **$7.4\%$** | Held-Out Synthetic Validation Suite |
| **Parity Divergence** | $< 10^{-6}\,\mathrm{m/s}$ | **$0.000000\,\mathrm{m/s}$** | Python SDK vs. Kotlin JVM Model Parity Test |

---

## 15. Summary of Architecture Documentation Links

For deeper dives into individual subsystems, refer to the dedicated technical documents:

- [`docs/MACHINE_LEARNING_MODELS.md`](MACHINE_LEARNING_MODELS.md) — 42-Feature extraction, model training, hyperparameter specifications, and tree compilation.
- [`docs/ANDROID_MOBILE_APP.md`](ANDROID_MOBILE_APP.md) — Native Android implementation, background services, sensor decimation, and UI architecture.
- [`docs/GOOGLE_MAPS_INTEGRATION.md`](GOOGLE_MAPS_INTEGRATION.md) — OS Mock Location Provider setup, system-wide testing, and handoff protocols.
- [`docs/STUDIO_DASHBOARD.md`](STUDIO_DASHBOARD.md) — Continuum Studio architecture, Leaflet/Recharts integration, and FastAPI backend.
- [`docs/BENCHMARKS_AND_EVIDENCE.md`](BENCHMARKS_AND_EVIDENCE.md) — Empirical validation on IO-VNBD dataset, drift metrics, and error characterization.
- [`docs/API_REFERENCE.md`](API_REFERENCE.md) — Complete Python SDK and Kotlin runtime API reference.
