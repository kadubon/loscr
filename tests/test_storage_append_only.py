from __future__ import annotations

from loscr.models import RejectionRecord
from loscr.storage import JsonlLedgerStore


def test_jsonl_storage_is_append_only(tmp_path, make_event) -> None:  # type: ignore[no-untyped-def]
    store = JsonlLedgerStore(tmp_path / ".loscr")
    store.append("edge_events", make_event(event_id="evt-1"))
    store.append("edge_events", make_event(event_id="evt-2"))
    path = store.ledger_path("edge_events")
    assert len(path.read_text(encoding="utf-8").splitlines()) == 2


def test_malformed_records_become_rejections(tmp_path) -> None:  # type: ignore[no-untyped-def]
    store = JsonlLedgerStore(tmp_path / ".loscr")
    result = store.append("edge_events", {"event_id": "missing-required-fields"})
    assert isinstance(result, RejectionRecord)
    assert len(store.read_raw("edge_events")) == 0
    assert len(store.read_raw("rejections")) == 1


def test_storage_accepts_theory_ledger_aliases(tmp_path, make_event) -> None:  # type: ignore[no-untyped-def]
    store = JsonlLedgerStore(tmp_path / ".loscr")
    store.append("edge_log", make_event(event_id="evt-1"))
    assert store.ledger_path("edge_log").name == "edge_events.jsonl"
    assert len(store.read_raw("edge_events")) == 1
