"""
⟡ Glyph Token - Core symbolic unit

Aligned with LingOS Kernel v0.1 Glyph Types:
- ANCHOR (LIT): Static identity/context anchors
- MUTATION (OP): State transition operators
- WARNING (CTL): Flow control and alerts
- AUDIT (META): Reflective/introspective markers
- CONSENT (CNS): User approval gates

Vector semantics (mechanistic, not semantic embeddings):
- X: Urgency/TTL pressure (-1 to 1)
- Y: Complexity/Load (-1 to 1)
- Z: Alignment/Stability (-1 to 1)
"""

from enum import Enum
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import hashlib
import json


class GlyphClass(str, Enum):
    """Glyph classification aligned with LingOS types."""
    ANCHOR = "anchor"       # LIT: Static context
    MUTATION = "mutation"   # OP: State changes
    WARNING = "warning"     # CTL: Flow control
    AUDIT = "audit"         # META: Reflection
    CONSENT = "consent"     # CNS: Approval gates


class GlyphVector(BaseModel):
    """
    Mechanistic 3D vector for glyph state.
    NOT semantic embeddings - deterministic axes.
    """
    x: float = Field(default=0.0, ge=-1.0, le=1.0, description="Urgency/TTL pressure")
    y: float = Field(default=0.0, ge=-1.0, le=1.0, description="Complexity/Load")
    z: float = Field(default=0.0, ge=-1.0, le=1.0, description="Alignment/Stability")
    
    def magnitude(self) -> float:
        return (self.x**2 + self.y**2 + self.z**2) ** 0.5


class GlyphToken(BaseModel):
    """
    Core glyph token - the atomic unit of the Glyph Engine.
    
    Key invariants:
    - Every glyph has a TTL (no unbounded persistence)
    - Every glyph has an owner (user-initiated or system rule)
    - Glyphs encode directional state, not meaning
    - Glyphs never represent identity
    """
    glyph_id: str = Field(..., description="Unique identifier (e.g., G-042)")
    glyph_class: GlyphClass = Field(..., description="Classification")
    vector: GlyphVector = Field(default_factory=GlyphVector)
    intensity: float = Field(default=0.5, ge=0.0, le=1.0, description="Strength 0-1")
    
    # Governance
    source: str = Field(default="user", description="Origin: user, system, rule")
    owner: str = Field(default="paul", description="Owner identity")
    ttl_seconds: int = Field(default=86400, ge=1, description="Time-to-live in seconds")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    # Explain (required for every glyph)
    explanation: str = Field(..., max_length=200, description="One-sentence explanation")
    
    # Linkage
    parent_id: Optional[str] = None
    
    def model_post_init(self, __context) -> None:
        """Set expiry based on TTL."""
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(seconds=self.ttl_seconds)
    
    def is_expired(self) -> bool:
        """Check if glyph has exceeded TTL."""
        return datetime.utcnow() > self.expires_at
    
    def refresh(self, additional_seconds: int = 86400) -> None:
        """Extend TTL (user action only)."""
        self.ttl_seconds += additional_seconds
        self.expires_at = datetime.utcnow() + timedelta(seconds=self.ttl_seconds)
    
    def attenuate(self, factor: float = 0.9) -> None:
        """Reduce intensity (decay operation)."""
        self.intensity = max(0.0, self.intensity * factor)
    
    def checksum(self) -> str:
        """SHA-256 hash for integrity verification."""
        data = f"{self.glyph_id}:{self.glyph_class.value}:{self.intensity}:{self.created_at.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def to_text(self) -> str:
        """Resolve to plain text (governance requirement)."""
        return f"[{self.glyph_class.value.upper()}] {self.explanation} (intensity: {self.intensity:.2f}, expires: {self.expires_at.isoformat()})"


# ==================== GENESIS GLYPHS ====================
# Pre-defined bootstrap glyphs for cold start (Gap #1 mitigation)

GENESIS_GLYPHS = {
    "G-000": GlyphToken(
        glyph_id="G-000",
        glyph_class=GlyphClass.ANCHOR,
        vector=GlyphVector(x=0.0, y=0.0, z=1.0),
        intensity=1.0,
        source="system",
        owner="paul",
        ttl_seconds=31536000,  # 1 year
        explanation="Genesis anchor - system bootstrap state.",
    ),
    "G-001": GlyphToken(
        glyph_id="G-001",
        glyph_class=GlyphClass.CONSENT,
        vector=GlyphVector(x=0.0, y=0.0, z=1.0),
        intensity=1.0,
        source="system",
        owner="paul",
        ttl_seconds=86400,  # 24 hours
        explanation="Default consent gate - requires explicit user approval.",
    ),
}
