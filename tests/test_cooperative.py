from continuum_idr.cooperative import TrafficReportStore, create_slowdown_report


def test_reports_expire_deduplicate_and_require_independent_origins():
    store = TrafficReportStore()
    first = create_slowdown_report("phone-a", "tunnel-east", 90, 100, 1.0, 12)
    assert store.ingest(first, 101)
    assert not store.ingest(first.relay(), 101)  # relay is not a new observation
    assert not store.confirmed_slowdown("tunnel-east", 90, 101)
    second = create_slowdown_report("phone-b", "tunnel-east", 94, 102, 2.0, 10)
    assert store.ingest(second, 102)
    assert store.confirmed_slowdown("tunnel-east", 90, 103)
    assert not store.confirmed_slowdown("tunnel-east", 90, 500)
