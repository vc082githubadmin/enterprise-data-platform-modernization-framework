# ADR-001: Adopt a Metadata-Driven Ingestion Foundation

## Status
Accepted (v0.1)

## Context
Large-scale modernization efforts typically fail to scale when pipelines are built as bespoke code per dataset. Enterprises require repeatable ingestion patterns that support:
- governance and auditability
- schema evolution
- predictable operations
- cross-team reuse

## Decision
Adopt a **metadata-driven ingestion approach**:
- datasets are described via a contract (config)
- the framework core reads contracts and orchestrates standardized steps
- extension points allow future capabilities without rewriting ingestion logic

## Consequences
### Positive
- consistent behavior across datasets
- easier governance integration (quality/lineage/reconciliation)
- faster onboarding via configuration

### Trade-offs / Risks
- requires disciplined metadata management
- initial scaffolding feels “slower” than writing one-off pipelines
- contract drift must be controlled via validation and versioning

## Notes
v0.1 includes the scaffold: contract stub + core interfaces + repo structure. Implementations deepen in later iterations.
