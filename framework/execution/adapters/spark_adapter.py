from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import os
import pandas as pd

from framework.execution.adapters.base import ExecutionAdapter
from framework.execution.execution_models import ExecutionStatus, ExecutionStep, StepResult
from framework.runtime.runtime_context import RuntimeContext


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dtype_to_contract_type(dtype) -> str:
    """
    Rough mapping pandas dtype -> contract type strings.
    v0.1: keep simple and evidence-based.
    """
    s = str(dtype).lower()
    if "int" in s:
        return "int"
    if "float" in s:
        return "float"
    if "datetime" in s:
        return "timestamp"
    if "bool" in s:
        return "boolean"
    return "string"


class SparkAdapter(ExecutionAdapter):
    """
    v0.1: pandas-backed implementation.
    We keep adapter name 'spark' so planner + future pyspark swap stays stable.
    """

    def name(self) -> str:
        return "spark"

    def execute_step(
        self,
        step: ExecutionStep,
        ctx: RuntimeContext,
        runtime_objects: Dict[str, Any],
    ) -> StepResult:
        start = utc_now_iso()

        try:
            if step.name == "READ":
                result = self._read(step, runtime_objects)
            elif step.name == "RUNTIME_SCHEMA_CHECK":
                result = self._schema_check(step, runtime_objects)
            elif step.name == "WRITE":
                result = self._write(step, ctx, runtime_objects)
            elif step.name == "POSTCHECK":
                result = self._postcheck(step, runtime_objects)
            else:
                raise ValueError(f"Unsupported step name: {step.name}")

            end = utc_now_iso()
            return StepResult(
                step_id=step.step_id,
                status=ExecutionStatus.SUCCEEDED,
                start_ts=start,
                end_ts=end,
                metrics=result.get("metrics", {}),
                evidence=result.get("evidence", {}),
                errors=[],
            )

        except Exception as e:
            end = utc_now_iso()
            return StepResult(
                step_id=step.step_id,
                status=ExecutionStatus.FAILED,
                start_ts=start,
                end_ts=end,
                metrics={},
                evidence={"exception_type": type(e).__name__},
                errors=[{"message": str(e)}],
            )

    def _read(self, step: ExecutionStep, runtime_objects: Dict[str, Any]) -> Dict[str, Any]:
        kind = step.inputs.get("kind")
        if kind != "file":
            raise ValueError(f"READ only supports kind=file in v0.1, got: {kind}")

        fmt = (step.inputs.get("format") or "").lower()
        location = step.inputs.get("location")

        if not location:
            raise ValueError("READ missing inputs.location")

        if not os.path.exists(location):
            raise FileNotFoundError(f"Source file not found: {location}")

        if fmt == "csv":
            df = pd.read_csv(location, **(step.inputs.get("options") or {}))
        elif fmt == "json":
            df = pd.read_json(location, **(step.inputs.get("options") or {}))
        else:
            raise ValueError(f"Unsupported file format in v0.1: {fmt}")
        
        # --- Contract-driven type coercion (v0.1) ---
        expected_schema = step.inputs.get("expected_schema") or []
        type_coercions = {"timestamp": [], "int": [], "float": [], "boolean": []}

        for col_def in expected_schema:
            if not isinstance(col_def, dict):
                continue
            col_name = col_def.get("name")
            col_type = (col_def.get("type") or "").lower()
            if not col_name or col_name not in df.columns:
                continue
            if col_type in type_coercions:
                type_coercions[col_type].append(col_name)

        # timestamps
        for c in type_coercions["timestamp"]:
            df[c] = pd.to_datetime(df[c], errors="coerce")

        # ints (nullable-friendly)
        for c in type_coercions["int"]:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")

        # floats
        for c in type_coercions["float"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        # booleans (very basic; improve later)
        for c in type_coercions["boolean"]:
            df[c] = df[c].astype("boolean")

        # Store dataframe using the symbolic ref
        out_ref = (step.outputs or {}).get("dataset_ref", "df:read")
        runtime_objects[out_ref] = df

        # Evidence: observed types after coercion
        observed_types = {col: str(dtype) for col, dtype in df.dtypes.items()}

        return {
            "metrics": {"row_count": int(len(df)), "col_count": int(len(df.columns))},
            "evidence": {
                "stored_ref": out_ref,
                "observed_columns": list(df.columns),
                "observed_types": observed_types,
                "coercions_applied": type_coercions,
            },
        }

    def _schema_check(self, step: ExecutionStep, runtime_objects: Dict[str, Any]) -> Dict[str, Any]:
        input_ref = step.inputs.get("input_ref")
        if not input_ref:
            raise ValueError("RUNTIME_SCHEMA_CHECK missing inputs.input_ref")

        df = runtime_objects.get(input_ref)
        if df is None:
            raise KeyError(f"Runtime object not found for ref: {input_ref}")

        expected = step.inputs.get("expected_schema") or []
        expected_names = [c.get("name") for c in expected if isinstance(c, dict)]

        missing = [c for c in expected_names if c not in df.columns]
        extra = [c for c in df.columns if c not in expected_names]

        # Type checks (best-effort)
        type_mismatches = []
        for c in expected:
            if not isinstance(c, dict):
                continue
            name = c.get("name")
            exp_type = (c.get("type") or "").lower()
            if name in df.columns:
                obs_type = _dtype_to_contract_type(df[name].dtype)
                # v0.1: only flag mismatch when expected is explicitly known and differs
                if exp_type and obs_type != exp_type and not (exp_type == "timestamp" and "datetime" in str(df[name].dtype).lower()):
                    type_mismatches.append({"column": name, "expected": exp_type, "observed": obs_type})

        if missing or type_mismatches:
            raise ValueError(
                f"Schema check failed. missing={missing}, type_mismatches={type_mismatches}, extra={extra}"
            )

        return {
            "metrics": {"missing_columns": 0, "type_mismatches": 0, "extra_columns": len(extra)},
            "evidence": {
                "input_ref": input_ref,
                "extra_columns": extra,
                "expected_schema_version": step.inputs.get("schema_version"),
            },
        }

    def _write(self, step: ExecutionStep, ctx: RuntimeContext, runtime_objects: Dict[str, Any]) -> Dict[str, Any]:
        input_ref = step.inputs.get("input_ref")
        if not input_ref:
            raise ValueError("WRITE missing inputs.input_ref")

        df = runtime_objects.get(input_ref)
        if df is None:
            raise KeyError(f"Runtime object not found for ref: {input_ref}")

        layer = step.inputs.get("target_layer") or "unknown_layer"
        target_table = step.inputs.get("target_table") or "unknown_table"

        # v0.1 local write target (CSV) - no pyarrow required
        safe_table = target_table.replace("/", "_")
        out_dir = os.path.join("artifacts", "data", layer, safe_table)
        os.makedirs(out_dir, exist_ok=True)

        out_path = os.path.join(out_dir, "data.csv")

        mode = (step.inputs.get("mode") or "append").lower()
        if mode not in ("append", "overwrite"):
            raise ValueError(f"Unsupported write mode in v0.1: {mode}")

        if mode == "overwrite" or not os.path.exists(out_path):
            df.to_csv(out_path, index=False)
            written = int(len(df))
        else:
            # append: read existing then concat then write (simple, not optimized)
            existing = pd.read_csv(out_path)
            combined = pd.concat([existing, df], ignore_index=True)
            combined.to_csv(out_path, index=False)
            written = int(len(df))

        runtime_objects[(step.outputs or {}).get("target_ref", target_table)] = out_path

        return {
            "metrics": {"rows_written": written},
            "evidence": {"output_path": out_path, "mode": mode},
        }

    def _postcheck(self, step: ExecutionStep, runtime_objects: Dict[str, Any]) -> Dict[str, Any]:
        # v0.1: ensure df:read exists and has rows OR target file exists (simple)
        df = runtime_objects.get("df:read")
        if df is None:
            # maybe we wrote to target path instead
            target_ref = step.inputs.get("target_ref")
            target_path = runtime_objects.get(target_ref)
            if target_path and os.path.exists(target_path):
                check_df = pd.read_csv(target_path)
                if len(check_df) <= 0:
                    raise ValueError("POSTCHECK failed: target rowcount is 0")
                return {"metrics": {"rowcount": int(len(check_df))}, "evidence": {"checked": target_path}}
            raise ValueError("POSTCHECK failed: no df:read and no target path found")

        if len(df) <= 0:
            raise ValueError("POSTCHECK failed: df:read rowcount is 0")

        return {"metrics": {"rowcount": int(len(df))}, "evidence": {"checked": "df:read"}}