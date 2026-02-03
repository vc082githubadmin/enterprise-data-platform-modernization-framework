# Ingestion Contract Specification (v0.1)

## Purpose
The ingestion contract is the **primary interface** between dataset onboarding and framework execution. It enables:
- repeatable ingestion behavior across datasets
- governance-ready evolution (quality/lineage/reconciliation hooks)
- safe scaling via configuration instead of bespoke code

The contract must be **human-readable**, **versioned**, and **validatable**.

---

## Contract Format
- YAML (preferred), JSON acceptable
- UTF-8 encoded
- Schema versioned via `contract.version`

---

## Top-Level Schema (v0.1)

### Required
- `contract.version` (integer)
- `dataset.name` (string)
- `dataset.domain` (string)
- `source.type` (enum: `file|table|api` — v0.1 supports describing these, not implementing)
- `target.logical_layer` (enum: `bronze|silver|gold`)
- `target.table_name` (string)
- `target.mode` (enum: `append|overwrite`)
- `schema.version` (integer)
- `schema.columns[]` (array)

### Optional
- `dataset.description` (string)
- `dataset.owner` (string)
- `dataset.tags[]` (array)
- `keys.primary[]` (array)
- `partitioning.columns[]` (array)
- `observability.enabled` (boolean)
- `lineage.enabled` (boolean)
- `quality.enabled` (boolean)
- `quality.rules[]` (array)

---

## Field Semantics

### `contract.version`
- Specifies the contract schema version (not the dataset schema version).
- v0.1 expects `1`.

### `dataset`
- `name`: stable identifier (kebab_case or snake_case recommended)
- `domain`: business domain (payments, risk, customer, retail, etc.)
- `description`: short purpose statement (optional but recommended)

### `source`
Represents where the dataset originates. v0.1 describes the source; future versions implement adapters.

- `type`:
  - `file` (e.g., CSV/JSON/Parquet)
  - `table` (e.g., warehouse table)
  - `api` (REST/GraphQL)
- Recommended fields (optional in v0.1):
  - `format` (for files)
  - `location` (URI/path)
  - `endpoint` (for APIs)

### `target`
Defines the logical destination and write semantics.

- `logical_layer`: `bronze|silver|gold`
- `table_name`: logical target (framework remains vendor-agnostic)
- `mode`: `append|overwrite`

### `schema`
- `version`: dataset schema version (increments on change)
- `columns[]`:
  - `name` (string)
  - `type` (string; e.g., string, int, decimal(18,2), timestamp)
  - `nullable` (boolean)

### `keys` (optional)
- `primary[]`: primary key columns. Strongly recommended for reconciliation and incremental patterns later.

### `partitioning` (optional)
- `columns[]`: partition columns for storage optimization; enforced later.

### Governance flags (optional in v0.1)
- `quality.enabled`
- `lineage.enabled`
- `observability.enabled`

These reserve space for future capabilities without changing the interface.

---

## Invariants (v0.1 Guardrails)
- `dataset.name` must be present and non-empty
- `contract.version` must be `1`
- `schema.columns` must contain at least 1 column
- Column names must be unique
- `target.logical_layer` must be one of `bronze|silver|gold`
- `target.mode` must be one of `append|overwrite`

---

## Versioning Strategy
Two independent version axes:

1. **Contract schema version** (`contract.version`)
   - Changes when the framework changes the contract structure

2. **Dataset schema version** (`schema.version`)
   - Changes when dataset columns/types change

---

## Example (v0.1)
```yaml
contract:
  version: 1

dataset:
  name: sample_customer
  domain: payments
  description: "Synthetic sample dataset for framework scaffolding."

source:
  type: file
  format: csv
  location: "examples/data/sample_customer.csv"

target:
  logical_layer: bronze
  table_name: bronze.sample_customer
  mode: append

schema:
  version: 1
  columns:
    - name: customer_id
      type: string
      nullable: false
    - name: created_ts
      type: timestamp
      nullable: true

keys:
  primary: ["customer_id"]

quality:
  enabled: false
  rules: []

lineage:
  enabled: false

observability:
  enabled: false