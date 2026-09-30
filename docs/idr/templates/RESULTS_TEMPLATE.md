# Experiment results template

**Status: unpopulated. No performance results are claimed by this template.**

## Provenance

| Field | Value to record |
| --- | --- |
| Experiment ID / date | Not measured |
| Dataset and transformation hash | Not recorded |
| Split manifest and parent-session counts | Not recorded |
| Model/checkpoint/export hash | Not trained |
| Profile / config / map-pack versions | Not recorded |
| Execution device / OS / runtime | Not measured |
| Initialization and adaptation policy | Not recorded |
| Reference source, quality and distance method | Not recorded |
| Outage schedule and exclusions | Not recorded |

## Per-outage table

| Run / parent session | Method | Duration s | Reference distance m | Entry error m | Endpoint error m | Relative displacement error m | Maximum error m | Drift % | Target met? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pending experiment | Pending | — | — | — | — | — | — | — | Not evaluated |

## Aggregate comparison

| Method | Independent sessions | Outages / valid coverage | Median / p95 endpoint error | Pass rate below 10% drift | Moving speed MAE | Failures |
| --- | --- | --- | --- | --- | --- | --- |
| Last-speed + gyro | — | — | — | — | — | — |
| Physical baseline | — | — | — | — | — | — |
| Learned motion + fusion | — | — | — | — | — | — |
| Plus validated constraints | — | — | — | — | — | — |

## Runtime and confidence

Record model size, process memory, p50/p95/p99 timing, output rate, missed deadlines, measurement/arrival timestamps, and thermal conditions. Record empirical uncertainty coverage and ellipse size at named confidence levels. A laptop measurement is not a smartphone measurement.

## Figures and failure notes

Attach the trajectory, speed, error and uncertainty plots specified in [the evaluation protocol](../06_EVALUATION_PROTOCOL.md). Include weak cases and exclusions. Identify the run used in the video and the rule used to select it.

## Reporting checks

- Same outages and initial conditions for compared methods.
- No hidden reference or future GNSS reaches inference.
- Repeated journey copies do not cross splits.
- Zero-distance cases reported in meters, not unstable percentages.
- Estimates, targets and measured results are labeled separately.
