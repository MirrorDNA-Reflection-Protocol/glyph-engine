"""
⟡ Glyph Engine - Main orchestrator

The central control system that:
1. Receives typed input
2. Encodes to glyph tokens
3. Validates transitions via scrolls
4. Executes allowed mutations
5. Audits everything
6. Outputs text and logs (never raw glyphs)

This is a CONTROL SYSTEM, not a memory system.
"""

from typing import Dict, Optional, List, Any, Tuple
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field
import uuid

from glyph_engine.token import GlyphToken, GlyphClass, GlyphVector, GENESIS_GLYPHS
from glyph_engine.input import InputMessage, InputType, CommandVerb, InputParser
from glyph_engine.scroll import Scroll, MutationType, GENESIS_SCROLL, STANDARD_SCROLL
from glyph_engine.validator import ValidatorEngine, ValidatorResult, ValidationAction
from glyph_engine.audit import AuditLog, AuditEventType
from glyph_engine.store import GlyphStore


class EngineConfig(BaseModel):
    """Configuration for the Glyph Engine."""
    vault_path: Path = Field(default=Path.home() / "MirrorDNA-Vault" / "GlyphEngine")
    max_active_glyphs: int = Field(default=100, description="Gap #7.1 - Accretion limit")
    default_ttl_seconds: int = Field(default=86400)
    enable_fast_path: bool = Field(default=True, description="Gap #7.2 - Silent updates")
    require_auth: bool = Field(default=True, description="Gap #2 - Authentication")


