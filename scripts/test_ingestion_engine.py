import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from framework.core.ingestion_engine import IngestionEngine

import json
from dataclasses import asdict


def print_result(result):
    d = asdict(result)
    print(f"Status: {d['status']}")
    print(f"Dataset: {d['dataset_name']}")
    details = d.get("details") or {}
    issues = details.get("issues", [])
    if issues:
        print("Issues:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. [{issue['severity']}:{issue['code']}] {issue['path']}")
            print(f"     {issue['message']}")
            if issue.get("hint"):
                print(f"     Hint: {issue['hint']}")
    else:
        print("Details:", details)



# ---- INVALID CONTRACT (missing dataset.name) ----
invalid_contract = {
    "contract": {"version": 1},
    "dataset": {
        # "name" missing on purpose
        "domain": "payments"
    },
    "source": {"type": "file"},
    "target": {
        "logical_layer": "bronze",
        "table_name": "bronze.sample",
        "mode": "append"
    },
    "schema": {
        "version": 1,
        "columns": []
    }
}


# ---- VALID CONTRACT (minimal happy path) ----
valid_contract = {
    "contract": {"version": 1},
    "dataset": {
        "name": "sample_customer",
        "domain": "payments"
    },
    "source": {"type": "file"},
    "target": {
        "logical_layer": "bronze",
        "table_name": "bronze.sample_customer",
        "mode": "append"
    },
    "schema": {
        "version": 1,
        "columns": [
            {"name": "customer_id", "type": "string", "nullable": False}
        ]
    }
}


engine = IngestionEngine(strict_validation=False)

print("\n--- INVALID CONTRACT TEST ---")
# result = engine.run(invalid_contract)
# print(json.dumps(asdict(result), indent=2))
print_result(engine.run(invalid_contract))

print("\n--- VALID CONTRACT TEST ---")
# result = engine.run(valid_contract)
# print(json.dumps(asdict(result), indent=2))
print_result(engine.run(valid_contract))