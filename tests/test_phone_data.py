from __future__ import annotations

import json
from pathlib import Path

import pytest

from continuum_idr.phone_data import (
    PhoneLogAudit,
    PhoneLogParser,
    generate_markdown_validation_report,
)
from continuum_idr.synthetic import export_scenario_jsonl, generate_scenario


@pytest.fixture
def sample_phone_log(tmp_path: Path) -> Path:
    scenario = generate_scenario("tunnel_total_gnss_blackout_60s", duration_s=40.0)
    out_file = tmp_path / "test_phone_trip.jsonl"
    export_scenario_jsonl(scenario, out_file)
    return out_file


def test_phone_log_parser_and_audit(sample_phone_log: Path):
    parser = PhoneLogParser(sample_phone_log)
    metadata, records = parser.parse()

    assert metadata is not None
    assert metadata.version == "1.0.0"
    assert metadata.device_model == "ContinuumSyntheticRig"
    assert len(records) > 100

    audit = parser.audit()
    assert audit.valid_schema is True
    assert audit.total_lines == len(records) + 1
    assert audit.duration_s > 35.0
    assert audit.avg_imu_rate_hz >= 9.0
    assert audit.gnss_records_count > 0

    audit_dict = audit.to_dict()
    assert audit_dict["valid_schema"] is True
    assert "metrics" in audit_dict


def test_markdown_validation_report(sample_phone_log: Path, tmp_path: Path):
    report_file = tmp_path / "field_report.md"
    report_md = generate_markdown_validation_report(sample_phone_log, report_file)

    assert report_file.exists()
    assert "# Continuum IDR — Field Trip Validation Report" in report_md
    assert "Sensor Health & Data Quality Audit" in report_md
    assert "GNSS Outage Drift Benchmark" in report_md


def test_phone_log_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        PhoneLogParser("non_existent_trip_file.jsonl")
