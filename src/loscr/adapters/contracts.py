"""Machine-readable adapter contracts from the LOSCR paper."""

from __future__ import annotations

from loscr.enums import ClaimLevel
from loscr.integrity import seal_model
from loscr.models import AdapterContract


def default_adapter_contracts() -> dict[str, AdapterContract]:
    """Return conservative default adapter contracts."""
    contracts = [
        AdapterContract(
            adapter_id="jsonl",
            source_system="local_jsonl",
            source_event_type="generic_record",
            field_map={"record": "declared_model"},
            conformance_tests=["schema_validation", "missing_field_rejection"],
            max_supported_claim_level=ClaimLevel.OBSERVABLE,
            integrity_hash="",
        ),
        AdapterContract(
            adapter_id="git",
            source_system="git",
            source_event_type="commit",
            field_map={
                "commit": "event_id,item_id",
                "parent_commit": "parent_event_id",
                "commit_time": "timestamp",
                "tree_hash": "output_hash",
            },
            hash_policy="hash tree or diff metadata; raw diff only by explicit caller request",
            conformance_tests=["timestamp_ordering", "identity_resolution", "hash_preservation"],
            max_supported_claim_level=ClaimLevel.CONTROLLED,
            integrity_hash="",
        ),
        AdapterContract(
            adapter_id="junit",
            source_system="junit_xml",
            source_event_type="testcase",
            field_map={
                "testcase": "item_id",
                "status": "status_raw",
                "time": "resource_raw.wall_time",
            },
            conformance_tests=["schema_validation", "status_mapping", "resource_mapping"],
            max_supported_claim_level=ClaimLevel.AUDITED,
            integrity_hash="",
        ),
        AdapterContract(
            adapter_id="llm_tool_log",
            source_system="local_llm_tool_jsonl",
            source_event_type="llm_or_tool_call",
            field_map={
                "prompt_hash": "input_hash",
                "output_hash": "output_hash",
                "token_count": "resource_raw.token_count",
                "tool_call_count": "resource_raw.tool_call_count",
            },
            conformance_tests=["prompt_hashing", "tool_manifest_hashing", "missing_field_policy"],
            max_supported_claim_level=ClaimLevel.CONTROLLED,
            integrity_hash="",
        ),
    ]
    return {contract.adapter_id: seal_model(contract) for contract in contracts}
