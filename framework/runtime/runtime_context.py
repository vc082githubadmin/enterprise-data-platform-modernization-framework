# Run ID, environment, correlation IDs, timestamps, adapter config, credentials handles (not secrets)
from __future__ import annotations
from framework.core.contract_validator import validate_contract
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass(frozen=True)
class RuntimeContext:
    """
    Non-secret runtime context. Safe to artifact.
    """
    run_id: str
    dataset_name: str
    env: str = "dev"
    trigger: str = "manual"  # manual | airflow | job | api
    started_at: str = field(default_factory=utc_now_iso)
    tags: Dict[str, str] = field(default_factory=dict)

    # Adapter-level runtime config (warehouse name, cluster label, etc.)
    adapter_config: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def new(dataset_name: str, env: str = "dev", trigger: str = "manual",
            tags: Optional[Dict[str, str]] = None,
            adapter_config: Optional[Dict[str, Any]] = None) -> "RuntimeContext":
        return RuntimeContext(
            run_id=str(uuid.uuid4()),
            dataset_name=dataset_name,
            env=env,
            trigger=trigger,
            tags=tags or {},
            adapter_config=adapter_config or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)