from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from .data import audit_pairs, discover_synchronized_pairs, load_paired_run
from .evaluation import build_outages, evaluate_model, replay_outage
from .model import MotionModelBundle
from .training import train_motion_model


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="idr", description="Continuum IDR prototype toolkit")
    sub = parser.add_subparsers(dest="command", required=True)

    audit = sub.add_parser("audit", help="audit synchronized IO-VNBD pairs")
    audit.add_argument("--dataset", default=".")
    audit.add_argument("--output", default="artifacts/audit/pairs.json")

    train = sub.add_parser("train", help="train the P0 motion model")
    train.add_argument("--dataset", default=".")
    train.add_argument("--output", default="models/motion_p0")

    evaluate = sub.add_parser("evaluate", help="run held-out GNSS outage evaluation")
    evaluate.add_argument("--dataset", default=".")
    evaluate.add_argument("--model", default="models/motion_p0")
    evaluate.add_argument("--output", default="artifacts/evaluation")

    replay = sub.add_parser("replay", help="headless SDK replay of one held-out outage")
    replay.add_argument("--dataset", default=".")
    replay.add_argument("--model", default="models/motion_p0")
    replay.add_argument("--run", default=None)
    replay.add_argument("--outage", default=None)

    studio = sub.add_parser("studio", help="serve Continuum Studio")
    studio.add_argument("--artifacts", default="artifacts/evaluation")
    studio.add_argument("--host", default="127.0.0.1")
    studio.add_argument("--port", type=int, default=8000)
    studio.add_argument("--dataset", default=".")
    studio.add_argument("--model", default="models/motion_p0")

    export_cmd = sub.add_parser("export", help="export motion model to zero-dependency portable format")
    export_cmd.add_argument("--model", default="models/motion_p0")
    export_cmd.add_argument("--output", default="models/portable/motion_portable.json")

    stress_cmd = sub.add_parser("stress", help="run GNSS fault injection stress tests (multipath, delays, jumps)")
    stress_cmd.add_argument("--model", default="models/motion_p0")
    stress_cmd.add_argument("--duration", type=float, default=50.0)

    profile_cmd = sub.add_parser("profile", help="benchmark vehicle profiles (car, motorcycle, commercial)")
    profile_cmd.add_argument("--profile", choices=["car", "passenger_car", "motorcycle", "commercial_truck"], default="car")

    bench_cmd = sub.add_parser("benchmark-scheduler", help="benchmark 200 Hz high-frequency propagation scheduler")
    bench_cmd.add_argument("--samples", type=int, default=1000)

    mobile_cmd = sub.add_parser("mobile-demo", help="simulate mobile fallback provider across healthy/outage/recovery states")
    mobile_cmd.add_argument("--steps", type=int, default=50)

    visuals_cmd = sub.add_parser("visuals", help="generate comprehensive presentation graphs and visualizations")
    visuals_cmd.add_argument("--artifacts", default="artifacts/evaluation")

    convert_map_cmd = sub.add_parser("convert-map-pack", help="convert GeoJSON or generate regional road pack")
    convert_map_cmd.add_argument("--input", default="indian_corridor", help="Path to GeoJSON file, or preset name: 'indian_corridor', 'synthetic'")
    convert_map_cmd.add_argument("--output", default="android/app/src/main/assets/sample_road_pack.json", help="Path to write JSON pack")
    convert_map_cmd.add_argument("--name", default="Electronic City Corridor", help="Name of the road pack")
    convert_map_cmd.add_argument("--origin-lat", type=float, default=None)
    convert_map_cmd.add_argument("--origin-lon", type=float, default=None)

    synthetic_cmd = sub.add_parser("synthetic", help="generate deterministic synthetic evaluation scenarios")
    synthetic_cmd.add_argument("--scenario", default="tunnel_total_gnss_blackout_60s", help="Scenario ID or 'list'")
    synthetic_cmd.add_argument("--duration", type=float, default=None, help="Duration in seconds")
    synthetic_cmd.add_argument("--output", default=None, help="Output JSONL trip file")

    val_phone_cmd = sub.add_parser("validate-phone-log", help="validate and audit on-device recorded JSONL trip log")
    val_phone_cmd.add_argument("log_file", help="Path to JSONL trip log")

    rep_phone_cmd = sub.add_parser("phone-report", help="generate markdown validation report from phone log")
    rep_phone_cmd.add_argument("log_file", help="Path to JSONL trip log")
    rep_phone_cmd.add_argument("--output", default=None, help="Path to write markdown report")

    traffic_gw_cmd = sub.add_parser("traffic-gateway", help="run localized cooperative V2X traffic gateway")
    traffic_gw_cmd.add_argument("--host", default="127.0.0.1", help="Gateway bind host")
    traffic_gw_cmd.add_argument("--port", type=int, default=8080, help="Gateway bind port")

    synth_pack_cmd = sub.add_parser("generate-synthetic-dataset", help="generate comprehensive 17-category synthetic Indian-road dataset")
    synth_pack_cmd.add_argument("--output", default="artifacts/synthetic_dataset", help="Output directory")
    synth_pack_cmd.add_argument("--trips-per-category", type=int, default=1, help="Number of trips per category")
    synth_pack_cmd.add_argument("--seed", type=int, default=2026, help="Deterministic random seed")

    val_folder_cmd = sub.add_parser("validate-field-folder", help="audit directory of phone/synthetic trips and generate splits")
    val_folder_cmd.add_argument("folder", help="Directory containing JSONL trip logs")
    val_folder_cmd.add_argument("--output", default=None, help="Path to write JSON manifest")
    val_folder_cmd.add_argument("--train-ratio", type=float, default=0.70)
    val_folder_cmd.add_argument("--val-ratio", type=float, default=0.15)
    val_folder_cmd.add_argument("--test-ratio", type=float, default=0.15)
    val_folder_cmd.add_argument("--seed", type=int, default=42)

    eval_ref_cmd = sub.add_parser("evaluate-reference", help="benchmark trip against high-precision reference trajectory")
    eval_ref_cmd.add_argument("trip", help="Path to estimated phone JSONL trip log")
    eval_ref_cmd.add_argument("--reference", default=None, help="Path to reference CSV or JSONL ground-truth")
    eval_ref_cmd.add_argument("--output-csv", default=None, help="Path to write point-by-point error CSV")
    eval_ref_cmd.add_argument("--output-report", default=None, help="Path to write evaluation markdown report")

    exp_cmd = sub.add_parser("run-experiments", help="comparatively benchmark candidate estimator configurations")
    exp_cmd.add_argument("--model", default="models/motion_p0", help="Path to trained model bundle")
    exp_cmd.add_argument("--candidates", nargs="*", default=None, help="Candidate names (default: all 5)")
    exp_cmd.add_argument("--scenarios", nargs="*", default=None, help="Scenario IDs (default: standard suite)")
    exp_cmd.add_argument("--output", default=None, help="Path to write JSON experiment results")
    exp_cmd.add_argument("--report", default=None, help="Path to write markdown comparison report")

    args = parser.parse_args(argv)
    if args.command == "audit":
        report = audit_pairs(args.dataset)
        _write_json(Path(args.output), report)
        print(json.dumps({k: report[k] for k in ("pair_count", "equal_length_count", "unequal_length_count", "drivers")}, indent=2))
    elif args.command == "train":
        manifest = train_motion_model(args.dataset, args.output)
        print(json.dumps(manifest["metrics"], indent=2))
    elif args.command == "evaluate":
        model_path = Path(args.model)
        if not (model_path / "manifest.json").exists():
            parser.error(f"model bundle not found at '{args.model}'. Run 'python -m continuum_idr.cli train' first.")
        summary = evaluate_model(args.dataset, args.model, args.output)
        print(json.dumps(summary, indent=2))
    elif args.command == "replay":
        model_path = Path(args.model)
        if not (model_path / "manifest.json").exists():
            parser.error(f"model bundle not found at '{args.model}'. Run 'python -m continuum_idr.cli train' first.")
        model = MotionModelBundle.load(args.model)
        test_run_ids = set(model.manifest.get("test_runs", []))
        pairs = [p for p in discover_synchronized_pairs(args.dataset) if p.run_id in test_run_ids and p.equal_length]
        if args.run:
            pairs = [p for p in pairs if p.run_id == args.run]
        if not pairs:
            parser.error("requested held-out run was not found")
        run = load_paired_run(pairs[0])
        outages = build_outages(run)
        if args.outage:
            outages = [o for o in outages if o.outage_id == args.outage]
        if not outages:
            parser.error("requested outage was not found")
        metrics, _ = replay_outage(run, model, outages[0])
        print(json.dumps({"run_id": run.pair.run_id, "model_id": model.model_id, **metrics}, indent=2))
    elif args.command == "studio":
        from .studio import run

        artifacts_path = Path(args.artifacts)
        if not (artifacts_path / "demo_replay.json").exists():
            print(f"[NOTE] Evaluation artifacts not found in '{args.artifacts}'. Run 'python -m continuum_idr.cli evaluate' before launching Studio.")
        run(artifacts_path, args.host, args.port, Path(args.dataset), Path(args.model))
    elif args.command == "export":
        from .portable_model import PortableMotionBundle

        model_path = Path(args.model)
        if not (model_path / "manifest.json").exists():
            parser.error(f"model bundle not found at '{args.model}'. Run 'python -m continuum_idr.cli train' first.")
        bundle = MotionModelBundle.load(args.model)
        portable = PortableMotionBundle.from_sklearn_bundle(bundle)
        out_p = Path(args.output)
        portable.save_json(out_p)
        print(json.dumps({
            "status": "success",
            "model_id": portable.model_id,
            "output_path": str(out_p),
            "file_size_bytes": out_p.stat().st_size,
        }, indent=2))
    elif args.command == "stress":
        from .stress import CorruptionScenario, evaluate_stress_scenario

        model_path = Path(args.model)
        if not (model_path / "manifest.json").exists():
            parser.error(f"model bundle not found at '{args.model}'. Run 'python -m continuum_idr.cli train' first.")
        bundle = MotionModelBundle.load(args.model)
        scenarios = [
            CorruptionScenario("multipath_jump_80m", "80m multipath coordinate jump", multipath_jump_m=(80.0, 0.0)),
            CorruptionScenario("timestamp_reversal", "Reversed timestamps from packet jitter", out_of_order_offset_s=2.0),
            CorruptionScenario("accuracy_degradation", "Degraded dilution of precision (75m accuracy)", degraded_accuracy_m=75.0),
        ]
        results = [evaluate_stress_scenario(bundle, sc, duration_s=args.duration) for sc in scenarios]
        summary = {
            "scenarios_evaluated": len(results),
            "results": [
                {
                    "scenario": r.scenario_id,
                    "fixes_injected": r.fixes_injected,
                    "fixes_rejected": r.fixes_rejected,
                    "rejection_rate_pct": r.rejection_rate_pct,
                    "cleanly_recovered": r.cleanly_recovered,
                    "max_position_error_vs_clean_m": r.max_position_error_vs_clean_m,
                }
                for r in results
            ],
        }
        print(json.dumps(summary, indent=2))
    elif args.command == "profile":
        from .engine import IDREngine
        from .profiles import PROFILES
        from .types import EngineConfig, GNSSFix, IMUSample

        profile = PROFILES[args.profile]
        config = EngineConfig(vehicle_profile=args.profile)
        bundle = MotionModelBundle.load("models/motion_p0")
        engine = IDREngine(config, bundle)
        engine.on_gnss(GNSSFix(0.0, 52.4, -1.5, 12.0, 90.0, 3.0))

        lean_angle_deg = 0.0
        if profile.lean_angle_compensation:
            lean_angle_deg = math.degrees(profile.calculate_lean_angle_rad(speed_mps=15.0, yaw_rate_radps=0.3))

        print(json.dumps({
            "profile_name": profile.name,
            "max_speed_kmh": profile.max_speed_mps * 3.6,
            "max_accel_mps2": profile.max_accel_mps2,
            "max_yaw_rate_degps": math.degrees(profile.max_yaw_rate_radps),
            "lean_angle_compensation": profile.lean_angle_compensation,
            "sample_turn_lean_angle_deg": lean_angle_deg,
        }, indent=2))
    elif args.command == "benchmark-scheduler":
        from .engine import IDREngine
        from .scheduling import HighRateScheduler
        from .types import EngineConfig, GNSSFix, IMUSample

        config = EngineConfig(imu_rate_hz=200.0, model_update_hz=10.0)
        bundle = MotionModelBundle.load("models/motion_p0")
        bundle.manifest["sample_rate_hz"] = 200.0
        engine = IDREngine(config, bundle)
        scheduler = HighRateScheduler(engine, target_imu_rate_hz=200.0, model_rate_hz=10.0)
        scheduler.step_gnss(GNSSFix(0.0, 52.4, -1.5, 10.0, 90.0, 3.0))

        for i in range(args.samples):
            scheduler.step_imu(IMUSample(i * 0.005, (0.0, 0.0, 9.81), (0.0, 0.0, 0.0), (0.0, 0.0, 9.81)))

        metrics = scheduler.get_metrics()
        print(json.dumps({
            "target_imu_rate_hz": scheduler.target_imu_rate_hz,
            "samples_processed": metrics.total_imu_samples,
            "model_triggers": metrics.total_model_triggers,
            "avg_propagation_latency_ms": metrics.avg_propagation_latency_ms,
            "p95_propagation_latency_ms": metrics.p95_propagation_latency_ms,
            "p99_propagation_latency_ms": metrics.p99_propagation_latency_ms,
            "budget_compliance_pct": 100.0 * (1.0 - metrics.budget_exceeded_count / max(metrics.total_imu_samples, 1)),
        }, indent=2))
    elif args.command == "mobile-demo":
        from .maps import RoadGraph
        from .mobile_fallback import FallbackState, MobileFallbackEngine
        from .types import GNSSFix, IMUSample

        graph = RoadGraph.create_synthetic_corridor(origin_lat=52.4, origin_lon=-1.5, length_m=2000.0)
        bundle = MotionModelBundle.load("models/motion_p0")
        engine = MobileFallbackEngine(model_bundle=bundle, road_graph=graph, gnss_timeout_s=2.0)

        results = []
        # Phase 1: Healthy GNSS (t=0..3s)
        for i in range(3):
            t = float(i)
            fix = GNSSFix(t, 52.4 + (i * 0.0001), -1.5, 12.0, 90.0, 3.0)
            update = engine.on_gnss(fix)
            results.append(update.to_dict())

        # Phase 2: Tunnel Entry / Outage (t=3..8s, no GPS)
        for i in range(30, 80):
            t = i * 0.1
            sample = IMUSample(t, (0.0, 0.0, 9.81), (0.0, 0.0, 0.0), (0.0, 0.0, 9.81))
            update = engine.on_imu(sample)
            if update and i % 10 == 0:
                results.append(update.to_dict())

        # Phase 3: GNSS Re-acquisition / Recovery (t=8.5s)
        rec_fix = GNSSFix(8.5, 52.4008, -1.4985, 12.0, 90.0, 3.5)
        update = engine.on_gnss(rec_fix)
        results.append(update.to_dict())

        print(json.dumps({
            "status": "success",
            "lifecycle_steps": len(results),
            "healthy_samples": sum(1 for r in results if r["fallback_state"] == "GNSS_HEALTHY"),
            "fallback_active_samples": sum(1 for r in results if r["fallback_state"] == "FALLBACK_ACTIVE"),
            "recovering_samples": sum(1 for r in results if r["fallback_state"] == "RECOVERING"),
            "sample_updates": results[:2] + results[-2:]
        }, indent=2))
    elif args.command == "visuals":
        from .visuals import generate_all_visuals

        created = generate_all_visuals(args.artifacts)
        print(json.dumps({
            "status": "success",
            "plots_generated": len(created),
            "files": created,
        }, indent=2))
    elif args.command == "convert-map-pack":
        from .maps import RoadGraph, build_road_graph_from_geojson

        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if args.input == "indian_corridor":
            graph = RoadGraph.create_indian_urban_corridor(
                origin_lat=args.origin_lat or 12.8450,
                origin_lon=args.origin_lon or 77.6600,
            )
        elif args.input == "synthetic":
            graph = RoadGraph.create_synthetic_corridor(
                origin_lat=args.origin_lat or 52.4,
                origin_lon=args.origin_lon or -1.5,
            )
        else:
            graph = build_road_graph_from_geojson(
                args.input,
                origin_lat=args.origin_lat,
                origin_lon=args.origin_lon,
                name=args.name,
            )
        pack_json = graph.to_pack_json(name=args.name)
        out_path.write_text(pack_json, encoding="utf-8")
        print(json.dumps({
            "status": "success",
            "output": str(out_path),
            "nodes": len(graph.nodes),
            "segments": len(graph.segments),
            "file_size_bytes": len(pack_json.encode("utf-8")),
        }, indent=2))
    elif args.command == "synthetic":
        from .synthetic import export_scenario_jsonl, generate_scenario, list_scenarios

        if args.scenario == "list":
            print(json.dumps(list_scenarios(), indent=2))
            return 0

        res = generate_scenario(args.scenario, duration_s=args.duration)
        summary = res.to_summary()

        if args.output:
            out_p = export_scenario_jsonl(res, args.output)
            summary["exported_jsonl"] = str(out_p)

        print(json.dumps(summary, indent=2))
    elif args.command == "validate-phone-log":
        from .phone_data import PhoneLogParser

        parser_inst = PhoneLogParser(args.log_file)
        audit = parser_inst.audit()
        print(json.dumps(audit.to_dict(), indent=2))
    elif args.command == "phone-report":
        from .phone_data import generate_markdown_validation_report

        report_md = generate_markdown_validation_report(args.log_file, args.output)
        if not args.output:
            print(report_md)
        else:
            print(f"Report written to {args.output}")
    elif args.command == "traffic-gateway":
        from .traffic_gateway import run_gateway

        run_gateway(host=args.host, port=args.port)
    elif args.command == "generate-synthetic-dataset":
        from .synthetic_dataset import generate_synthetic_dataset_pack

        manifest = generate_synthetic_dataset_pack(
            output_dir=args.output,
            trips_per_category=args.trips_per_category,
            seed=args.seed,
        )
        print(json.dumps({
            "status": "success",
            "output_dir": args.output,
            "categories_count": manifest["categories_count"],
            "total_trips": manifest["total_trips"],
            "total_duration_hours": manifest["total_duration_hours"],
            "total_distance_km": manifest["total_distance_km"],
        }, indent=2))
    elif args.command == "validate-field-folder":
        from .phone_data import validate_trip_folder

        res = validate_trip_folder(
            folder_path=args.folder,
            train_ratio=args.train_ratio,
            val_ratio=args.val_ratio,
            test_ratio=args.test_ratio,
            seed=args.seed,
            out_manifest_path=args.output,
        )
        print(json.dumps({
            "status": "success",
            "summary": res["summary"],
            "data_quality": res["data_quality"],
            "missing_sensors": res["missing_sensors"],
            "splits": {
                "train_count": res["splits"]["train_count"],
                "val_count": res["splits"]["val_count"],
                "test_count": res["splits"]["test_count"],
            },
        }, indent=2))
    elif args.command == "evaluate-reference":
        from .reference_eval import evaluate_trajectory_against_reference

        rep = evaluate_trajectory_against_reference(
            trip_path=args.trip,
            reference_path=args.reference,
            out_csv_path=args.output_csv,
            out_report_path=args.output_report,
        )
        print(json.dumps(rep.to_dict(), indent=2))
    elif args.command == "run-experiments":
        from .experiments import format_experiment_comparison_markdown, run_experiment_suite

        suite = run_experiment_suite(
            candidate_names=args.candidates,
            evaluation_scenarios=args.scenarios,
            model_path=args.model,
        )
        if args.output:
            _write_json(Path(args.output), suite)
        if args.report:
            md = format_experiment_comparison_markdown(suite)
            Path(args.report).parent.mkdir(parents=True, exist_ok=True)
            Path(args.report).write_text(md, encoding="utf-8")
        print(json.dumps({
            "status": "success",
            "provenance": suite["provenance"],
            "notice": suite["notice"],
            "candidates_evaluated": suite["candidates_evaluated"],
            "results": suite["results"],
        }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
