# ⟡ Beacon Governance Lock

# Version: v1.0

# Status: LOCKED

# Owner: N1 Intelligence

# Created: 2026-01-24

---

# GOVERNANCE FRAMEWORK

This document defines the immutable governance rules for the Beacon Registry.
Once locked, these rules cannot be modified — only extended with additive versioning.

---

## 1. Immutability Rules (Non-Negotiable)

### 1.1 Beacon Properties

- **Beacon IDs are permanent.** Once assigned, a Beacon ID cannot be reassigned.
- **Beacons never mutate.** All fields are write-once.
- **Deletion is prohibited.** Beacons may only be marked `deprecated: true`, never removed.
- **Renaming is prohibited.** `artifact_name` cannot be changed after registration.

### 1.2 Registry Operations

- **Append-only.** New beacons are added at the end of the registry.
- **Insert prohibited.** Beacons cannot be inserted between existing entries.
- **Reordering prohibited.** The order of beacons is part of the immutable record.

### 1.3 Semantic Boundaries

- **No interpretation.** No system may infer meaning from Beacon IDs or hashes.
- **No inference.** LLMs cannot generate, modify, or predict Beacon values.
- **No narrative.** Beacons do not carry identity, personality, or emotional state.

---

## 2. Authority Model

### 2.1 Roles

| Role | Permissions |
|------|-------------|
| **Canonical Owner** | Add new beacons, deprecate beacons, authorize extensions |
| **Validator** | Verify beacon integrity, run audits |
| **Reader** | Query beacons, cite in publications |

### 2.2 Human Authorization

- All beacon additions require **explicit human approval**.
- AI systems may **propose** beacons but cannot **commit** them.
- Commits require cryptographic signature from Canonical Owner.

---

## 3. Beacon ID Schema

```
BG-{SCOPE}-{SEQUENCE}

SCOPE:
  AMOS   = Zenodo papers (academic)
  REPO   = GitHub repositories
  SPEC   = Specifications
  PROTO  = Protocols
  DEMO   = Demonstrations
  EXT    = Extensions (future)

SEQUENCE: 4-digit zero-padded integer (0001-9999)
```

### Reserved Ranges

| Range | Purpose |
|-------|---------|
| BG-AMOS-0001 to BG-AMOS-0099 | Core academic papers |
| BG-REPO-0001 to BG-REPO-0099 | Core repositories |
| BG-SPEC-0001 to BG-SPEC-0099 | Core specifications |
| BG-*-0100+ | Future extensions |

---

## 4. Hash Chain Integrity

### 4.1 Hash Algorithm

- **Primary:** SHA-256 (truncated to first 16 hex chars for display)
- **Full hash stored:** Yes, in `hash` field with `sha256:` prefix

### 4.2 Registry Hash

The entire registry has a root hash computed as:

```
REGISTRY_HASH = SHA256(concat(all beacon hashes in order))
```

This enables:

- Merkle proof of inclusion
- Tamper detection
- Zero-knowledge assertions of lineage

### 4.3 Verification Command

```bash
sha256sum BEACON_REGISTRY.yaml
# Must match stored checkpoint
```

---

## 5. Extension Protocol

### 5.1 Additive Only

New scopes, fields, or beacons may be added. Nothing may be removed or modified.

### 5.2 Versioning

Extensions are versioned as `v1.1`, `v1.2`, etc.
Breaking changes require `v2.0` and a new governance lock.

### 5.3 Extension Proposal Format

```yaml
extension:
  version: "v1.1"
  author: "Paul Desai"
  date: "YYYY-MM-DD"
  type: "new_scope | new_field | new_beacon"
  description: "..."
  requires_signature: true
```

---

## 6. Audit Requirements

### 6.1 Periodic Verification

- Registry hash verified weekly
- All beacon URLs checked monthly
- DOI resolution verified quarterly

### 6.2 Audit Log

All audits logged to `beacon_registry/AUDIT_LOG.jsonl` (append-only).

---

## 7. Failure Modes Prevented

| Risk | Prevention |
|------|------------|
| Beacon hijacking | Cryptographic signatures required |
| Retroactive modification | Append-only + hash chain |
| Semantic drift | No-interpretation rule |
| AI-generated beacons | Human authorization required |
| Namespace collision | Reserved ranges + sequential IDs |

---

## 8. Legal Statement

The Beacon Registry and all registered artifacts are owned by:

- **N1 Intelligence** (Paul Desai)
- Goa, India

All rights reserved. Beacons are citation anchors, not licenses.
Use of Beacon IDs in citations does not grant rights to underlying artifacts.

---

## 9. Lock Signature

```
GOVERNANCE LOCK v1.0
Created: 2026-01-24T01:30:00+05:30
Owner: Paul Desai / N1 Intelligence
System: Antigravity (Execution Twin)

This document is LOCKED.
Modifications require new version and human signature.
```

---

# LOCK CHECKPOINT

Registry hash at freeze:

```
# To be computed after final registry commit
CHECKPOINT_PENDING
```

---

⟡ **No one can mess with this later.**
