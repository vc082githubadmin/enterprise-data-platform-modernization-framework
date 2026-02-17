# Converts contract fields into an executable plan (deterministic)

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from framework.execution.execution_models import ExecutionPlan, ExecutionStep


def _canonical_json(obj: Dict[str, Any]) -> str:
    # Stable ordering, no whitespace differences
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def contract_fingerprint(contract: Dict[str, Any]) -> str:
    payload = _canonical_json(contract).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def _get(d: Dict[str, Any], path: str, default=None):
    """
    Lightweight dot-path getter: "target.write.mode"
    """
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def infer_adapter_name(contract: Dict[str, Any]) -> str:
    source_kind = (_get(contract, "source.kind", "unknown") or "unknown").lower()

    mapping = {
        "file": "spark",
        "table": "snowflake",  # v0.1 choice: table sources come from snowflake
        "api": "spark",        # placeholder
    }
    return mapping.get(source_kind, "unknown")

def _build_read_step(contract: Dict[str, Any], adapter: str) -> ExecutionStep:
    source_kind = _get(contract, "source.kind")
    if source_kind == "file":
        return ExecutionStep(
            step_id="001_read",
            name="READ",
            adapter=adapter,
            inputs={
                "kind": "file",
                "format": _get(contract, "source.file.format"),
                "location": _get(contract, "source.file.location"),
                "options": _get(contract, "source.file.options", {}) or {},
                "expected_columns": [c.get("name") for c in (_get(contract, "schema.columns") or []) if isinstance(c, dict)],
                "expected_schema": [
                    {"name": c.get("name"), "type": c.get("type"), "nullable": c.get("nullable", True)}
                        for c in (_get(contract, "schema.columns") or [])
                        if isinstance(c, dict)
                    ],
            },
            outputs={"dataset_ref": "df:read"},  # symbolic reference for later steps
        )

    if source_kind == "table":
        return ExecutionStep(
            step_id="001_read",
            name="READ",
            adapter=adapter,
            inputs={
                "kind": "table",
                "table": _get(contract, "source.table.name"),  # if/when you add this field
                "columns": [c.get("name") for c in (_get(contract, "schema.columns") or []) if isinstance(c, dict)],
            },
            outputs={"dataset_ref": "resultset:read"},
        )

    # fallback
    return ExecutionStep(
        step_id="001_read",
        name="READ",
        adapter=adapter,
        inputs={"kind": source_kind},
        outputs={"dataset_ref": "unknown"},
    )

def _build_schema_check_step(contract: Dict[str, Any], adapter: str) -> ExecutionStep:
    cols = _get(contract, "schema.columns") or []
    expected = []
    for c in cols:
        if isinstance(c, dict):
            expected.append(
                {"name": c.get("name"), "type": c.get("type"), "nullable": c.get("nullable", True)}
            )

    return ExecutionStep(
        step_id="002_runtime_schema_check",
        name="RUNTIME_SCHEMA_CHECK",
        adapter=adapter,
        inputs={
            "input_ref": "df:read",
            "expected_schema": expected,
            "schema_version": _get(contract, "schema.version"),
        },
        outputs={"schema_check_ref": "schema_check:002"},
    )

def _build_write_step(contract: Dict[str, Any], adapter: str) -> ExecutionStep:
    return ExecutionStep(
        step_id="003_write",
        name="WRITE",
        adapter=adapter,
        inputs={
            "input_ref": "df:read",
            "target_layer": _get(contract, "target.layer"),
            "target_table": _get(contract, "target.table"),
            "mode": _get(contract, "target.write.mode"),
            "merge": _get(contract, "target.write.merge", {}),
            "primary_keys": _get(contract, "keys.primary", []),
            "partition_cols": _get(contract, "partitioning.columns", []),
        },
        outputs={"target_ref": _get(contract, "target.table")},
    )

def _build_postcheck_step(contract: Dict[str, Any], adapter: str) -> ExecutionStep:
    return ExecutionStep(
        step_id="004_postcheck",
        name="POSTCHECK",
        adapter=adapter,
        inputs={
            "target_ref": _get(contract, "target.table"),
            "checks": [
                {"name": "rowcount_nonzero", "enabled": True},
            ],
        },
        outputs={"postcheck_ref": "postcheck:004"},
    )

def build_execution_plan(contract: Dict[str, Any], run_id: str, dataset_name: str) -> ExecutionPlan:
    adapter = infer_adapter_name(contract)
    fp = contract_fingerprint(contract)

    steps = [
        _build_read_step(contract, adapter),
        _build_schema_check_step(contract, adapter),
        _build_write_step(contract, adapter),
        _build_postcheck_step(contract, adapter),
    ]

    return ExecutionPlan(
        plan_version="execution_plan_v1",
        run_id=run_id,
        dataset_name=dataset_name,
        adapter_name=adapter,
        contract_fingerprint=fp,
        steps=steps,
    )