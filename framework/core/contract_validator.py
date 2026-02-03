"""
Contract Validator (Scaffold v0.1)

Validates the ingestion contract against v0.1 invariants and required fields.
This is intentionally lightweight and vendor-agnostic.

Future:
- contract schema registry
- richer typing/constraints
- environment-specific policies
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ContractValidationErrorCodes:
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_VALUE = "INVALID_VALUE"
    DUPLICATE_COLUMN = "DUPLICATE_COLUMN"
    EMPTY_COLUMNS = "EMPTY_COLUMNS"
    UNSUPPORTED_CONTRACT_VERSION = "UNSUPPORTED_CONTRACT_VERSION"


@dataclass
class ValidationError:
    code: str
    path: str
    message: str


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)

    def raise_if_invalid(self) -> None:
        if not self.is_valid:
            formatted = "\n".join([f"- [{e.code}] {e.path}: {e.message}" for e in self.errors])
            raise ValueError(f"Contract validation failed:\n{formatted}")


def _get(dct: Dict[str, Any], path: str) -> Optional[Any]:
    """
    Safe get using dot-separated path. Returns None if any segment is missing.
    Example: _get(contract, "dataset.name")
    """
    cur: Any = dct
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def validate_contract(contract: Dict[str, Any]) -> ValidationResult:
    errors: List[ValidationError] = []

    # Required fields (v0.1)
    required_paths = [
        "contract.version",
        "dataset.name",
        "dataset.domain",
        "source.type",
        "target.logical_layer",
        "target.table_name",
        "target.mode",
        "schema.version",
        "schema.columns",
    ]

    for p in required_paths:
        if _get(contract, p) is None:
            errors.append(
                ValidationError(
                    code=ContractValidationErrorCodes.MISSING_REQUIRED_FIELD,
                    path=p,
                    message="Required field is missing.",
                )
            )

    # Stop early if core structure is missing
    if errors:
        return ValidationResult(is_valid=False, errors=errors)

    # Contract version enforcement
    contract_version = _get(contract, "contract.version")
    if contract_version != 1:
        errors.append(
            ValidationError(
                code=ContractValidationErrorCodes.UNSUPPORTED_CONTRACT_VERSION,
                path="contract.version",
                message=f"Unsupported contract version: {contract_version}. Expected: 1",
            )
        )

    # Validate target enums
    logical_layer = _get(contract, "target.logical_layer")
    if logical_layer not in ("bronze", "silver", "gold"):
        errors.append(
            ValidationError(
                code=ContractValidationErrorCodes.INVALID_VALUE,
                path="target.logical_layer",
                message="Must be one of: bronze, silver, gold",
            )
        )

    mode = _get(contract, "target.mode")
    if mode not in ("append", "overwrite"):
        errors.append(
            ValidationError(
                code=ContractValidationErrorCodes.INVALID_VALUE,
                path="target.mode",
                message="Must be one of: append, overwrite",
            )
        )

    # Schema columns validation
    cols = _get(contract, "schema.columns")
    if not isinstance(cols, list) or len(cols) == 0:
        errors.append(
            ValidationError(
                code=ContractValidationErrorCodes.EMPTY_COLUMNS,
                path="schema.columns",
                message="schema.columns must be a non-empty array",
            )
        )
        return ValidationResult(is_valid=False, errors=errors)

    # Uniqueness of column names
    seen = set()
    for i, col in enumerate(cols):
        name = col.get("name") if isinstance(col, dict) else None
        if not name:
            errors.append(
                ValidationError(
                    code=ContractValidationErrorCodes.MISSING_REQUIRED_FIELD,
                    path=f"schema.columns[{i}].name",
                    message="Column name is required",
                )
            )
            continue

        if name in seen:
            errors.append(
                ValidationError(
                    code=ContractValidationErrorCodes.DUPLICATE_COLUMN,
                    path=f"schema.columns[{i}].name",
                    message=f"Duplicate column name: {name}",
                )
            )
        seen.add(name)

    return ValidationResult(is_valid=(len(errors) == 0), errors=errors)