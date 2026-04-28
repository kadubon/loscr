"""Local adapters for LOSCR ingestion."""

from loscr.adapters.contracts import default_adapter_contracts
from loscr.adapters.jsonl import read_jsonl_records

__all__ = ["default_adapter_contracts", "read_jsonl_records"]
