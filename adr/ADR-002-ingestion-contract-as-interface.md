# ADR-002: Treat the Ingestion Contract as the Primary Interface

## Status
Accepted (Week 1)

## Context
In enterprise modernization, ingestion pipelines often proliferate into bespoke implementations per dataset. This creates:
- inconsistent behavior across teams and domains
- governance gaps (quality/lineage/reconciliation applied unevenly)
- operational unpredictability
- high onboarding cost for new datasets

A framework intended to scale across regulated enterprises needs a stable, auditable interface that supports:
- repeatability
- validation
- versioning
- extension without rewrites

## Decision
Adopt the **ingestion contract** as the **primary interface** for onboarding and executing ingestion behavior.

The framework core will:
- read the contract
- validate required fields and invariants
- drive standardized orchestration
- expose extension hooks that can act on the contract and outcomes

## Consequences

### Positive
- Consistent ingestion behavior across datasets and teams
- Config-first onboarding (faster time-to-production)
- Natural place to attach governance controls (quality/lineage/reconciliation)
- Clear versioning boundaries (contract schema vs dataset schema)

### Trade-offs / Risks
- Contract drift becomes a failure mode if not validated and versioned
- Some teams may resist “constraints” in favor of bespoke flexibility
- Requires disciplined documentation and schema governance over time

### Mitigations
- Provide a validator with explicit error codes and actionable messages
- Maintain ADR history to justify interface changes
- Keep the contract minimal and evolve via versioning

## Notes
v0.1 introduces:
- contract specification (docs)
- validation scaffold (code)
- reserved sections for future platform capabilities (quality/lineage/observability)