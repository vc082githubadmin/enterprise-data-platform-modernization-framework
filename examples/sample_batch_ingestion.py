"""
Example usage pattern (v0.1 scaffold).

This example shows how the framework *will* be used.
Actual ingestion execution is not implemented in v0.1.
"""

import yaml
from framework.core.ingestion_engine import IngestionEngine

def main():
    with open("framework/config/ingestion_contract.yaml", "r", encoding="utf-8") as f:
        contract = yaml.safe_load(f)

    engine = IngestionEngine()
    result = engine.run(contract)
    print(result)

if __name__ == "__main__":
    main()
