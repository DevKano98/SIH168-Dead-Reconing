# Continuum IDR — Android Source Integration

This directory contains Kotlin source for integrating the Continuum prototype with Android location and motion sensors. It is an integration reference, not a published Maven package or a device-certified production SDK.

## Included files

| File | Purpose |
| --- | --- |
| `ContinuumLocationEngine.kt` | Reads Android location and motion events and emits fallback location updates |
| `PortableTreeRunner.kt` | Evaluates the exported portable motion-model JSON without a Python runtime |

The Android path has different implementation details from the Python evaluator. Establish numerical and full-trajectory parity before treating them as equivalent navigation runtimes.

## Integrate the source

1. Copy both Kotlin files into your application package and update their package declaration if necessary.
2. Copy `models/portable/motion_portable.json` to `app/src/main/assets/motion_portable.json`.
3. Add location and sensor permissions to the manifest.
4. Load the portable model and start one engine instance for the active trip.

```xml
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.HIGH_SAMPLING_RATE_SENSORS" />
```

Request runtime location permission in your Activity or Compose flow before starting the engine.

```kotlin
val json = assets.open("motion_portable.json")
    .bufferedReader()
    .use { it.readText() }

val runner = PortableTreeRunner.fromJsonString(json)
val engine = ContinuumLocationEngine(this, runner)

engine.start(object : ContinuumLocationEngine.LocationUpdateCallback {
    override fun onLocationUpdate(
        location: Location,
        isFallback: Boolean,
        state: ContinuumLocationEngine.FallbackState
    ) {
        updateMap(location.latitude, location.longitude)
        updatePositioningStatus(state, isFallback)
    }

    override fun onSurfaceAnomaly(eventType: String, severity: Double) {
        logSurfaceEvent(eventType, severity)
    }

    override fun onMountShiftDetected() {
        showAlignmentWarning()
    }
})
```

Call `engine.stop()` when the owning service or screen stops tracking.

## Client behaviour

Use `FallbackState` to explain positioning quality:

- `GNSS_HEALTHY`: normal location measurements are available.
- `OUTAGE_PENDING`: the expected fix cadence has been missed but fallback is not confirmed.
- `FALLBACK_ACTIVE`: the engine is emitting a dead-reckoned location.
- `RECOVERING`: GNSS has returned and the engine is transitioning back.

Show uncertainty or degraded status to the user. Do not describe a fallback estimate as lane-level unless an independent reference test supports that claim.

## Required validation before a release

- Confirm sensor axes and mounting assumptions on the target phone and vehicle.
- Compare portable-runner output with the Python model for the same feature vectors.
- Compare complete Android and Python trajectories for the same event stream.
- Measure update rate, latency percentiles, missed deadlines, memory, battery, and thermal behaviour on named devices.
- Test permission denial, missing sensors, timestamp gaps, background execution, process recreation, and GNSS recovery.
- Run reference-based road tests outside the training domain.

The repository currently supplies the source path and component tests. It does not contain the physical-device evidence needed to claim universal phone compatibility, a specific battery cost, or production accuracy.
