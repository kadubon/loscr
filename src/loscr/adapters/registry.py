"""Adapter extension registry."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel


class Adapter(Protocol):
    adapter_id: str
    max_supported_claim_level: str

    def read(self, path: str | Path) -> Sequence[BaseModel]:
        """Read a local source and return LOSCR model records."""


@dataclass(frozen=True)
class FunctionAdapter:
    adapter_id: str
    max_supported_claim_level: str
    reader: Callable[[str | Path], Sequence[BaseModel]]

    def read(self, path: str | Path) -> Sequence[BaseModel]:
        return self.reader(path)


class AdapterRegistry:
    """Small explicit registry for local adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, Adapter] = {}

    def register(self, adapter: Adapter) -> None:
        if adapter.adapter_id in self._adapters:
            raise ValueError(f"adapter already registered: {adapter.adapter_id}")
        self._adapters[adapter.adapter_id] = adapter

    def get(self, adapter_id: str) -> Adapter:
        try:
            return self._adapters[adapter_id]
        except KeyError as exc:
            raise KeyError(f"unknown adapter: {adapter_id}") from exc

    def list_ids(self) -> list[str]:
        return sorted(self._adapters)
