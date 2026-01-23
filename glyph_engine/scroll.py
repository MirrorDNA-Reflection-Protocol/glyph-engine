"""
⟡ Scroll Pathways - Allowed state transitions

Scrolls are validated sequences of glyph transitions.
They define allowed state evolution (FSM for AI behavior).

Key properties:
- Scrolls do NOT execute logic
- They define what transitions are LEGAL
- They prevent illegal states (e.g., recursive amplification)
"""

from enum import Enum
from typing import List, Set, Optional
from pydantic import BaseModel, Field


class MutationType(str, Enum):
    """Allowed mutation operations on glyphs."""
    ROTATE = "rotate"         # Change vector direction
    ATTENUATE = "attenuate"   # Reduce intensity
    AMPLIFY = "amplify"       # Increase intensity (often forbidden)
    TRANSFORM = "transform"   # Change class
    REFRESH = "refresh"       # Extend TTL
    DECAY = "decay"           # Natural TTL reduction


class ScrollTransition(BaseModel):
    """
    Single allowed transition in a scroll.
    
    from_glyph -> to_glyph via mutation_type
    """
    from_glyph_id: str
    to_glyph_id: str
    mutation_type: MutationType
    requires_consent: bool = False
    max_intensity_delta: float = Field(default=0.5, ge=0.0, le=1.0)


class Scroll(BaseModel):
    """
    A validated sequence of allowed glyph transitions.
    
    Scrolls are the FSM definition for the Glyph Engine.
    """
    scroll_id: str = Field(..., description="Unique identifier (e.g., S-019)")
    name: str = Field(..., description="Human-readable name")
    sequence: List[str] = Field(default_factory=list, description="Ordered glyph IDs")
    
    # Allowed/forbidden operations
    allowed_mutations: Set[MutationType] = Field(default_factory=lambda: {
        MutationType.ROTATE,
        MutationType.ATTENUATE,
        MutationType.REFRESH,
        MutationType.DECAY,
    })
    forbidden_mutations: Set[MutationType] = Field(default_factory=lambda: {
        MutationType.AMPLIFY,  # Recursive amplification prevention
    })
    
    # Transitions
    transitions: List[ScrollTransition] = Field(default_factory=list)
    
    # Governance
    validator_id: str = Field(default="V-00", description="Validator to use")
    max_active_glyphs: int = Field(default=50, description="Gap #7.1 - Accretion prevention")
    
    def is_mutation_allowed(self, mutation: MutationType) -> bool:
        """Check if mutation type is allowed by this scroll."""
        if mutation in self.forbidden_mutations:
            return False
        return mutation in self.allowed_mutations
    
    def can_transition(self, from_id: str, to_id: str, mutation: MutationType) -> bool:
        """Check if a specific transition is valid."""
        if not self.is_mutation_allowed(mutation):
            return False
        
        for t in self.transitions:
            if t.from_glyph_id == from_id and t.to_glyph_id == to_id:
                if t.mutation_type == mutation:
                    return True
        
        # If no explicit transitions defined, allow within mutation rules
        return len(self.transitions) == 0


# ==================== GENESIS SCROLLS ====================
# Pre-defined bootstrap scrolls

GENESIS_SCROLL = Scroll(
    scroll_id="S-000",
    name="Genesis Scroll",
    sequence=["G-000", "G-001"],
    allowed_mutations={
        MutationType.ROTATE,
        MutationType.ATTENUATE,
        MutationType.REFRESH,
        MutationType.DECAY,
    },
    forbidden_mutations={
        MutationType.AMPLIFY,
        MutationType.TRANSFORM,  # Cannot transform genesis glyphs
    },
    validator_id="V-00",
    max_active_glyphs=50,
)

STANDARD_SCROLL = Scroll(
    scroll_id="S-001",
    name="Standard Session Scroll",
    sequence=[],
    allowed_mutations={
        MutationType.ROTATE,
        MutationType.ATTENUATE,
        MutationType.AMPLIFY,  # Allowed with limits
        MutationType.REFRESH,
        MutationType.DECAY,
        MutationType.TRANSFORM,
    },
    forbidden_mutations=set(),
    validator_id="V-01",
    max_active_glyphs=100,
)
