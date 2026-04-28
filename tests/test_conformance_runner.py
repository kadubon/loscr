from __future__ import annotations

from loscr.conformance import run_conformance_path


def test_machine_readable_conformance_fixtures_pass() -> None:
    results = run_conformance_path("examples/synthetic_conformance")
    assert len(results) == 6
    assert all(item["passed"] for item in results)
