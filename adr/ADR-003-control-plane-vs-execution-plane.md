# ADR-003: Separation of Control Plane and Execution Plane

**Status:** Accepted  
**Date:** 2026-02-09  
**Decision Makers:** Data Platform Architecture  
**Context:** Enterprise Data Platform Modernization Framework

---

## Context

Week 1 of the framework established **contract-first ingestion** with deterministic validation and immutable validation artifacts.  
However, without a clear separation between *decision-making* and *runtime execution*, ingestion frameworks tend to drift toward:

- pipeline-centric logic
- tool-defined semantics
- implicit governance behavior
- brittle modernization and migration paths

In many enterprise platforms, execution engines (Spark jobs, SQL scripts, connectors) silently accumulate responsibilities such as schema interpretation, write semantics, and governance enforcement. Over time, execution becomes the architecture.

This leads to:
- inconsistent behavior across datasets
- difficulty auditing or explaining ingestion outcomes
- unsafe schema evolution
- poor AI/ML readiness due to lack of reproducible intent

To prevent this, the framework must explicitly distinguish **what should happen** from **how it happens**.

---

## Decision

We will **separate the Control Plane from the Execution Plane** in the framework.

- The **Control Plane** is responsible for:
  - interpreting validated ingestion contracts
  - enforcing invariants and governance rules
  - deciding *what actions are permitted*
  - producing a deterministic execution plan artifact

- The **Execution Plane** is responsible for:
  - executing an approved execution plan
  - performing runtime operations via adapters
  - emitting immutable execution artifacts
  - never redefining platform semantics

Execution **must not occur** unless:
- contract validation has passed
- an execution plan has been explicitly produced by the control plane

This separation is enforced structurally in the framework.

---

## Consequences

### Positive
- Clear architectural boundary between intent and runtime behavior
- Deterministic, auditable ingestion runs
- Tooling becomes an implementation detail, not architecture
- Governance becomes enforceable by design, not by convention
- Platform behavior becomes portable across execution engines
- Strong foundation for AI- and agent-assisted orchestration

### Trade-offs
- Additional abstraction layers increase initial complexity
- Execution adapters are intentionally constrained and less flexible
- Some runtime optimizations may require explicit control-plane changes

These trade-offs are acceptable to ensure long-term scalability, safety, and governance.

---

## Alternatives Considered

### 1. Pipeline-Centric Architecture
Allow execution pipelines to interpret contracts and enforce behavior directly.

**Rejected because:**
- semantics become tool-dependent
- governance is inconsistently applied
- behavior becomes difficult to audit or migrate

### 2. Tool-Native Orchestration Only
Rely entirely on Spark, Snowflake, or cloud-native orchestration semantics.

**Rejected because:**
- platform behavior becomes vendor-locked
- migration requires pipeline-by-pipeline rewrites
- architectural intent is lost over time

---

## Implications for Future Capabilities

This decision enables:
- deterministic execution artifacts for audit and compliance
- safe schema evolution and incremental modernization
- AI and agentic systems that reason over metadata, not pipelines
- controlled automation with explicit human and policy boundaries

The control plane becomes the **system of record for intent**, while the execution plane becomes the **system of action**.

---

## Related Decisions

- ADR-002: Ingestion Contract as Primary Interface
- Week 1: Validation-first semantics and immutable artifacts

---

## Notes

This ADR intentionally avoids committing to:
- specific execution engines
- performance optimizations
- production deployment models

Those concerns will be addressed incrementally without violating this separation.