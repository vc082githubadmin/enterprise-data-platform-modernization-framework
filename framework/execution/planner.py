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


def infer_adapter_name(contract: Dict[str, Any]) -> str:
    # We will tune this mapping as our contract schema evolves.
    src_type = (contract.get("source") or {}).get("kind", "unknown")
    # Example mappings:
    # - "spark" -> "spark"
    # - "snowflake" -> "snowflake"
    # - "file" -> "spark" (because Spark reads files)
    mapping = {
        "spark": "spark",
        "snowflake": "snowflake",
        "file": "spark",
        "table": "snowflake",   # choose snowflake for v0.1 table source
        "api": "spark",         # placeholder
    }
    return mapping.get(str(src_type).lower(), "unknown")


def build_execution_plan(contract: Dict[str, Any], run_id: str, dataset_name: str) -> ExecutionPlan:
    adapter_name = infer_adapter_name(contract)
    fp = contract_fingerprint(contract)

    # Day-1: placeholder step only
    steps = [
        ExecutionStep(
            step_id="001_stub",
            name="STUB",
            adapter=adapter_name,
            inputs={"note": "Day1 stub - no execution"},
            outputs={},
        )
    ]

    return ExecutionPlan(
        plan_version="execution_plan_v1",
        run_id=run_id,
        dataset_name=dataset_name,
        adapter_name=adapter_name,
        contract_fingerprint=fp,
        steps=steps,
    )