from framework.core.ingestion_engine import IngestionEngine


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
result = engine.run(invalid_contract)
print(result)

print("\n--- VALID CONTRACT TEST ---")
result = engine.run(valid_contract)
print(result)