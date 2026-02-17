from __future__ import annotations

from typing import Dict
from framework.execution.adapters.base import ExecutionAdapter
from framework.execution.adapters.spark_adapter import SparkAdapter
from framework.execution.adapters.snowflake_adapter import SnowflakeAdapter


class AdapterNotFoundError(RuntimeError):
    pass


class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: Dict[str, ExecutionAdapter] = {}

    def register(self, adapter: ExecutionAdapter) -> None:
        self._adapters[adapter.name()] = adapter

    def resolve(self, name: str) -> ExecutionAdapter:
        if name not in self._adapters:
            raise AdapterNotFoundError(f"No adapter registered for '{name}'")
        return self._adapters[name]


# Day-1 default registry (empty)
DEFAULT_ADAPTER_REGISTRY = AdapterRegistry()
DEFAULT_ADAPTER_REGISTRY.register(SparkAdapter())
DEFAULT_ADAPTER_REGISTRY.register(SnowflakeAdapter())