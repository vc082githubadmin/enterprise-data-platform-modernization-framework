from typing import Any, Dict
import yaml

def load_contract(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("Contract YAML root must be a mapping/object.")
    return data