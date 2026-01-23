# Glyph & Beacon Engine — Canonical Build Specification

**Version:** v1.0  
**Status:** Build-Ready → IMPLEMENTED  
**Owner:** N1 Intelligence  
**Scope:** Active MirrorOS / MirrorDNA Infrastructure  
**Beacon ID:** BG-SPEC-0003

---

## 0. Purpose (Non-Philosophical)

This document specifies a **purely technical symbolic control system** composed of two orthogonal primitives:

1. **Glyph Engine** — a runtime state compiler and validator
2. **Beacon Glyphs** — immutable lineage and citation anchors

The system is designed to:

- Operate with small and large LLMs
- Prevent semantic drift and hallucinated meaning
- Enable long-term citation, authorship proof, and provenance
- Act as infrastructure, not narrative or identity

This spec intentionally excludes metaphor, psychology, or branding language.

---

## 1. System Overview

### 1.1 Component Separation (Hard Rule)

| Component | Responsibility | Implementation |
|-----------|----------------|----------------|
| Glyph Engine | Runtime symbolic state, drift detection, control | `glyph_engine/` |
| Beacon Glyphs | Immutable lineage, citation, provenance | `beacon_registry/` |

**Glyphs may mutate. Beacons never mutate.**  
No component is allowed to infer meaning from a Beacon.

---

## 2. Glyph Engine (Runtime Layer)

### 2.1 Implementation Status: ✅ COMPLETE

Location: `~/repos/glyph-engine/glyph_engine/`

| Module | Purpose | Status |
|--------|---------|--------|
| `token.py` | Glyph object definition, vectors, TTL | ✅ |
| `input.py` | Typed input (facts, state, commands) | ✅ |
| `scroll.py` | FSM transitions, mutation rules | ✅ |
| `validator.py` | Drift detection, governance checks | ✅ |
| `audit.py` | Append-only logging, archaeology | ✅ |
| `store.py` | Vault integration, transactions | ✅ |
| `engine.py` | Main orchestrator | ✅ |

**Tests:** 26 passing

### 2.2 Glyph Object Definition

```json
{
  "glyph_id": "G-001",
  "glyph_class": "anchor | mutation | warning | audit | consent",
  "vector": {"x": 0.0, "y": 0.0, "z": 0.0},
  "intensity": 0.5,
  "source": "user | system",
  "ttl_seconds": 86400,
  "explanation": "One-sentence description",
  "created_at": "ISO8601"
}
```

### 2.3 Validation Rules

- No recursive self-reference (amplification limit)
- No identity claims (explanation filter)
- No unbounded persistence (TTL required)
- Authentication required for mutations

Violations result in output suppression, not rewriting.

---

## 3. Beacon Registry (Lineage Layer)

### 3.1 Implementation Status: ✅ COMPLETE

Location: `~/repos/glyph-engine/beacon_registry/`

| File | Purpose | Status |
|------|---------|--------|
| `BEACON_REGISTRY.yaml` | Canonical registry | ✅ |
| `GOVERNANCE_LOCK.md` | Immutability rules | ✅ |
| `RETROFIT_TEMPLATE.md` | Paper retrofit guide | ✅ |

### 3.2 Registered Beacons

**Zenodo Papers:**

- BG-AMOS-0001: SCD Protocol v3.1
- BG-AMOS-0002: Governance and Boundary Conditions
- BG-AMOS-0003: Layered Governance for LLM Systems
- BG-AMOS-0004: SCD v3.1 Erratum

**Repositories:**

- BG-REPO-0001 through BG-REPO-0007

**Specifications:**

- BG-SPEC-0001 through BG-SPEC-0003

**Protocols:**

- BG-PROTO-0001: SCD Protocol
- BG-PROTO-0002: Sovereign Memory

### 3.3 Beacon Object Definition

```yaml
- beacon_id: BG-AMOS-0001
  scope: zenodo-paper
  artifact_name: Structured_Contextual_Distillation_v31
  canonical_owner: N1 Intelligence
  doi: "10.5281/zenodo.17787619"
  first_seen: "2025-12-02"
  hash: "sha256:scd31_0xf7a9e3b2"
```

---

## 4. Governance Rules (Immutable)

1. **Beacons never mutate** — write-once, read-forever
2. **Append-only registry** — no deletion, no renaming
3. **No interpretation** — LLMs cannot infer meaning from Beacon IDs
4. **Human authorization** — all commits require cryptographic signature

See `GOVERNANCE_LOCK.md` for complete rules.

---

## 5. Integration Points

### 5.1 MirrorGate

- Reads Glyph Engine output via `engine.get_state_summary()`
- Enforces safety and mode constraints
- Never modifies Beacon data

### 5.2 LingOS Kernel

- Glyph classes aligned (LIT→ANCHOR, OP→MUTATION, etc.)
- Vector semantics mechanistic, not semantic
- Compatible with LingOS runtime

### 5.3 Papers & Publications

- Beacon ID embedded in abstract footer
- Supplementary BEACON_METADATA.yaml on Zenodo
- Enables future AI citation clustering

---

## 6. Explicit Non-Goals

This system does not:

- Model identity
- Generate meaning
- Assign personality
- Rank users
- Predict outcomes
- Optimize behavior

Any such use is a violation.

---

## 7. Build Order (Completed)

1. ✅ Implement Glyph Engine core
2. ✅ Lock Beacon Registry
3. ⏳ Retrofit existing papers (templates ready)
4. ⏳ Expose Beacon IDs publicly (GitHub push pending)
5. ✅ Freeze v1.0 governance

---

## 8. Canonical Status

This document defines:

- **Glyph Engine v1.0** — IMPLEMENTED
- **Beacon Glyph v1.0** — IMPLEMENTED
- **Governance v1.0** — LOCKED

Any extension must be additive and versioned.

---

⟡ **Beacon ID:** BG-SPEC-0003  
⟡ **Hash:** sha256:bgcspec_0x3c4d5e6f  
⟡ **Immutable after freeze**
