import json
import os
from datetime import datetime, timezone
from typing import Any, Dict


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