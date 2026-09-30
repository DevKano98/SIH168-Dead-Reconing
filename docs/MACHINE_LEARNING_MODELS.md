# Continuum IDR — Machine Learning Models & Portable Edge Inference

This document details the machine learning models, feature engineering pipelines, training routines, portable serialization format, and on-device execution engine in Continuum IDR.

---

## 1. Machine Learning Overview

Vehicles without mechanical odometry connections (such as standard consumer cars and motorcycles using smartphones) cannot directly query wheel rotation counts. Continuum IDR replaces wheel speed hardware with an **Inertial Machine Learning Estimator**:

```
[Phone IMU (100 Hz)] ──> [2.0s Window] ──> [42 Statistical Features] 
                                                   │
                   ┌───────────────────────────────┴───────────────────────────────┐
                   ▼                                                               ▼
[HistGradientBoosting Speed Regressor]                          [Logistic Regression Stop Classifier]
(Estimates forward velocity 0–55 m/s)                           (Computes P(stopped) from 0.0 to 1.0)
                   │                                                               │
                   └───────────────────────────────┬───────────────────────────────┘
                                                   ▼
                                        [Final Gated Speed]
                                     (0.0 km/h if P >= 0.50)
```

---

## 2. Feature Extraction Pipeline

Features are extracted from a causal 2.0-second sliding window at 10 Hz (20 samples per channel). Each sample contains 6 channels:
- Linear Acceleration: $a_x, a_y, a_z$ ($\text{m/s}^2$)
- Angular Velocity: $\omega_x, \omega_y, \omega_z$ ($\text{rad/s}$)

### The 42-Feature Vector Layout

| Index Range | Channel | Statistics Computed (7 per channel) |
| :--- | :--- | :--- |
| `00 – 06` | Linear Accel X | Mean, Std, Min, Max, Last, Delta, Root-Energy |
| `07 – 13` | Linear Accel Y | Mean, Std, Min, Max, Last, Delta, Root-Energy |
| `14 – 20` | Linear Accel Z | Mean, Std, Min, Max, Last, Delta, Root-Energy |
| `21 – 27` | Gyroscope X | Mean, Std, Min, Max, Last, Delta, Root-Energy |
| `28 – 34` | Gyroscope Y | Mean, Std, Min, Max, Last, Delta, Root-Energy |
| `35 – 41` | Gyroscope Z | Mean, Std, Min, Max, Last, Delta, Root-Energy |

### Statistical Formulations
1. **Mean:** Central tendency of acceleration or rotation.
2. **Standard Deviation:** Captures suspension vibration variance, road surface irregularities, and engine RPM harmonics.
3. **Min / Max:** Extreme peak accelerations (e.g., bumps, braking events, aggressive cornering).
4. **Last:** Instantaneous value at window boundary.
5. **Delta ($x_{\mathrm{last}} - x_{\mathrm{first}}$):** Rate of change over the 2-second interval (acceleration onset or braking ramp).
6. **Root-Energy ($\sqrt{\frac{1}{N} \sum x^2}$):** Total spectral dynamic intensity, distinguishing stationary engine idling from high-speed cruising.

---

## 3. Model Architectures & Training Workflow

### 3.1 Speed Estimator: Histogram Gradient Boosting
The speed regressor uses `sklearn.ensemble.HistGradientBoostingRegressor`:
- **Algorithm:** Histogram-based gradient boosted decision trees.
- **Tree Count:** 50–100 boosting stages.
- **Loss Function:** Least Squares with shrinkage ($\eta = 0.1$).
- **Maximum Leaves:** 31 leaves per tree.
- **Inference Time:** ~80 µs on modern ARM CPUs.

### 3.2 Stop Detector: Regularized Logistic Regression
In low-speed stop-and-go traffic, pure regression trees often predict low non-zero velocities (e.g., 0.8–1.5 m/s) when a vehicle is actually stationary at a traffic light. To eliminate artificial position creep:
- A `LogisticRegression` classifier is trained on binary stopped masks ($\text{speed} < 0.25\,\text{m/s}$).
- When $P(\text{stopped}) \ge 0.50$, output speed is forcefully clamped to $0.0\,\text{m/s}$, activating the **Zero Velocity Update (ZUPT)** filter.

### 3.3 Dynamic Uncertainty Binning
To provide error ellipses to navigation layers, the speed domain $[0, 55]\,\text{m/s}$ is partitioned into uncertainty bins based on empirical residual standard deviations:
- Low speed ($0 - 5\,\text{m/s}$): $\sigma_v \approx 0.35\,\text{m/s}$
- Medium speed ($5 - 20\,\text{m/s}$): $\sigma_v \approx 0.80\,\text{m/s}$
- High speed ($> 20\,\text{m/s}$): $\sigma_v \approx 1.80\,\text{m/s}$

---

## 4. Portable Edge Serialization (`motion_portable.json`)

Running machine learning models on Android or embedded automotive microcontrollers typically requires heavy runtimes like TensorFlow Lite or ONNX Runtime. Continuum IDR avoids all heavy dependencies by exporting the entire trained model into a single lightweight, self-contained JSON bundle:

```json
{
  "manifest": {
    "version": "1.0.0",
    "model_id": "continuum-motion-p0",
    "feature_names": ["accel_x_mean", "accel_x_std", "..."],
    "uncertainty_bins_mps": [0.0, 5.0, 15.0, 25.0],
    "uncertainty_std_mps": [0.35, 0.65, 1.10, 1.85]
  },
  "speed_mean": 12.435,
  "stop_linear_intercept": -0.852,
  "stop_linear_weights": [-0.12, 0.45, -0.08, "... 42 weights ..."],
  "speed_trees": [
    [
      {"f": 1, "th": 0.452, "l": 1, "r": 2},
      {"v": -1.24},
      {"f": 27, "th": -0.012, "l": 3, "r": 4},
      {"v": 0.85},
      {"v": 2.15}
    ]
  ]
}
```

### Tree Node Structure
Each node in `speed_trees` is compactly serialized:
- Decision Node: `{"f": feature_index, "th": threshold, "l": left_child, "r": right_child}`
- Leaf Node: `{"v": leaf_contribution_value}`

---

## 5. Zero-Dependency Kotlin Runtime (`PortableTreeRunner.kt`)

On Android, [`PortableTreeRunner.kt`](file:///d:/iovnbd/IO-VNBD/android/app/src/main/java/ai/continuum/idr/PortableTreeRunner.kt) parses this JSON at startup into memory structures.

### Performance Benchmarks
- **Cold load time:** $< 25\,\text{ms}$
- **Inference latency per step:** $85 - 140\,\text{µs}$ (0.00014 seconds)
- **Memory footprint:** $< 4.5\,\text{MB}$ heap
- **External dependencies:** Zero (standard Android JSON & Math libraries only)

### Parity Guarantees
We enforce continuous float-level parity tests between Python scikit-learn and the Kotlin portable tree runner:
- Python test: `tests/test_portable_model.py`
- Kotlin JVM test: `android/app/src/test/java/ai/continuum/idr/ParityTest.kt`
- **Tolerance:** $\max |\hat{v}_{\mathrm{Python}} - \hat{v}_{\mathrm{Kotlin}}| < 10^{-5}\,\text{m/s}$.
