"""
Contract Validator (Scaffold v0.1)

Validates the ingestion contract against v0.1 invariants and required fields.
This is intentionally lightweight and vendor-agnostic.

Future:
- contract schema registry
- richer typing/constraints
- environment-specific policies
"""
from typing import Any, Dict, Optional, List
from framework.core.validation_codes import ContractValidationErrorCodes
from framework.core.validation_models import Issue, Severity, ValidationResult


def validate_contract(contract: Dict[str, Any]) -> ValidationResult:
    issues: List[Issue] = []

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
            issues.append(
                Issue(
                    code=ContractValidationErrorCodes.MISSING_REQUIRED_FIELD,
                    severity=Severity.ERROR,
                    path=p,
                    message="Required field is missing.",
                    hint=f"Add '{p}' to the contract as per the spec.",
                )
            )

    # Only stop if schema.columns is missing entirely (semantic checks depend on it)
    if any(i.path == "schema.columns" for i in issues):
        return ValidationResult(issues=issues)

    # Contract version enforcement
    contract_version = _get(contract, "contract.version")
    if contract_version != 1:
        issues.append(
            Issue(
                code=ContractValidationErrorCodes.UNSUPPORTED_CONTRACT_VERSION,
                severity=Severity.ERROR,
                path="contract.version",
                message=f"Unsupported contract version: {contract_version}. Expected: 1",
                hint="Set contract.version to 1 for v0.1 contracts.",
            )
        )

    # Validate target enums
    logical_layer = _get(contract, "target.logical_layer")
    if logical_layer not in ("bronze", "silver", "gold"):
        issues.append(
            Issue(
                code=ContractValidationErrorCodes.INVALID_VALUE,
                severity=Severity.ERROR,
                path="target.logical_layer",
                message="Must be one of: bronze, silver, gold",
            )
        )

    mode = _get(contract, "target.mode")
    if mode not in ("append", "overwrite"):
        issues.append(
            Issue(
                code=ContractValidationErrorCodes.INVALID_VALUE,
                severity=Severity.ERROR,
                path="target.mode",
                message="Must be one of: append, overwrite",
            )
        )

    # Schema columns validation
    cols = _get(contract, "schema.columns")
    if not isinstance(cols, list) or len(cols) == 0:
        issues.append(
            Issue(
                code=ContractValidationErrorCodes.EMPTY_COLUMNS,
                severity=Severity.ERROR,
                path="schema.columns",
                message="schema.columns must be a non-empty array",
                hint="Add at least one column definition under schema.columns.",
            )
        )
        return ValidationResult(issues=issues)

    # Uniqueness of column names
    seen = set()
    for i, col in enumerate(cols):
        name = col.get("name") if isinstance(col, dict) else None
        if not name:
            issues.append(
                Issue(
                    code=ContractValidationErrorCodes.MISSING_REQUIRED_FIELD,
                    severity=Severity.ERROR,
                    path=f"schema.columns[{i}].name",
                    message="Column name is required",
                )
            )
            continue

        if name in seen:
            issues.append(
                Issue(
                    code=ContractValidationErrorCodes.DUPLICATE_COLUMN,
                    severity=Severity.ERROR,
                    path=f"schema.columns[{i}].name",
                    message=f"Duplicate column name: {name}",
                )
            )
        seen.add(name)

    return ValidationResult(issues=issues)

def _get(d: Dict[str, Any], path: str) -> Any:
    """
    Safely fetch nested dict values using dotted paths like 'dataset.name'.
    Returns None if any segment is missing.
    """
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        if part not in cur:
            return None
        cur = cur[part]
    return cur