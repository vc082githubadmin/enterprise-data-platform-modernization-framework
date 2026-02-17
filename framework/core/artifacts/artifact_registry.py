# Defines canonical artifact names/paths and schema versions

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactPaths:
    """
    Canonical artifact paths under a run root.
    """
    contract_snapshot: str = "contract.snapshot.json"

    validation_dir: str = "validation"
    execution_dir: str = "execution"
    step_results_dir: str = "execution/step_results"

    execution_context: str = "execution/execution_context.json"
    execution_plan: str = "execution/execution_plan.json"
    execution_summary: str = "execution/execution_summary.json"
    execution_not_attempted: str = "execution/execution_not_attempted.json"


ARTIFACT_PATHS = ArtifactPaths()


@dataclass(frozen=True)
class ArtifactSchemaVersions:
    execution_context: str = "execution_context_v1"
    execution_plan: str = "execution_plan_v1"
    execution_summary: str = "execution_summary_v1"
    execution_not_attempted: str = "execution_not_attempted_v1"


ARTIFACT_SCHEMAS = ArtifactSchemaVersions()