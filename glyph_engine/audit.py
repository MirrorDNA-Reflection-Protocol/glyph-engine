"""
⟡ Audit Layer - Append-only event logging

Every mutation is recorded. Append-only. No silent writes.
Forgetting is visible.

Gap #3 mitigation: Includes "archaeology" helpers for reconstructing
why current state is what it is.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field
import json


class AuditEventType(str, Enum):
    """Types of auditable events."""
    CREATED = "created"
    MUTATED = "mutated"
    DECAYED = "decayed"
    EXPIRED = "expired"
    REJECTED = "rejected"
    REFRESHED = "refreshed"
    FORGOTTEN = "forgotten"
    VALIDATED = "validated"
    VALIDATION_FAILED = "validation_failed"


class AuditEvent(BaseModel):
    """
    Single audit event - immutable record.
    
    Every field is explicit. No inference.
    """
    event_id: str = Field(..., description="Unique event ID")
    event_type: AuditEventType
    glyph_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Context
    source: str = Field(default="user")
    session_id: Optional[str] = None
    
    # Details
    reason: str = Field(..., description="Why this event occurred")
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    
    # Validation context
    validator_id: Optional[str] = None
    validation_results: Optional[List[Dict[str, Any]]] = None
    
    def to_jsonl(self) -> str:
        """Serialize to JSONL format."""
        return self.model_dump_json() + "\n"


class AuditLog:
    """
    Append-only audit log.
    
    Stores events in JSONL format for easy replay and analysis.
    Gap #6 consideration: No "ephemeral" mode - everything is logged.
    """
    
    def __init__(self, log_path: Path):
        """Initialize with path to JSONL file."""
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._event_counter = 0
    
    def append(self, event: AuditEvent) -> None:
        """Append event to log (never overwrite)."""
        with open(self.log_path, "a") as f:
            f.write(event.to_jsonl())
    
    def create_event(
        self,
        event_type: AuditEventType,
        glyph_id: str,
        reason: str,
        source: str = "user",
        session_id: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        validator_id: Optional[str] = None,
        validation_results: Optional[List[Dict[str, Any]]] = None,
    ) -> AuditEvent:
        """Create and append an audit event."""
        self._event_counter += 1
        event = AuditEvent(
            event_id=f"A-{self._event_counter:06d}",
            event_type=event_type,
            glyph_id=glyph_id,
            reason=reason,
            source=source,
            session_id=session_id,
            before_state=before_state,
            after_state=after_state,
            validator_id=validator_id,
            validation_results=validation_results,
        )
        self.append(event)
        return event
    
    def read_all(self) -> List[AuditEvent]:
        """Read all events from log."""
        if not self.log_path.exists():
            return []
        
        events = []
        with open(self.log_path, "r") as f:
            for line in f:
                if line.strip():
                    events.append(AuditEvent.model_validate_json(line))
        return events
    
    def query_by_glyph(self, glyph_id: str) -> List[AuditEvent]:
        """Get all events for a specific glyph (Gap #3 - archaeology)."""
        return [e for e in self.read_all() if e.glyph_id == glyph_id]
    
    def query_by_type(self, event_type: AuditEventType) -> List[AuditEvent]:
        """Get all events of a specific type."""
        return [e for e in self.read_all() if e.event_type == event_type]
    
    def query_by_timerange(
        self,
        start: datetime,
        end: Optional[datetime] = None,
    ) -> List[AuditEvent]:
        """Get events within time range."""
        if end is None:
            end = datetime.utcnow()
        return [e for e in self.read_all() if start <= e.timestamp <= end]
    
    def reconstruct_glyph_history(self, glyph_id: str) -> Dict[str, Any]:
        """
        Reconstruct complete history of a glyph.
        
        Gap #3 - Glyph Archaeology: Answers "why is this glyph in this state?"
        """
        events = self.query_by_glyph(glyph_id)
        
        history = {
            "glyph_id": glyph_id,
            "total_events": len(events),
            "creation_event": None,
            "mutations": [],
            "current_state": None,
            "timeline": [],
        }
        
        for event in sorted(events, key=lambda e: e.timestamp):
            timeline_entry = {
                "event_id": event.event_id,
                "type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "reason": event.reason,
                "source": event.source,
            }
            history["timeline"].append(timeline_entry)
            
            if event.event_type == AuditEventType.CREATED:
                history["creation_event"] = timeline_entry
            elif event.event_type == AuditEventType.MUTATED:
                history["mutations"].append(timeline_entry)
            
            if event.after_state:
                history["current_state"] = event.after_state
        
        return history
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate audit summary for reporting."""
        events = self.read_all()
        
        summary = {
            "total_events": len(events),
            "by_type": {},
            "by_glyph": {},
            "rejected_count": 0,
            "validation_failures": 0,
        }
        
        for event in events:
            # Count by type
            type_key = event.event_type.value
            summary["by_type"][type_key] = summary["by_type"].get(type_key, 0) + 1
            
            # Count by glyph
            summary["by_glyph"][event.glyph_id] = summary["by_glyph"].get(event.glyph_id, 0) + 1
            
            # Count failures
            if event.event_type == AuditEventType.REJECTED:
                summary["rejected_count"] += 1
            if event.event_type == AuditEventType.VALIDATION_FAILED:
                summary["validation_failures"] += 1
        
        return summary
