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

    # required_paths = [
    #     "contract.version",
    #     "dataset.name",
    #     "dataset.domain",
    #     "source.type",
    #     "target.logical_layer",
    #     "target.table_name",
    #     "target.mode",
    #     "schema.version",
    #     "schema.columns",
    # ]

    required_paths = [
        "contract.schema_version",
        "dataset.name",
        "dataset.domain",
        "source.kind",
        "target.layer",
        "target.table",
        "target.write.mode",
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
    contract_version = _get(contract, "contract.schema_version")
    if contract_version != 1:
        issues.append(
            Issue(
                code=ContractValidationErrorCodes.UNSUPPORTED_CONTRACT_VERSION,
                severity=Severity.ERROR,
                path="contract.schema_version",
                message=f"Unsupported contract version: {contract_version}. Expected: 1",
                hint="Set contract.version to 1 for v0.1 contracts.",
            )
        )

    # Validate target enums
    logical_layer = _get(contract, "target.layer")
    if logical_layer not in ("bronze", "silver", "gold"):
        issues.append(
            Issue(
                code=ContractValidationErrorCodes.INVALID_VALUE,
                severity=Severity.ERROR,
                path="target.layer",
                message="Must be one of: bronze, silver, gold",
            )
        )
    
    # Validate source enums
    source_kind = _get(contract, "source.kind")
    if source_kind not in ("file", "table", "api"):
        issues.append(
            Issue(
                code=ContractValidationErrorCodes.INVALID_VALUE,
                severity=Severity.ERROR,
                path="source.kind",
                message="Must be one of: file, table, api",
            )
        )

    # If source.kind == file, require minimal file block fields
    if source_kind == "file":
        if _get(contract, "source.file.format") is None:
            issues.append(
                Issue(
                    code=ContractValidationErrorCodes.MISSING_REQUIRED_FIELD,
                    severity=Severity.ERROR,
                    path="source.file.format",
                    message="Required field is missing for file source.",
                    hint="Add 'source.file.format' for file sources.",
                )
            )
        if _get(contract, "source.file.location") is None:
            issues.append(
                Issue(
                    code=ContractValidationErrorCodes.MISSING_REQUIRED_FIELD,
                    severity=Severity.ERROR,
                    path="source.file.location",
                    message="Required field is missing for file source.",
                    hint="Add 'source.file.location' for file sources.",
                )
            )

    write_mode = _get(contract, "target.write.mode")
    if write_mode not in ("append", "overwrite"):
        issues.append(
            Issue(
                code=ContractValidationErrorCodes.INVALID_VALUE,
                severity=Severity.ERROR,
                path="target.write.mode",
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
    col_names: List[str] = []

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
        else:
            seen.add(name)
            col_names.append(name)

    # Semantic checks: keys.primary must exist in schema columns
    primary_keys = _get(contract, "keys.primary")
    if primary_keys is not None:
        if not isinstance(primary_keys, list) or len(primary_keys) == 0:
            issues.append(
                Issue(
                    code=ContractValidationErrorCodes.INVALID_VALUE,
                    severity=Severity.ERROR,
                    path="keys.primary",
                    message="keys.primary must be a non-empty array when provided",
                )
            )
        else:
            for j, key in enumerate(primary_keys):
                if key not in col_names:
                    issues.append(
                        Issue(
                            code=ContractValidationErrorCodes.INVALID_VALUE,
                            severity=Severity.ERROR,
                            path=f"keys.primary[{j}]",
                            message=f"Primary key '{key}' must exist in schema.columns",
                            hint="Add the column to schema.columns or fix keys.primary.",
                        )
                    )

    # Semantic checks: partitioning.columns must exist in schema columns
    part_cols = _get(contract, "partitioning.columns")
    if part_cols is not None:
        if not isinstance(part_cols, list):
            issues.append(
                Issue(
                    code=ContractValidationErrorCodes.INVALID_VALUE,
                    severity=Severity.ERROR,
                    path="partitioning.columns",
                    message="partitioning.columns must be an array when provided",
                )
            )
        else:
            for j, c in enumerate(part_cols):
                if c not in col_names:
                    issues.append(
                        Issue(
                            code=ContractValidationErrorCodes.INVALID_VALUE,
                            severity=Severity.ERROR,
                            path=f"partitioning.columns[{j}]",
                            message=f"Partition column '{c}' must exist in schema.columns",
                            hint="Add the column to schema.columns or fix partitioning.columns.",
                        )
                    )


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