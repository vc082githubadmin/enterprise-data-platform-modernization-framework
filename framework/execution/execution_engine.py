from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from framework.execution.execution_models import ExecutionResult, ExecutionStatus
from framework.execution.planner import build_execution_plan
from framework.runtime.runtime_context import RuntimeContext

from framework.core.artifacts.writer import (
    write_validation_artifact,
    write_execution_context_artifact,
    write_execution_plan_artifact,
    write_execution_summary_artifact,
    write_execution_not_attempted_artifact,
)

from framework.core.contract_validator import validate_contract


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_to_dict(obj: Any) -> Dict[str, Any]:
    """
    Try to convert validation result (or any model) to dict safely.
    """
    if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
        return obj.to_dict()
    return {}  # fallback

def _has_errors(validation_result: Any) -> bool:
    # Preferred: your ValidationResult usually has errors()
    if hasattr(validation_result, "errors") and callable(getattr(validation_result, "errors")):
        return len(validation_result.errors()) > 0

    # Otherwise: inspect issues list
    issues = getattr(validation_result, "issues", None)
    if isinstance(issues, list):
        for issue in issues:
            sev = getattr(issue, "severity", None)
            if sev is None:
                continue
            # Severity might be Enum; compare by name
            if getattr(sev, "name", str(sev)).upper() == "ERROR":
                return True
        return False

    # Fail closed (governance-safe)
    return True


def run_contract(
    contract: Dict[str, Any],
    contract_path: str = "<in-memory>",
    ctx: Optional[RuntimeContext] = None,
    artifacts_base_dir: str = "artifacts/runs",
) -> ExecutionResult:
    dataset = contract.get("dataset") or {}
    dataset_id = dataset.get("id") or dataset.get("name") or "unknown.dataset"
    ctx = ctx or RuntimeContext.new(dataset_name=dataset_id)

    # 1) Week 1: validate first (governance gate)
    validation_result = validate_contract(contract)

    # Write Week 1 validation artifact (this makes Day 1 self-contained)
    validation_artifact_path = write_validation_artifact(
        dataset_id=dataset_id,
        run_id=ctx.run_id,
        contract_path=contract_path,
        validation_result=_safe_to_dict(validation_result),
        status="PASS" if not _has_errors(validation_result) else "FAIL",
        base_dir="artifacts/validation",
    )

    # 2) If validation fails → no execution
    has_errors = _has_errors(validation_result)

    if has_errors:
        reason = {
            "message": "Validation failed. Execution not attempted.",
            "validation_artifact": validation_artifact_path,
            "validation_summary": _safe_to_dict(validation_result),
        }

        write_execution_not_attempted_artifact(
            dataset_id=dataset_id,
            run_id=ctx.run_id,
            reason=reason,
            base_dir=artifacts_base_dir,
        )

        return ExecutionResult(
            run_id=ctx.run_id,
            dataset_name=dataset_id,
            status=ExecutionStatus.SKIPPED,
        )

    # 3) Validation passed → write execution context
    ctx_ref = write_execution_context_artifact(
        dataset_id=dataset_id,
        run_id=ctx.run_id,
        execution_context={
            "run_id": ctx.run_id,
            "dataset_id": dataset_id,
            "env": ctx.env,
            "trigger": ctx.trigger,
            "started_at": ctx.started_at,
            "tags": ctx.tags,
            "adapter_config": ctx.adapter_config,
            "validation_artifact": validation_artifact_path,
        },
        base_dir=artifacts_base_dir,
    )

    # 4) Build + write plan (Day 1 stub)
    plan = build_execution_plan(contract, run_id=ctx.run_id, dataset_name=dataset_id)
    plan_ref = write_execution_plan_artifact(
        dataset_id=dataset_id,
        run_id=ctx.run_id,
        execution_plan={
            **plan.to_dict(),
            "generated_at_utc": utc_now_iso(),
        },
        base_dir=artifacts_base_dir,
    )

    # 5) Write summary (Day 1: stub / planned)
    summary_ref = write_execution_summary_artifact(
        dataset_id=dataset_id,
        run_id=ctx.run_id,
        execution_summary={
            "run_id": ctx.run_id,
            "dataset_id": dataset_id,
            "status": ExecutionStatus.PLANNED.value,
            "timestamp_utc": utc_now_iso(),
            "note": "Day1 stub - planner + artifacts only. No adapter execution.",
            "refs": {
                "validation_artifact": validation_artifact_path,
                "execution_context": ctx_ref,
                "execution_plan": plan_ref,
            },
            "steps": [
                {"step_id": s.step_id, "name": s.name, "adapter": s.adapter}
                for s in plan.steps
            ],
        },
        base_dir=artifacts_base_dir,
    )

    return ExecutionResult(
        run_id=ctx.run_id,
        dataset_name=dataset_id,
        status=ExecutionStatus.PLANNED,
        plan_ref=plan_ref,
        summary_ref=summary_ref,
        step_results=[],
    )