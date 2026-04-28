from __future__ import annotations

from loscr.schemas import export_json_schemas


def test_schema_export_works(tmp_path) -> None:  # type: ignore[no-untyped-def]
    written = export_json_schemas(tmp_path)
    names = {path.name for path in written}
    assert "AdapterContract.schema.json" in names
    assert "EdgeEventEnvelope.schema.json" in names
    assert "ClaimContract.schema.json" in names
    assert "CheckerResult.schema.json" in names
