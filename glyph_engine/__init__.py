"""
⟡ Glyph Engine v1.0

Symbolic control and continuity interface for human-AI interaction.
State encoding layer, governed mutation interface, drift detection, and audit system.

Aligned with:
- LingOS Kernel v0.1 (Glyph types, Chains, Policies, Consent)
- Beacon Glyph SDK (Cryptographic Claims)
- MirrorDNA Vault (Sovereign Storage)

© 2026 Paul Desai / N1 Intelligence
"""

from glyph_engine.token import GlyphToken, GlyphClass
from glyph_engine.input import InputMessage, InputType, CommandVerb
from glyph_engine.scroll import Scroll, ScrollTransition
from glyph_engine.validator import Validator, ValidatorResult
from glyph_engine.engine import GlyphEngine, create_engine
from glyph_engine.audit import AuditLog, AuditEvent
from glyph_engine.store import GlyphStore

__version__ = "1.0.0"
__author__ = "Paul Desai"

__all__ = [
    "GlyphToken",
    "GlyphClass",
    "InputMessage",
    "InputType",
    "CommandVerb",
    "Scroll",
    "ScrollTransition",
    "Validator",
    "ValidatorResult",
    "GlyphEngine",
    "create_engine",
    "AuditLog",
    "AuditEvent",
    "GlyphStore",
]
