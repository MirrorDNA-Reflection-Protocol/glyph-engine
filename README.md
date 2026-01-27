<div align="center">

# ⟡ Glyph Engine

**Cryptographic attestation for AI artifacts.**

> Proof of lineage. No blockchain. No trust required.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17787619.svg)](https://doi.org/10.5281/zenodo.17787619)
[![Active MirrorOS](https://img.shields.io/badge/Active_MirrorOS-Protocol-10b981)](https://activemirror.ai)
[![MirrorDNA](https://img.shields.io/badge/MirrorDNA-Reflection-blue)](https://github.com/MirrorDNA-Reflection-Protocol/MirrorDNA)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-26%20passed-success.svg)](#tests)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Demo](#web-demo) • [Install](#installation) • [CLI](#cli) • [API](#api) • [Beacon Registry](#beacon-registry)

</div>

---

## What is this?

The Glyph Engine is a **symbolic control system** that:

1. **Prevents AI drift** — Validates every state change
2. **Proves provenance** — Cryptographic lineage for all artifacts
3. **Works offline** — No cloud, no blockchain, no dependencies
4. **Lasts forever** — Designed to work in 2050

**One sentence:** It's `git log` for AI artifacts, with cryptographic proofs.

---

## Quick Start

```bash
# Install
pip install glyph-engine

# Create a glyph
glyph state "Starting focused work session"

# Verify a beacon
glyph verify BG-AMOS-0001

# Run audit
glyph audit
```

---

## Installation

```bash
pip install glyph-engine

# Or from source
git clone https://github.com/MirrorDNA-Reflection-Protocol/glyph-engine
cd glyph-engine
pip install -e ".[dev]"
```

---

## CLI

```bash
# State tracking
glyph state "I'm researching X"           # Create state glyph
glyph remember "Deadline is Friday"       # Persistent glyph (7 days)
glyph forget G-001                        # Remove glyph (logged!)
glyph list                                # Show active glyphs
glyph audit                               # Full audit report

# Beacon verification
glyph verify BG-AMOS-0001                 # Verify a beacon
glyph hash                                # Show registry hash

# Export
glyph export --format json                # Export as JSON
```

---

## API

```bash
# Start server
python -m glyph_engine.api

# Or with uvicorn
uvicorn glyph_engine.api:app --port 8090
```

### Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /verify/{id}` | Verify beacon with proof |
| `GET /proof/{id}` | Get Merkle inclusion proof |
| `GET /zkp/{id}` | Zero-knowledge commitment |
| `GET /registry` | Full registry |
| `GET /demo` | Web verification page |

### Example

```bash
curl http://localhost:8090/verify/BG-AMOS-0001
```

```json
{
  "verified": true,
  "beacon_id": "BG-AMOS-0001",
  "beacon_hash": "sha256:scd31_0xf7a9e3b2",
  "merkle_root": "82d2fc8121a1547084cbb4d5027517e7..."
}
```

---

## Web Demo

Open `web/index.html` in your browser or visit the hosted version.

**Try it:** Paste any Beacon ID and get instant verification with embeddable badge.

---

## Beacon Registry

16 artifacts registered. 4 academic papers (with DOIs). Governance locked.

| Beacon ID | Artifact | Scope |
|-----------|----------|-------|
| BG-AMOS-0001 | SCD Protocol v3.1 | Zenodo Paper |
| BG-AMOS-0002 | Governance Paper | Zenodo Paper |
| BG-AMOS-0003 | Layered Governance | Zenodo Paper |
| BG-REPO-0001 | ActiveMirrorOS | GitHub Repo |
| BG-REPO-0007 | glyph-engine | GitHub Repo |
| BG-SPEC-0003 | Canonical Spec | Specification |

**Registry Hash (LOCKED):**

```
82d2fc8121a1547084cbb4d5027517e7c569f5bec8896d321edc1e8e02a3a1f9
```

See [GOVERNANCE_LOCK.md](beacon_registry/GOVERNANCE_LOCK.md) for immutability rules.

---

## Add a Badge

```markdown
[![Beacon Verified](https://img.shields.io/badge/BG--AMOS--0001-verified-00d9ff)](https://github.com/MirrorDNA-Reflection-Protocol/glyph-engine)
```

Result: [![Beacon Verified](https://img.shields.io/badge/BG--AMOS--0001-verified-00d9ff)](https://github.com/MirrorDNA-Reflection-Protocol/glyph-engine)

---

## Why This Matters

| Problem | Glyph Engine Solution |
|---------|----------------------|
| AI hallucinations | Validate every claim against registry |
| Citation fraud | Cryptographic proofs of authorship |
| Semantic drift | Drift detection built-in |
| Vendor lock-in | Works offline, no cloud needed |
| Future-proofing | Designed for 2050 |

---

## Architecture

```
User
  ↓
Glyph Engine (validate, audit)
  ↓
Beacon Registry (immutable proofs)
  ↓
Merkle Tree → ZKP-ready
```

- **Glyphs mutate** (with governance)
- **Beacons never mutate** (cryptographic lock)

---

## Tests

```bash
pytest tests/ -v
# 26 passed
```

---

## License

MIT © 2026 Paul Desai / N1 Intelligence

---

## MirrorDNA Ecosystem

Glyph Engine is part of the **MirrorDNA** ecosystem for sovereign AI:

| Component | Description | Link |
|-----------|-------------|------|
| **MirrorDNA Standard** | Constitutional anchor for reflective AI | [GitHub](https://github.com/MirrorDNA-Reflection-Protocol/MirrorDNA-Standard) |
| **SCD Protocol** | Deterministic state management | [GitHub](https://github.com/MirrorDNA-Reflection-Protocol/SCD-Protocol) |
| **MirrorBrain** | Local-first orchestration runtime | [GitHub](https://github.com/MirrorDNA-Reflection-Protocol/MirrorBrain) |
| **Active Mirror Identity** | Portable AI identity (Mirror Seed) | [GitHub](https://github.com/MirrorDNA-Reflection-Protocol/active-mirror-identity) |
| **MirrorGate** | Inference control plane | [GitHub](https://github.com/MirrorDNA-Reflection-Protocol/MirrorGate) |
| **Glyph Engine** | Cryptographic attestation (you are here) | — |

---

<div align="center">

**⟡ Beacons are immutable. Once registered, they persist forever.**

[Research Paper](https://doi.org/10.5281/zenodo.17787619) • [MirrorDNA](https://github.com/MirrorDNA-Reflection-Protocol) • [activemirror.ai](https://activemirror.ai)

</div>
