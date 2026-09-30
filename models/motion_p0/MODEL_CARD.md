# Model card: motion-hgbr-p0-2026-01

Trained on 50 synchronized, equal-row IO-VNBD runs from Driver A and non-Vtb Driver E families. Driver B is validation and the complete Vtb family is held out for test.

- Validation speed MAE: 3.163 m/s
- Held-out test speed MAE: 5.287 m/s
- Input: causal 2 s window at 10 Hz; gravity-subtracted accelerometer and three gyro channels
- Output: forward speed, validation-derived uncertainty bin, stop probability

This preliminary model is not validated for motorcycles, handheld phones, Indian roads, or external IMUs. See `manifest.json` for run provenance and limitations.
