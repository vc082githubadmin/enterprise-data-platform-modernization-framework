# Scope (v0.1)

## Purpose
Establish a durable, enterprise-style framework foundation for data platform modernization initiatives:
- reusable patterns over one-off pipelines
- metadata-driven behavior over hardcoding
- documented decisions (ADRs) and reference architecture
- safe-by-design thinking suitable for regulated environments

## In scope (v0.1)
- Repository structure aligned to enterprise platform work
- Metadata contract (initial draft) for batch ingestion
- Extension model (how new capabilities plug in)
- Documentation set: scope, principles, executive summary, reference architecture
- ADR-001 documenting the initial architectural decision

## Out of scope (v0.1)
- CDC implementation
- Streaming implementation
- ML training/serving pipelines
- Vendor-specific deployment (AWS/Azure/Snowflake/Databricks specifics)
- Production hardening (SLAs, SLOs, autoscaling policies, etc.)

## Definition of done for v0.1
- Clear README with positioning and repo navigation
- Reference architecture document exists
- ADR-001 exists and is coherent
- Ingestion contract stub exists
- Framework skeleton exists with clear extension points
