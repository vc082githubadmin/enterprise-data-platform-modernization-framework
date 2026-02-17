import json
import os
from datetime import datetime, timezone
# from typing import Any, Dict
import tempfile
from typing import Any, Dict, Optional

def write_validation_artifact(
    dataset_id: str,
    run_id: str,
    contract_path: str,
    validation_result: Dict[str, Any],
    status: str,
    base_dir: str = "artifacts/validation",
) -> str:
    """
    Writes a JSON artifact for every ingestion run (pass or fail).
    Path: artifacts/validation/<dataset_id>/<run_id>.json
    """
    safe_dataset = dataset_id.replace("/", "_")
    out_dir = os.path.join(base_dir, safe_dataset)
    os.makedirs(out_dir, exist_ok=True)

    artifact_path = os.path.join(out_dir, f"{run_id}.json")

    payload = {
        "run_id": run_id,
        "dataset_id": dataset_id,
        "contract_path": contract_path,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "validation": validation_result,
    }

    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return artifact_path

def _atomic_write_json(path: str, payload: Dict[str, Any]) -> None:
    """
    Best-effort atomic write: write temp then rename.
    Avoids partial files if process dies mid-write.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", suffix=".json", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False, sort_keys=True)
        os.replace(tmp_path, path)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass


def _safe_dataset(dataset_id: str) -> str:
    return dataset_id.replace("/", "_")


def write_execution_context_artifact(
    dataset_id: str,
    run_id: str,
    execution_context: Dict[str, Any],
    base_dir: str = "artifacts/runs",
) -> str:
    """
    Path: artifacts/runs/<dataset_id>/<run_id>/execution/execution_context.json
    """
    safe_dataset = _safe_dataset(dataset_id)
    out_dir = os.path.join(base_dir, safe_dataset, run_id, "execution")
    artifact_path = os.path.join(out_dir, "execution_context.json")

    payload = {
        "schema_version": "execution_context_v1",
        "run_id": run_id,
        "dataset_id": dataset_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "context": execution_context,
    }

    _atomic_write_json(artifact_path, payload)
    return artifact_path


def write_execution_plan_artifact(
    dataset_id: str,
    run_id: str,
    execution_plan: Dict[str, Any],
    base_dir: str = "artifacts/runs",
) -> str:
    """
    Path: artifacts/runs/<dataset_id>/<run_id>/execution/execution_plan.json
    """
    safe_dataset = _safe_dataset(dataset_id)
    out_dir = os.path.join(base_dir, safe_dataset, run_id, "execution")
    artifact_path = os.path.join(out_dir, "execution_plan.json")

    payload = {
        "schema_version": "execution_plan_v1",
        "run_id": run_id,
        "dataset_id": dataset_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "plan": execution_plan,
    }

    _atomic_write_json(artifact_path, payload)
    return artifact_path


def write_execution_summary_artifact(
    dataset_id: str,
    run_id: str,
    execution_summary: Dict[str, Any],
    base_dir: str = "artifacts/runs",
) -> str:
    """
    Path: artifacts/runs/<dataset_id>/<run_id>/execution/execution_summary.json
    """
    safe_dataset = _safe_dataset(dataset_id)
    out_dir = os.path.join(base_dir, safe_dataset, run_id, "execution")
    artifact_path = os.path.join(out_dir, "execution_summary.json")

    payload = {
        "schema_version": "execution_summary_v1",
        "run_id": run_id,
        "dataset_id": dataset_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "summary": execution_summary,
    }

    _atomic_write_json(artifact_path, payload)
    return artifact_path


def write_execution_not_attempted_artifact(
    dataset_id: str,
    run_id: str,
    reason: Dict[str, Any],
    base_dir: str = "artifacts/runs",
) -> str:
    """
    Path: artifacts/runs/<dataset_id>/<run_id>/execution/execution_not_attempted.json
    """
    safe_dataset = _safe_dataset(dataset_id)
    out_dir = os.path.join(base_dir, safe_dataset, run_id, "execution")
    artifact_path = os.path.join(out_dir, "execution_not_attempted.json")

    payload = {
        "schema_version": "execution_not_attempted_v1",
        "run_id": run_id,
        "dataset_id": dataset_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
    }

    _atomic_write_json(artifact_path, payload)
    return artifact_path

def write_step_result_artifact(
    dataset_id: str,
    run_id: str,
    step_id: str,
    step_result: Dict[str, Any],
    base_dir: str = "artifacts/runs",
) -> str:
    """
    Path: artifacts/runs/<dataset_id>/<run_id>/execution/step_results/<step_id>.json
    """
    safe_dataset = dataset_id.replace("/", "_")
    out_dir = os.path.join(base_dir, safe_dataset, run_id, "execution", "step_results")
    os.makedirs(out_dir, exist_ok=True)

    artifact_path = os.path.join(out_dir, f"{step_id}.json")

    payload = {
        "schema_version": "step_result_v1",
        "run_id": run_id,
        "dataset_id": dataset_id,
        "step_id": step_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "result": step_result,
    }

    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return artifact_path