from __future__ import annotations

from typing import Tuple
from framework.execution.error_codes import ExecutionErrorCode


def map_exception_to_error(e: Exception) -> Tuple[ExecutionErrorCode, str]:
    msg = str(e)

    if isinstance(e, FileNotFoundError):
        return ExecutionErrorCode.SOURCE_NOT_FOUND, msg

    if isinstance(e, KeyError):
        return ExecutionErrorCode.STEP_FAILED, msg

    if isinstance(e, ValueError):
        if "Schema check failed" in msg:
            return ExecutionErrorCode.SCHEMA_MISMATCH, msg
        if "POSTCHECK failed" in msg:
            return ExecutionErrorCode.POSTCHECK_FAILED, msg
        if "Unsupported step name" in msg:
            return ExecutionErrorCode.UNSUPPORTED_STEP, msg
        if "Unsupported file format" in msg:
            return ExecutionErrorCode.UNSUPPORTED_FORMAT, msg
        if "WRITE missing inputs.input_ref" in msg or "Unsupported write mode" in msg:
            return ExecutionErrorCode.WRITE_FAILED, msg
        return ExecutionErrorCode.STEP_FAILED, msg

    return ExecutionErrorCode.INTERNAL_ERROR, msg