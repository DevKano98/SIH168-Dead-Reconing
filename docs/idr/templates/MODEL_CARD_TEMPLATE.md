# Motion model card template

**Status: specification for a future trained artifact. No trained model is attached yet.**

## Identity and use

Record model name/version, checkpoint hash, export hash, intended vehicle/mount profile, training date, repository revision, framework/runtime versions, and contact/owner. State whether the model predicts absolute speed, an anchored correction, or another quantity.

## Inputs and outputs

List ordered channels, units, frames, sample rate, causal window duration, normalization, availability masks, state context, and initialization requirements. Specify the exact interpretation of output mean, variance, stop probability, and any quality flags. Record unavailable-sensor behavior.

## Data and splitting

Identify raw sources, source hashes, transformations, semantic repairs, parent-session grouping, and train/validation/test counts. List excluded recordings and reasons. Document reference-label quality. State whether local adaptation uses pre-outage test observations and how it is bounded.

## Training

Record architecture, parameter count, loss terms, optimizer, learning rate, batch/sequence policy, seed, stopping rule, augmentations, uncertainty floor, and hyperparameters selected on validation. For anchored models, document how training rollouts reproduce the model's own state errors.

## Evaluation

Link the frozen experiment and [results table](RESULTS_TEMPLATE.md). Include speed errors, sustained bias, position drift, false stops, confidence coverage, and independent-session counts. Distinguish paired vehicle-reference tests from phone-only exploratory tests and real local-road validation.

## Deployment

Record exported operators, input/output tensor shapes, numerical parity tolerance/result, model size, named-device latency, memory, and quantization changes. Full trajectory parity should accompany single-window prediction parity.

## Limitations

Document constant-speed ambiguity, initial-state dependence, low-rate training, mounting assumptions, unsupported reverse/lean/handheld motion, magnetic sensitivity, and known failure scenarios. State what happens when the SDK detects an unsupported profile.

## Promotion checklist

- Reviewed data and fixed parent-session split.
- Held-out closed-loop evaluation against meaningful baselines.
- Causal features and no outage-label leakage.
- Uncertainty calibration measured rather than assumed.
- Export and runtime compatibility verified.
- Claims in the demo agree with this card.
