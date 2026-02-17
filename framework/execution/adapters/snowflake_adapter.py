"""
Snowflake Adapter (Stub v0.1)

Purpose:
- Prove adapter symmetry + artifact parity without requiring Snowflake connectivity.
- Returns deterministic StepResult envelopes with Snowflake-like evidence fields.

Notes:
- This adapter executes NO real SQL.
- It is suitable for demos, tests, and proving control/execution separation.
- Real Snowflake integration can be added later behind the same interface.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from framework.execution.adapters.base import ExecutionAdapter
from framework.execution.execution_models import ExecutionStep, StepResult, ExecutionStatus
from framework.runtime.runtime_context import RuntimeContext


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SnowflakeAdapter(ExecutionAdapter):
    """
    Stub adapter implementing execute_step() with deterministic outputs.

    Expected step naming (adjust mapping if your planner uses different names):
      - READ
      - RUNTIME_SCHEMA_CHECK
      - WRITE
      - POSTCHECK
    """
    def name(self) -> str:
        return "snowflake"

    ADAPTER_NAME = "snowflake"
    ADAPTER_VERSION = "0.1"

    def validate_connectivity(self, ctx) -> Dict[str, Any]:
        """
        Stub connectivity report. No external calls.
        Engine may choose to artifact this as a connectivity report.
        """
        return {
            "adapter": self.ADAPTER_NAME,
            "adapter_version": self.ADAPTER_VERSION,
            "status": "OK",
            "mode": "STUB",
            "checked_at": _utc_now_iso(),
            "notes": "No Snowflake connection attempted (stub mode).",
        }

    def execute_step(
        self,
        step: ExecutionStep,
        ctx: RuntimeContext,
        runtime_objects: Dict[str, Any],
    ) -> StepResult:
        
        start_ts = _utc_now_iso()

        # Common envelope fields
        status = ExecutionStatus.SUCCEEDED
        metrics: Dict[str, Any] = {}
        evidence: Dict[str, Any] = {
            "adapter": self.ADAPTER_NAME,
            "adapter_version": self.ADAPTER_VERSION,
            "mode": "STUB",
        }
        errors = []

        try:
            step_name = getattr(step, "name", None) or getattr(step, "step_name", None)
            step_id = getattr(step, "step_id", None) or getattr(step, "id", None)

            inputs = getattr(step, "inputs", {}) or {}
            def _ro_get(*keys):
                for k in keys:
                    if k in runtime_objects and runtime_objects[k] is not None:
                        return runtime_objects[k]
                return None

            def _ro_set(key, value):
                if value is not None:
                    runtime_objects[key] = value

            # Normalize common inputs (planner can set these)
            source_fqn = (
                inputs.get("source_fqn")
                or inputs.get("source")
                or inputs.get("source_table")
                or inputs.get("table")
                or _ro_get("source_fqn", "read_source_fqn")
            )

            target_fqn = (
                inputs.get("target_fqn")
                or inputs.get("target")
                or inputs.get("target_table")
                or inputs.get("target_ref")
                or _ro_get("target_fqn", "write_target_fqn")
            )

            mode = (inputs.get("mode") or "append").lower()

            expected_schema = inputs.get("expected_schema")  # usually dict{name:type} or list[columns]
            # Provide deterministic "query id"
            evidence["query_id"] = f"SIM-{step_id}"

            if step_name == "READ":
                # Deterministic rowcount for stub runs (can be overridden by inputs)
                rowcount = int(inputs.get("stub_rowcount", 100))
                metrics["rowcount"] = rowcount
                evidence["source_fqn"] = source_fqn
                evidence["sql"] = f"SELECT COUNT(*) FROM {source_fqn}" if source_fqn else "SELECT COUNT(*) FROM <source>"
                _ro_set("source_fqn", source_fqn)
                _ro_set("read_source_fqn", source_fqn)

            elif step_name == "RUNTIME_SCHEMA_CHECK":
                evidence["source_fqn"] = source_fqn
                # For stub: observed == expected unless a mismatch is explicitly requested
                mismatch = bool(inputs.get("stub_schema_mismatch", False))

                observed_schema = self._stub_observed_schema(expected_schema, mismatch=mismatch)
                evidence["expected_schema"] = expected_schema
                evidence["observed_schema"] = observed_schema
                evidence["diff_summary"] = self._schema_diff_summary(expected_schema, observed_schema)

                if mismatch:
                    status = ExecutionStatus.FAILED
                    errors.append("Schema mismatch detected (stub).")

            elif step_name == "WRITE":
                # Prefer source from READ if not present on this step
                source_fqn = source_fqn or _ro_get("source_fqn", "read_source_fqn")

                _ro_set("target_fqn", target_fqn)
                _ro_set("write_target_fqn", target_fqn)

                # Safety: avoid "None" in demo SQL
                safe_source = source_fqn or "<source_table>"
                safe_target = target_fqn or _ro_get("target_fqn", "write_target_fqn") or "<target_table>"

                evidence["source_fqn"] = safe_source
                evidence["target_fqn"] = safe_target
                evidence["mode"] = mode

                if mode == "overwrite":
                    evidence["sql"] = f"CREATE OR REPLACE TABLE {safe_target} AS SELECT * FROM {safe_source}"
                else:
                    evidence["sql"] = f"INSERT INTO {safe_target} SELECT * FROM {safe_source}"

                metrics["rows_affected"] = int(inputs.get("stub_rows_affected", 100))

            elif step_name == "POSTCHECK":
                safe_target = target_fqn or _ro_get("target_fqn", "write_target_fqn") or "<target_table>"
                evidence["target_fqn"] = safe_target
                evidence["sql"] = f"SELECT COUNT(*) FROM {safe_target}"
                metrics["rowcount"] = int(inputs.get("stub_target_rowcount", 100))

            else:
                status = ExecutionStatus.FAILED
                errors.append(f"Unsupported step name for SnowflakeAdapter stub: {step_name}")

        except Exception as e:
            status = ExecutionStatus.FAILED
            errors.append(f"Unhandled adapter error (stub): {type(e).__name__}: {e}")

        end_ts = _utc_now_iso()

        # Build StepResult with the same envelope as other adapters
        return StepResult(
            step_id=getattr(step, "step_id", None) or getattr(step, "id", "UNKNOWN_STEP"),
            status=status,
            start_ts=start_ts,
            end_ts=end_ts,
            metrics=metrics,
            evidence=evidence,
            errors=errors,
        )

    def _stub_observed_schema(self, expected_schema: Any, mismatch: bool) -> Any:
        """
        Return a deterministic observed schema.
        If mismatch=True, mutate one field in a predictable way.
        Supports dict-based schemas best.
        """
        if expected_schema is None:
            # Fallback: pretend we saw something
            return {"__stub_col__": "varchar"}

        if isinstance(expected_schema, dict):
            observed = dict(expected_schema)
            if mismatch and observed:
                # mutate first key deterministically
                first_key = sorted(observed.keys())[0]
                observed[first_key] = f"{observed[first_key]}__MISMATCH"
            return observed

        # If schema is list-based (e.g. [{"name":..., "type":...}]), keep as-is
        # (mismatch simulation could be added later)
        return expected_schema

    def _schema_diff_summary(self, expected: Any, observed: Any) -> Dict[str, Any]:
        """
        Lightweight diff summary for artifacts (stub-friendly).
        """
        if isinstance(expected, dict) and isinstance(observed, dict):
            missing = sorted([k for k in expected.keys() if k not in observed])
            extra = sorted([k for k in observed.keys() if k not in expected])
            type_mismatches = sorted([
                k for k in expected.keys()
                if k in observed and str(expected[k]).lower() != str(observed[k]).lower()
            ])
            return {"missing": missing, "extra": extra, "type_mismatches": type_mismatches}

        return {"note": "diff_summary not available for non-dict schema shapes (stub)."}