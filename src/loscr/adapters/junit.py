"""JUnit XML adapter for local CI/evaluator records."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

from loscr.hashing import attach_integrity_hash, canonical_hash
from loscr.models import EdgeEventEnvelope, ResourceRaw


def junit_to_edge_events(
    path: str | Path,
    *,
    claim_scope_id: str = "default",
    station_id: str = "ci",
    policy_id: str = "junit",
) -> list[EdgeEventEnvelope]:
    """Convert local JUnit XML test cases into Layer 0 events."""
    tree = ElementTree.parse(Path(path))
    root = tree.getroot()
    events: list[EdgeEventEnvelope] = []
    for index, testcase in enumerate(root.iter("testcase")):
        classname = testcase.attrib.get("classname", "unknown")
        name = testcase.attrib.get("name", f"case-{index}")
        time_value = float(testcase.attrib.get("time", "0") or 0)
        failed = testcase.find("failure") is not None or testcase.find("error") is not None
        skipped = testcase.find("skipped") is not None
        status = "skipped" if skipped else "failed" if failed else "passed"
        item_id = f"{classname}.{name}"
        data = {
            "event_id": f"junit:{canonical_hash({'item': item_id, 'index': index})}",
            "event_type": "junit_testcase",
            "timestamp": "1970-01-01T00:00:00Z",
            "item_id": item_id,
            "parent_event_id": None,
            "station_id": station_id,
            "policy_id": policy_id,
            "action_type": "test",
            "substrate_fingerprint": canonical_hash({"adapter": "junit", "path": Path(path).name}),
            "status_raw": status,
            "resource_raw": ResourceRaw(wall_time=time_value, compute_seconds=time_value).model_dump(
                mode="json"
            ),
            "queue_channel": "validation",
            "queue_age_raw": 0.0,
            "dependency_flag": False,
            "reuse_count": 0,
            "input_hash": canonical_hash({"testcase": item_id}),
            "output_hash": canonical_hash({"status": status}),
            "claim_scope_id": claim_scope_id,
        }
        events.append(EdgeEventEnvelope.model_validate(attach_integrity_hash(data)))
    return events
