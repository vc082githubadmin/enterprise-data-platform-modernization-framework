# Week 1 Plan — Metadata-Driven Ingestion Foundation
**Branch:** `week-01-metadata-driven-ingestion`  
**Week objective:** Establish the contract-first ingestion foundation that can scale across datasets and teams in regulated enterprises.

## Why this week matters
Enterprise modernization fails when ingestion is implemented as bespoke pipelines per dataset. Week 1 locks the primary interface (the ingestion contract), establishes decision records, and adds a minimal validation scaffold so the framework can evolve safely.

## Deliverables (Week 1)
1. **Ingestion Contract Spec (v0.1)**
   - Required vs optional fields
   - Versioning approach
   - Invariants and guardrails

2. **ADR-002**
   - Contract-as-interface decision
   - Trade-offs and consequences

3. **Validation Scaffold (framework-only)**
   - Validator module
   - Error model and codes
   - Engine calls validator (still scaffold, no real ingest)

4. **Extension Model (documentation)**
   - Lifecycle hooks for future capabilities

5. **Narrative Polish**
   - README “Start Here”
   - Executive summary tightened
   - Release notes drafted

## Definition of Done (Week 1)
- A reviewer can understand the ingestion contract without reading code.
- Contract validation exists and returns actionable error information.
- Extension model is documented (hooks defined, no implementation required).
- Main branch is merge-ready and tagged `v0.1`.

## Out of Scope (Week 1)
- CDC / streaming ingestion
- Data quality execution
- Lineage/observability emission
- Any cloud-specific integrations (AWS/Azure/Snowflake/Databricks specifics)
- Production deployment concerns

## Daily Execution (lightweight)
- **Wednesday:** contract spec + ADR-002
- **Thursday:** validator scaffold + engine integration + extension model doc
- **Friday:** README + exec summary + release notes + merge & tag