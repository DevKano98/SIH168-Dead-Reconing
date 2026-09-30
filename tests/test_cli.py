import pytest
from continuum_idr.cli import main


def test_cli_missing_subcommand():
    with pytest.raises(SystemExit):
        main([])


def test_cli_missing_model_actionable_error():
    with pytest.raises(SystemExit) as exc_info:
        main(["evaluate", "--model", "non_existent_dir_123"])
    assert exc_info.value.code == 2


def test_cli_audit_execution(tmp_path):
    out_file = tmp_path / "pairs.json"
    code = main(["audit", "--dataset", ".", "--output", str(out_file)])
    assert code == 0
    assert out_file.exists()


def test_cli_export(tmp_path):
    out_json = tmp_path / "motion_test.json"
    code = main(["export", "--model", "models/motion_p0", "--output", str(out_json)])
    assert code == 0
    assert out_json.exists()


def test_cli_stress():
    code = main(["stress", "--model", "models/motion_p0", "--duration", "5.0"])
    assert code == 0


def test_cli_profile_motorcycle():
    code = main(["profile", "--profile", "motorcycle"])
    assert code == 0


def test_cli_benchmark_scheduler():
    code = main(["benchmark-scheduler", "--samples", "50"])
    assert code == 0


def test_cli_mobile_demo():
    code = main(["mobile-demo"])
    assert code == 0


def test_cli_visuals():
    code = main(["visuals", "--artifacts", "artifacts/evaluation"])
    assert code == 0