class EngineResponse(BaseModel):
    """Response from engine operations."""
    success: bool
    message: str
    glyph_id: Optional[str] = None
    validation_results: Optional[List[Dict[str, Any]]] = None
    text_output: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GlyphEngine:
    """
    Main Glyph Engine orchestrator.
    
    Sits OUTSIDE the LLM. The LLM never reasons in glyphs.
    Glyphs never enter the model as symbols.
    """
    
    def __init__(self, config: Optional[EngineConfig] = None):
        """Initialize the engine with configuration."""
        self.config = config or EngineConfig()
        
        # Initialize subsystems
        self.store = GlyphStore(self.config.vault_path)
        self.audit = AuditLog(self.config.vault_path / "audit.jsonl")
        self.validator = ValidatorEngine()
        
        # Load scrolls
        self._scrolls: Dict[str, Scroll] = {}
        self._load_scrolls()
        
        # Active session
        self.session_id = str(uuid.uuid4())[:8]
        self._glyph_counter = 0
        self._mutation_history: Dict[str, List[Dict[str, Any]]] = {}
    
    def _load_scrolls(self) -> None:
        """Load scrolls from store."""
        for scroll_id in self.store.list_scrolls():
            scroll = self.store.load_scroll(scroll_id)
            if scroll:
                self._scrolls[scroll_id] = scroll
        
        # Ensure defaults exist
        if "S-000" not in self._scrolls:
            self._scrolls["S-000"] = GENESIS_SCROLL
        if "S-001" not in self._scrolls:
            self._scrolls["S-001"] = STANDARD_SCROLL
    
    def _generate_glyph_id(self) -> str:
        """Generate unique glyph ID."""
        self._glyph_counter += 1
        return f"G-{self._glyph_counter:03d}"
    
    def _get_scroll(self, scroll_id: str = "S-001") -> Scroll:
        """Get scroll by ID, default to standard."""
        return self._scrolls.get(scroll_id, STANDARD_SCROLL)
    
    def _check_accretion(self) -> bool:
        """Check if we're at glyph limit (Gap #7.1)."""
        active_count = len(self.store.get_active_glyphs())
        return active_count < self.config.max_active_glyphs
    
    def _run_decay_cycle(self) -> List[str]:
        """Run decay on expired glyphs."""
        expired = self.store.get_expired_glyphs()
        removed = []
        
        for glyph_id, glyph in expired.items():
            self.store.delete_glyph(glyph_id)
            self.audit.create_event(
                event_type=AuditEventType.EXPIRED,
                glyph_id=glyph_id,
                reason=f"TTL expired at {glyph.expires_at}",
                source="system",
                session_id=self.session_id,
                before_state=glyph.model_dump(),
            )
            removed.append(glyph_id)
        
        return removed
    
    # ==================== PUBLIC API ====================
    
    def process_input(self, raw_input: Dict[str, Any]) -> EngineResponse:
        """
        Main entry point - process typed input.
        
        Accepts:
        - {"type": "fact", "payload": {...}}
        - {"type": "state", "payload": {...}}
        - {"type": "command", "verb": "remember", ...}
        """
        try:
            msg = InputParser.parse(raw_input)
        except ValueError as e:
            return EngineResponse(
                success=False,
                message=f"Invalid input: {e}",
            )
        
        # Check authentication (Gap #2)
        if self.config.require_auth and not msg.is_authenticated():
            return EngineResponse(
                success=False,
                message="Authentication required",
            )
        
        # Route by input type
        if msg.input_type == InputType.FACT:
            return self._handle_fact(msg)
        elif msg.input_type == InputType.STATE:
            return self._handle_state(msg)
        elif msg.input_type == InputType.COMMAND:
            return self._handle_command(msg)
        
        return EngineResponse(
            success=False,
            message=f"Unknown input type: {msg.input_type}",
        )
    
    def _handle_fact(self, msg: InputMessage) -> EngineResponse:
        """Handle durable fact input."""
        # Facts are stored in Vault, not as glyphs
        fact_id = f"F-{uuid.uuid4().hex[:8]}"
        content = msg.payload.get("content", "")
        metadata = {
            "source": msg.source,
            "category": msg.payload.get("category", "general"),
        }
        
        self.store.save_fact(fact_id, content, metadata)
        
        return EngineResponse(
            success=True,
            message=f"Fact stored: {fact_id}",
            text_output=f"Recorded fact: {content[:50]}...",
        )
    
    def _handle_state(self, msg: InputMessage) -> EngineResponse:
        """Handle ephemeral session state."""
        # Run decay first
        self._run_decay_cycle()
        
        # Check accretion limit
        if not self._check_accretion():
            return EngineResponse(
                success=False,
                message="Glyph limit reached. Run consolidation or wait for decay.",
            )
        
        # Create state glyph
        glyph_id = self._generate_glyph_id()
        
        # Determine glyph class from payload
        glyph_class = GlyphClass(msg.payload.get("class", "anchor"))
        
        # Build vector from payload or defaults
        vector = GlyphVector(
            x=msg.payload.get("urgency", 0.0),
            y=msg.payload.get("complexity", 0.0),
            z=msg.payload.get("alignment", 0.5),
        )
        
        glyph = GlyphToken(
            glyph_id=glyph_id,
            glyph_class=glyph_class,
            vector=vector,
            intensity=msg.payload.get("intensity", 0.5),
            source=msg.source,
            owner=msg.payload.get("owner", "paul"),
            ttl_seconds=msg.payload.get("ttl", self.config.default_ttl_seconds),
            explanation=msg.payload.get("explanation", "User-declared state"),
            parent_id=msg.payload.get("parent_id"),
        )
        
        # Validate
        results = self.validator.validate_transition(
            validator_id="V-01",
            context={
                "glyph": glyph,
                "mutation": None,
                "source": msg.source,
                "authenticated": msg.is_authenticated(),
                "history": [],
            },
        )
        
        # Check for failures
        failed = [r for r in results if not r.passed]
        if failed:
            self.audit.create_event(
                event_type=AuditEventType.VALIDATION_FAILED,
                glyph_id=glyph_id,
                reason=failed[0].message,
                source=msg.source,
                session_id=self.session_id,
                validation_results=[r.model_dump() for r in results],
            )
            return EngineResponse(
                success=False,
                message=f"Validation failed: {failed[0].message}",
                validation_results=[r.model_dump() for r in results],
            )
        
        # Save glyph
        self.store.save_glyph(glyph)
        
        # Audit
        self.audit.create_event(
            event_type=AuditEventType.CREATED,
            glyph_id=glyph_id,
            reason="State glyph created",
            source=msg.source,
            session_id=self.session_id,
            after_state=glyph.model_dump(),
        )
        
        return EngineResponse(
            success=True,
            message=f"State recorded: {glyph_id}",
            glyph_id=glyph_id,
            text_output=glyph.to_text(),
        )
    
    def _handle_command(self, msg: InputMessage) -> EngineResponse:
        """Handle explicit command verbs."""
        verb = msg.command_verb
        
        if verb == CommandVerb.REMEMBER:
            return self._cmd_remember(msg)
        elif verb == CommandVerb.FORGET:
            return self._cmd_forget(msg)
        elif verb == CommandVerb.REFRAME:
            return self._cmd_reframe(msg)
        elif verb == CommandVerb.AUDIT:
            return self._cmd_audit(msg)
        elif verb == CommandVerb.REFRESH:
            return self._cmd_refresh(msg)
        elif verb == CommandVerb.ATTENUATE:
            return self._cmd_attenuate(msg)
        
        return EngineResponse(
            success=False,
            message=f"Unknown command: {verb}",
        )
    
    def _cmd_remember(self, msg: InputMessage) -> EngineResponse:
        """Create persistent glyph."""
        # Similar to state but with longer TTL
        msg.payload["ttl"] = msg.payload.get("ttl", 604800)  # 7 days
        return self._handle_state(msg)
    
    def _cmd_forget(self, msg: InputMessage) -> EngineResponse:
        """Remove glyph (logged, visible deletion)."""
        glyph_id = msg.target_glyph_id
        glyph = self.store.load_glyph(glyph_id)
        
        if glyph is None:
            return EngineResponse(
                success=False,
                message=f"Glyph not found: {glyph_id}",
            )
        
        # Delete and audit
        self.store.delete_glyph(glyph_id)
        self.audit.create_event(
            event_type=AuditEventType.FORGOTTEN,
            glyph_id=glyph_id,
            reason=msg.payload.get("reason", "User requested forget"),
            source=msg.source,
            session_id=self.session_id,
            before_state=glyph.model_dump(),
        )
        
        return EngineResponse(
            success=True,
            message=f"Forgot: {glyph_id}",
            glyph_id=glyph_id,
            text_output=f"Removed glyph: {glyph.explanation}",
        )
    
    def _cmd_reframe(self, msg: InputMessage) -> EngineResponse:
        """Transform glyph."""
        glyph_id = msg.target_glyph_id
        glyph = self.store.load_glyph(glyph_id)
        
        if glyph is None:
            return EngineResponse(
                success=False,
                message=f"Glyph not found: {glyph_id}",
            )
        
        before_state = glyph.model_dump()
        
        # Apply reframe
        if "class" in msg.payload:
            glyph.glyph_class = GlyphClass(msg.payload["class"])
        if "explanation" in msg.payload:
            glyph.explanation = msg.payload["explanation"]
        if "intensity" in msg.payload:
            glyph.intensity = msg.payload["intensity"]
        
        # Validate transformation
        scroll = self._get_scroll()
        if not scroll.is_mutation_allowed(MutationType.TRANSFORM):
            return EngineResponse(
                success=False,
                message="Transform not allowed in current scroll",
            )
        
        # Save and audit
        self.store.save_glyph(glyph)
        self.audit.create_event(
            event_type=AuditEventType.MUTATED,
            glyph_id=glyph_id,
            reason="Reframe command",
            source=msg.source,
            session_id=self.session_id,
            before_state=before_state,
            after_state=glyph.model_dump(),
        )
        
        return EngineResponse(
            success=True,
            message=f"Reframed: {glyph_id}",
            glyph_id=glyph_id,
            text_output=glyph.to_text(),
        )
    
    def _cmd_audit(self, msg: InputMessage) -> EngineResponse:
        """Generate audit report."""
        if msg.target_glyph_id:
            # Specific glyph history (Gap #3 - archaeology)
            history = self.audit.reconstruct_glyph_history(msg.target_glyph_id)
            return EngineResponse(
                success=True,
                message=f"Audit for {msg.target_glyph_id}",
                text_output=f"Glyph history: {history['total_events']} events, created: {history.get('creation_event', 'unknown')}",
            )
        else:
            # Full summary
            summary = self.audit.generate_summary()
            store_stats = self.store.get_stats()
            
            report = f"""
⟡ GLYPH ENGINE AUDIT REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Session: {self.session_id}
Active Glyphs: {store_stats['active_glyphs']}
Expired: {store_stats['expired_glyphs']}
Total Events: {summary['total_events']}
Rejections: {summary['rejected_count']}
Validation Failures: {summary['validation_failures']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            return EngineResponse(
                success=True,
                message="Audit complete",
                text_output=report.strip(),
            )
    
    def _cmd_refresh(self, msg: InputMessage) -> EngineResponse:
        """Extend glyph TTL."""
        glyph_id = msg.target_glyph_id
        glyph = self.store.load_glyph(glyph_id)
        
        if glyph is None:
            return EngineResponse(
                success=False,
                message=f"Glyph not found: {glyph_id}",
            )
        
        before_state = glyph.model_dump()
        additional = msg.payload.get("seconds", 86400)
        glyph.refresh(additional)
        
        self.store.save_glyph(glyph)
        self.audit.create_event(
            event_type=AuditEventType.REFRESHED,
            glyph_id=glyph_id,
            reason=f"TTL extended by {additional} seconds",
            source=msg.source,
            session_id=self.session_id,
            before_state=before_state,
            after_state=glyph.model_dump(),
        )
        
        return EngineResponse(
            success=True,
            message=f"Refreshed: {glyph_id}",
            glyph_id=glyph_id,
            text_output=glyph.to_text(),
        )
    
    def _cmd_attenuate(self, msg: InputMessage) -> EngineResponse:
        """Reduce glyph intensity."""
        glyph_id = msg.target_glyph_id
        glyph = self.store.load_glyph(glyph_id)
        
        if glyph is None:
            return EngineResponse(
                success=False,
                message=f"Glyph not found: {glyph_id}",
            )
        
        before_state = glyph.model_dump()
        factor = msg.payload.get("factor", 0.9)
        glyph.attenuate(factor)
        
        self.store.save_glyph(glyph)
        self.audit.create_event(
            event_type=AuditEventType.MUTATED,
            glyph_id=glyph_id,
            reason=f"Attenuated by factor {factor}",
            source=msg.source,
            session_id=self.session_id,
            before_state=before_state,
            after_state=glyph.model_dump(),
        )
        
        return EngineResponse(
            success=True,
            message=f"Attenuated: {glyph_id}",
            glyph_id=glyph_id,
            text_output=glyph.to_text(),
        )
    
    # ==================== STATE QUERIES ====================
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get current engine state for MirrorGate integration."""
        active = self.store.get_active_glyphs()
        
        return {
            "session_id": self.session_id,
            "active_glyph_count": len(active),
            "glyph_limit": self.config.max_active_glyphs,
            "glyphs": [
                {
                    "id": g.glyph_id,
                    "class": g.glyph_class.value,
                    "intensity": g.intensity,
                    "expires": g.expires_at.isoformat() if g.expires_at else None,
                    "explain": g.explanation,
                }
                for g in active.values()
            ],
            "vault_path": str(self.config.vault_path),
        }
    
    def get_glyph_text(self, glyph_id: str) -> Optional[str]:
        """Get plain text representation of glyph."""
        glyph = self.store.load_glyph(glyph_id)
        if glyph:
            return glyph.to_text()
        return None
    
    def get_all_text(self) -> str:
        """Get all glyphs as text (for LLM context injection)."""
        active = self.store.get_active_glyphs()
        lines = ["⟡ ACTIVE GLYPHS:"]
        for glyph in sorted(active.values(), key=lambda g: g.intensity, reverse=True):
            lines.append(f"  • {glyph.to_text()}")
        return "\n".join(lines)


# ==================== CONVENIENCE FACTORY ====================

def create_engine(
    vault_path: Optional[Path] = None,
    **config_kwargs
) -> GlyphEngine:
    """Create engine with sensible defaults."""
    config = EngineConfig(
        vault_path=vault_path or Path.home() / "MirrorDNA-Vault" / "GlyphEngine",
        **config_kwargs,
    )
    return GlyphEngine(config)
