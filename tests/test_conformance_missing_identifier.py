from __future__ import annotations

from loscr.checker import CheckerContext, check
from loscr.models import TelemetryReducerOutput


def test_missing_identifier_invalidates_claim(make_contract) -> None:  # type: ignore[no-untyped-def]
    contract = make_contract(claim_level="observable", ledger_schema_ids=["edge_events"])
    context = CheckerContext(
        telemetry=TelemetryReducerOutput(
            coverage_by_scope={"scope": 1.0},
            missing_identifier_events=["<missing_event_id>"],
        ),
        ledgers_present=["edge_events"],
    )
    result = check(contract, context)
    assert result.status.value == "invalid"
    assert result.supported_level.value == "descriptive"
