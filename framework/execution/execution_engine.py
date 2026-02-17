from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from framework.core.artifacts.writer import (
    write_validation_artifact,
    write_execution_context_artifact,
    write_execution_plan_artifact,
    write_execution_summary_artifact,
    write_execution_not_attempted_artifact,
    write_step_result_artifact,
)
from framework.core.contract_validator import validate_contract
from framework.execution.adapters.registry import DEFAULT_ADAPTER_REGISTRY
from framework.execution.execution_models import ExecutionResult, ExecutionStatus
from framework.execution.planner import build_execution_plan
from framework.runtime.runtime_context import RuntimeContext

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

    # 1) Validation-first governance gate (Week 1)
    validation_result = validate_contract(contract)
    has_errors = _has_errors(validation_result)

    validation_artifact_path = write_validation_artifact(
        dataset_id=dataset_id,
        run_id=ctx.run_id,
        contract_path=contract_path,
        validation_result=_safe_to_dict(validation_result),
        status="PASS" if not _has_errors(validation_result) else "FAIL",
        base_dir="artifacts/validation",
    )

    # 2) If validation fails → execution is not attempted
    if has_errors:
        reason = {
            "error_code": "VALIDATION_FAILED",
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

    # 4) Build + write deterministic execution plan (before any execution)
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

    # 5) Execute steps via adapter, artifact each step result
    runtime_objects: Dict[str, Any] = {}
    adapter = DEFAULT_ADAPTER_REGISTRY.resolve(plan.adapter_name)

    step_results = []
    step_result_refs = {}

    overall_status = ExecutionStatus.SUCCEEDED
    failed_step_id = None
    failure_code = None
    failure_message = None

    for step in plan.steps:
        step_result = adapter.execute_step(step, ctx, runtime_objects)
        step_results.append(step_result)

        ref = write_step_result_artifact(
            dataset_id=dataset_id,
            run_id=ctx.run_id,
            step_id=step.step_id,
            step_result=step_result.to_dict(),
            base_dir=artifacts_base_dir,
        )
        step_result_refs[step.step_id] = ref

        if step_result.status == ExecutionStatus.FAILED:
            failed_step_id = step.step_id
            # pull from errors if present
            if step_result.errors:
                failure_code = step_result.errors[0].get("code")
                failure_message = step_result.errors[0].get("message")
            overall_status = ExecutionStatus.FAILED
            break

    failure_block = None
    if overall_status == ExecutionStatus.FAILED:
        failure_block = {
            "failed_step_id": failed_step_id,
            "error_code": failure_code,
            "error_message": failure_message,
        }

    # 6) Unified execution summary artifact
    summary_ref = write_execution_summary_artifact(
        dataset_id=dataset_id,
        run_id=ctx.run_id,
        execution_summary={
            "run_id": ctx.run_id,
            "dataset_id": dataset_id,
            "status": overall_status.value,            
            "timestamp_utc": utc_now_iso(),
            "note": "Day3 execution - steps executed via adapter with step artifacts. Summary includes refs to step results.",
            "refs": {
                "validation_artifact": validation_artifact_path,
                "execution_context": ctx_ref,
                "execution_plan": plan_ref,
            },
            "step_result_refs": step_result_refs,
            "step_results": [sr.to_dict() for sr in step_results],
            "steps": [
                {"step_id": s.step_id, "name": s.name, "adapter": s.adapter}
                for s in plan.steps
            ],
            "failure": failure_block,
        },
        base_dir=artifacts_base_dir,
    )

    return ExecutionResult(
        run_id=ctx.run_id,
        dataset_name=dataset_id,
        status=overall_status,
        plan_ref=plan_ref,
        summary_ref=summary_ref,
        step_results=step_results,
    )