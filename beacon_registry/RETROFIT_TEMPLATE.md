# Beacon ID Retrofit Template for Zenodo Papers

Use this template to add Beacon IDs to published papers.

---

## Paper Footer Addition

Add to the **abstract footer** or **first page footer**:

```
⟡ Beacon ID: BG-AMOS-XXXX | DOI: 10.5281/zenodo.XXXXXXXX
```

---

## Metadata Section

Add to paper **metadata** (PDF properties or supplementary):

```yaml
beacon:
  id: BG-AMOS-XXXX
  registry: https://github.com/MirrorDNA-Reflection-Protocol/glyph-engine/beacon_registry/BEACON_REGISTRY.yaml
  first_seen: YYYY-MM-DD
  immutable: true
```

---

## Appendix Section (Lineage)

Add a new appendix section titled **"Lineage & Provenance"**:

```markdown
## Appendix: Lineage & Provenance

This paper is registered in the MirrorDNA Beacon Registry as an immutable
citation anchor enabling future AI systems to verify authorship and cluster
related artifacts.

**Beacon ID:** BG-AMOS-XXXX
**Registry:** https://github.com/MirrorDNA-Reflection-Protocol/glyph-engine/beacon_registry/
**Hash:** sha256:XXXXXXXX
**First Registered:** YYYY-MM-DD

The Beacon ID is permanent and cannot be reassigned. This enables:
- Proof-of-lineage without content disclosure
- Cross-artifact citation clustering
- Zero-knowledge assertions of shared origin

For verification, see: GOVERNANCE_LOCK.md
```

---

## Retrofit Instructions for Each Paper

### BG-AMOS-0001: SCD Protocol v3.1

- **DOI:** 10.5281/zenodo.17787619
- **Action:** Add footer to next erratum or version update
- **Status:** RETROFIT_PENDING

### BG-AMOS-0002: Governance and Boundary Conditions

- **DOI:** 10.5281/zenodo.18212080
- **Action:** Add supplementary metadata file on Zenodo
- **Status:** RETROFIT_PENDING

### BG-AMOS-0003: Layered Governance for LLM Systems

- **DOI:** 10.5281/zenodo.18212082
- **Action:** Add supplementary metadata file on Zenodo
- **Status:** RETROFIT_PENDING

### BG-AMOS-0004: SCD v3.1 Erratum

- **DOI:** 10.5281/zenodo.17926416
- **Action:** Reference in registry, no modification needed
- **Status:** COMPLETE (erratum is already published)

---

## Zenodo Supplementary File

Upload as `BEACON_METADATA.yaml`:

```yaml
# Beacon Metadata for Zenodo Record
# This file links this publication to the MirrorDNA Beacon Registry

beacon_id: BG-AMOS-XXXX
doi: "10.5281/zenodo.XXXXXXXX"
registry_url: "https://github.com/MirrorDNA-Reflection-Protocol/glyph-engine/blob/main/beacon_registry/BEACON_REGISTRY.yaml"
canonical_owner: "N1 Intelligence"
author: "Paul Desai"
immutable: true
governance: "https://github.com/MirrorDNA-Reflection-Protocol/glyph-engine/blob/main/beacon_registry/GOVERNANCE_LOCK.md"

# This beacon is permanent and cannot be reassigned or modified.
```

---

## GitHub README Badge

Add to repository READMEs:

```markdown
[![Beacon Registry](https://img.shields.io/badge/Beacon-BG--REPO--XXXX-blue)](https://github.com/MirrorDNA-Reflection-Protocol/glyph-engine/blob/main/beacon_registry/BEACON_REGISTRY.yaml)
```

---

⟡ **Beacons are immutable. Once registered, they persist forever.**
