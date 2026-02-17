# stable interfaces
# ExecutionAdapter interface + AdapterCapabilities
from __future__ import annotations

from abc import ABC, abstractmethod
from framework.execution.execution_models import ExecutionStep, StepResult
from framework.runtime.runtime_context import RuntimeContext


class ExecutionAdapter(ABC):
    """
    Adapters are intentionally dumb: they execute a step, return a structured StepResult.
    No orchestration logic belongs here.
    """

    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def execute_step(self, step: ExecutionStep, ctx: RuntimeContext) -> StepResult:
        raise NotImplementedError