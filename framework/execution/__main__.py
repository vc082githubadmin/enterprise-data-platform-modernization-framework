import argparse
import json
import os
import sys

try:
    import yaml
except ImportError:
    yaml = None

from framework.execution.execution_engine import run_contract


def load_contract(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Contract file not found: {path}")

    _, ext = os.path.splitext(path.lower())

    with open(path, "r", encoding="utf-8") as f:
        if ext in (".yaml", ".yml"):
            if yaml is None:
                raise RuntimeError("PyYAML not installed. Install with: pip install pyyaml")
            return yaml.safe_load(f)
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Run governed ingestion contract.")
    parser.add_argument("--contract", required=True, help="Path to contract (JSON or YAML)")
    args = parser.parse_args()

    contract = load_contract(args.contract)

    result = run_contract(
        contract=contract,
        contract_path=args.contract,
    )

    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()