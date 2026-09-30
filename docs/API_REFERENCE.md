# Continuum IDR — Complete API Reference

This reference documents the public APIs across the Python SDK, the REST Runtime Daemon, and the native Android Kotlin framework.

---

## 1. Python SDK API (`continuum_idr`)

### 1.1 Core Engine (`continuum_idr.engine`)

#### `EngineConfig`
Configuration class for the inertial dead-reckoning engine.

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `imu_rate_hz` | `float` | `10.0` | Target decimated sampling frequency for feature windows |
| `gnss_timeout_s` | `float` | `2.0` | Inactivity duration before declaring a GNSS outage |
| `accuracy_threshold_m` | `float` | `25.0` | Maximum acceptable GNSS horizontal accuracy |
| `recovery_duration_s` | `float` | `2.5` | Linear blending time when returning from outage |
| `vehicle_profile` | `VehicleProfile` | `CAR` | Vehicle dynamics profile (`CAR`, `MOTORCYCLE`, `PARKING`, `EXTERNAL_IMU`) |

#### `IDREngine(config: EngineConfig, model: MotionModelBundle, road_graph: Optional[RoadGraph] = None)`
Main navigation estimator class.

- `on_gnss(fix: GNSSFix) -> Optional[NavigationState]`  
  Ingests an incoming satellite fix. If accurate, updates coordinates and aligns baseline biases.
- `on_imu(sample: IMUSample) -> NavigationState`  
  Ingests a continuous accelerometer/gyroscope sample. Advances window, predicts speed, integrates yaw rate, and returns the updated state.
- `reset() -> None`  
  Clears all internal buffers, resets state to `GNSS_HEALTHY`.

#### `IMUSample`
Data class representing a single timestamped inertial measurement.
```python
IMUSample(
    timestamp_s: float,
    accel_mps2: tuple[float, float, float],    # (ax, ay, az) linear acceleration
    gyro_radps: tuple[float, float, float],    # (gx, gy, gz) angular velocity
    gravity_mps2: tuple[float, float, float]   # (gx, gy, gz) gravity vector
)
```

#### `GNSSFix`
Data class representing an external satellite position fix.
```python
GNSSFix(
    timestamp_s: float,
    latitude_deg: float,
    longitude_deg: float,
    speed_mps: float,
    course_deg: float,
    horizontal_accuracy_m: float
)
```

#### `NavigationState`
Output state computed at every IMU or GNSS event.
```python
NavigationState(
    timestamp_s: float,
    latitude_deg: float,
    longitude_deg: float,
    speed_mps: float,
    bearing_deg: float,
    uncertainty_m: float,
    tracking_mode: TrackingMode, # GNSS_HEALTHY, OUTAGE_PENDING, FALLBACK_ACTIVE, RECOVERING
    is_fallback: Boolean,
    segment_id: Optional[str] = None,
    match_confidence: float = 0.0,
    lean_angle_deg: float = 0.0
)
```

---

## 2. Continuum Studio REST Runtime API

Continuum Studio exposes interactive REST endpoints at `http://127.0.0.1:8000/api/runtime/`:

### 2.1 `GET /api/runtime/status`
Returns live state of the active simulation session.
```json
{
  "status": "playing",
  "scenario": "Vtb01",
  "step_index": 452,
  "total_steps": 2400,
  "elapsed_s": 45.2,
  "tracking_mode": "FALLBACK_ACTIVE",
  "is_gnss_withheld": true,
  "current_state": {
    "lat": 12.84521,
    "lon": 77.66014,
    "speed_kmh": 46.5,
    "bearing_deg": 42.0,
    "uncertainty_m": 4.2,
    "inference_latency_us": 112
  }
}
```

### 2.2 `POST /api/runtime/control`
Sends control signals to pause, step, seek, or change replay speed.
```json
// Request Body
{
  "action": "pause", // "play", "pause", "step", "restart", "set_speed"
  "speed_multiplier": 2.0
}
```

### 2.3 `POST /api/runtime/scenario`
Switches active route scenario or toggles stochastic perturbations.
```json
// Request Body
{
  "scenario": "Vtb03",
  "inject_noise": true,
  "inject_bumps": true,
  "withhold_gnss": false
}
```

### 2.4 `POST /api/runtime/toggle_gnss`
Toggles manual GNSS satellite kill switch.
```json
// Request Body
{
  "withhold": true
}
```

### 2.5 `GET /api/runtime/export`
Exports the entire active session as a `.json` or `.csv` archive.

---

## 3. Native Android Kotlin API (`ai.continuum.idr`)

### 3.1 `ContinuumLocationEngine`
Drop-in replacement for standard Android location listeners.

- `fun start(callback: LocationUpdateCallback): Unit`  
  Registers Android GNSS and IMU sensors and begins live positioning.
- `fun stop(): Unit`  
  Unregisters all sensor listeners and clears memory buffers.
- `fun setAnchorOrigin(lat: Double, lon: Double, bearingDeg: Float): Unit`  
  Sets an initial coordinate origin for indoor or desk testing.
- `fun getDiagnostics(): EngineDiagnostics`  
  Returns live inference latency (µs), sample counts, and heap memory.

### 3.2 `PortableTreeRunner`
Executes serialized decision trees on-device.

- `companion object fun fromJsonString(jsonStr: String): PortableTreeRunner`  
  Parses model weights exported from Python.
- `fun predict(features: DoubleArray): Prediction`  
  Evaluates 42 features in $\sim 100\,\text{µs}$. Returns speed (m/s), standard deviation, and stop classification.

### 3.3 `SystemMockRelay`
Connects Continuum's dead-reckoned output directly to Android's OS `GPS_PROVIDER`.

- `fun startRelay(): Boolean`  
  Registers test provider in Android OS. Returns `true` if enabled in Developer Options.
- `fun pushLocation(location: Location): Unit`  
  Pushes synthetic coordinates to Android OS for Google Maps/Waze.
- `fun stopRelay(): Unit`  
  Removes test provider and restores native hardware GPS.

### 3.4 `TrackingService` Action Constants
- `ACTION_STATUS` (`ai.continuum.idr.STATUS`): Broadcasts service status text.
- `ACTION_TELEMETRY` (`ai.continuum.idr.TELEMETRY`): Broadcasts full position, speed, and map-matching updates.
- `ACTION_HEARTBEAT` (`ai.continuum.idr.HEARTBEAT`): Emits a 500 ms periodic diagnostic pulse with sample counts and memory stats.
- `ACTION_SET_ANCHOR` (`ai.continuum.idr.SET_ANCHOR`): Command intent to set origin coordinates.
- `ACTION_TOGGLE_MOCK_RELAY` (`ai.continuum.idr.TOGGLE_MOCK_RELAY`): Command intent to start/stop Google Maps mock GPS relay.
