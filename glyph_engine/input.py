"""
⟡ Input Layer - Typed input processing

Accepted input types (explicit, typed):
- FACT: Durable, user-authored, stored in Vault
- STATE: Session state, ephemeral, auto-decays
- COMMAND: Explicit verbs (remember, forget, reframe, audit)

No implicit inference - all inputs must be explicitly typed.
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class InputType(str, Enum):
    """Explicit input classification."""
    FACT = "fact"       # Durable, Vault-stored
    STATE = "state"     # Ephemeral session
    COMMAND = "command" # Explicit verbs


class CommandVerb(str, Enum):
    """Allowed command verbs (no implicit inference)."""
    REMEMBER = "remember"   # Create/persist glyph
    FORGET = "forget"       # Remove glyph (logged)
    REFRAME = "reframe"     # Transform glyph
    AUDIT = "audit"         # Request audit report
    REFRESH = "refresh"     # Extend TTL
    ATTENUATE = "attenuate" # Reduce intensity


class InputMessage(BaseModel):
    """
    Typed input to the Glyph Engine.
    
    Every input must have an explicit type.
    Commands require explicit verbs.
    """
    input_type: InputType = Field(..., description="Type of input")
    payload: Dict[str, Any] = Field(default_factory=dict)
    source: str = Field(default="user", description="Origin of input")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Optional command specifics
    command_verb: Optional[CommandVerb] = None
    target_glyph_id: Optional[str] = None
    
    # Authentication (Gap #2 mitigation)
    auth_token: Optional[str] = None
    session_id: Optional[str] = None
    
    def is_authenticated(self) -> bool:
        """Check if input has valid auth context."""
        # In production, this would verify the token
        return self.auth_token is not None or self.source == "system"
    
    def validate_command(self) -> bool:
        """Ensure commands have required fields."""
        if self.input_type == InputType.COMMAND:
            if self.command_verb is None:
                return False
            if self.command_verb in [CommandVerb.FORGET, CommandVerb.REFRAME, 
                                      CommandVerb.REFRESH, CommandVerb.ATTENUATE]:
                return self.target_glyph_id is not None
        return True


class InputParser:
    """
    Parse raw input into typed InputMessage.
    
    Strict parsing - rejects ambiguous input.
    """
    
    @staticmethod
    def parse(raw: Dict[str, Any]) -> InputMessage:
        """
        Parse raw dict into InputMessage.
        
        Raises ValueError for invalid/ambiguous input.
        """
        if "type" not in raw:
            raise ValueError("Input must have explicit 'type' field")
        
        input_type = InputType(raw["type"])
        
        msg = InputMessage(
            input_type=input_type,
            payload=raw.get("payload", {}),
            source=raw.get("source", "user"),
            timestamp=datetime.fromisoformat(raw["timestamp"]) if "timestamp" in raw else datetime.utcnow(),
            command_verb=CommandVerb(raw["verb"]) if "verb" in raw else None,
            target_glyph_id=raw.get("target"),
            auth_token=raw.get("auth_token"),
            session_id=raw.get("session_id"),
        )
        
        if not msg.validate_command():
            raise ValueError(f"Invalid command: missing required fields for {msg.command_verb}")
        
        return msg
