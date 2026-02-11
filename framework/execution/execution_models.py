# Strong typed structures for plan, steps, metrics, results, pointers to artifacts
# ExecutionPlan, ExecutionStep, ExecutionResult, StepResult, ExecutionStatus

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class ExecutionStatus(str, Enum):
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass(frozen=True)
class ExecutionStep:
    step_id: str
    name: str  # READ | RUNTIME_SCHEMA_CHECK | WRITE | POSTCHECK | STUB
    adapter: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExecutionPlan:
    plan_version: str
    run_id: str
    dataset_name: str
    adapter_name: str
    contract_fingerprint: str
    steps: List[ExecutionStep] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["steps"] = [s.to_dict() for s in self.steps]
        return d


@dataclass(frozen=True)
class StepResult:
    step_id: str
    status: ExecutionStatus
    start_ts: str
    end_ts: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    evidence: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExecutionResult:
    run_id: str
    dataset_name: str
    status: ExecutionStatus
    plan_ref: Optional[str] = None
    summary_ref: Optional[str] = None
    step_results: List[StepResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["step_results"] = [sr.to_dict() for sr in self.step_results]
        return d