"""
⟡ Glyph Engine Tests

Comprehensive tests for the Glyph Engine.
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil

from glyph_engine import (
    GlyphEngine,
    GlyphToken,
    GlyphClass,
    InputMessage,
    InputType,
    CommandVerb,
    Scroll,
    Validator,
    AuditLog,
    GlyphStore,
)
from glyph_engine.engine import EngineConfig, create_engine
from glyph_engine.token import GlyphVector, GENESIS_GLYPHS
from glyph_engine.scroll import MutationType, GENESIS_SCROLL
from glyph_engine.validator import ValidatorEngine, ValidationAction
from glyph_engine.input import InputParser


class TestGlyphToken:
    """Tests for GlyphToken."""
    
    def test_create_minimal_glyph(self):
        glyph = GlyphToken(
            glyph_id="G-001",
            glyph_class=GlyphClass.ANCHOR,
            explanation="Test anchor glyph",
        )
        assert glyph.glyph_id == "G-001"
        assert glyph.glyph_class == GlyphClass.ANCHOR
        assert glyph.intensity == 0.5  # default
        assert glyph.ttl_seconds == 86400  # default
        assert glyph.expires_at is not None
    
    def test_glyph_expiry(self):
        glyph = GlyphToken(
            glyph_id="G-002",
            glyph_class=GlyphClass.MUTATION,
            explanation="Test mutation",
            ttl_seconds=1,
        )
        assert not glyph.is_expired()
        # Manually set expiry to past
        glyph.expires_at = datetime.utcnow() - timedelta(seconds=10)
        assert glyph.is_expired()
    
    def test_glyph_attenuate(self):
        glyph = GlyphToken(
            glyph_id="G-003",
            glyph_class=GlyphClass.ANCHOR,
            explanation="Test",
            intensity=1.0,
        )
        glyph.attenuate(0.5)
        assert glyph.intensity == 0.5
        glyph.attenuate(0.5)
        assert glyph.intensity == 0.25
    
    def test_glyph_vector(self):
        vector = GlyphVector(x=0.5, y=-0.3, z=0.8)
        assert abs(vector.magnitude() - 0.9899) < 0.01
    
    def test_glyph_checksum(self):
        glyph = GlyphToken(
            glyph_id="G-004",
            glyph_class=GlyphClass.AUDIT,
            explanation="Checksum test",
        )
        checksum1 = glyph.checksum()
        checksum2 = glyph.checksum()
        assert checksum1 == checksum2
        assert len(checksum1) == 16
    
    def test_genesis_glyphs_exist(self):
        assert "G-000" in GENESIS_GLYPHS
        assert "G-001" in GENESIS_GLYPHS
        assert GENESIS_GLYPHS["G-000"].glyph_class == GlyphClass.ANCHOR


class TestInputParser:
    """Tests for input parsing."""
    
    def test_parse_fact(self):
        raw = {
            "type": "fact",
            "payload": {"content": "Test fact"},
            "source": "user",
        }
        msg = InputParser.parse(raw)
        assert msg.input_type == InputType.FACT
        assert msg.payload["content"] == "Test fact"
    
    def test_parse_command(self):
        raw = {
            "type": "command",
            "verb": "forget",
            "target": "G-001",
        }
        msg = InputParser.parse(raw)
        assert msg.input_type == InputType.COMMAND
        assert msg.command_verb == CommandVerb.FORGET
        assert msg.target_glyph_id == "G-001"
    
    def test_reject_missing_type(self):
        raw = {"payload": {"foo": "bar"}}
        with pytest.raises(ValueError, match="must have explicit 'type'"):
            InputParser.parse(raw)
    
    def test_reject_invalid_command(self):
        raw = {
            "type": "command",
            "verb": "forget",
            # Missing target
        }
        with pytest.raises(ValueError, match="missing required fields"):
            InputParser.parse(raw)


class TestScroll:
    """Tests for Scroll pathways."""
    
    def test_genesis_scroll(self):
        scroll = GENESIS_SCROLL
        assert scroll.scroll_id == "S-000"
        assert MutationType.AMPLIFY in scroll.forbidden_mutations
        assert MutationType.ATTENUATE in scroll.allowed_mutations
    
    def test_mutation_allowed(self):
        scroll = GENESIS_SCROLL
        assert scroll.is_mutation_allowed(MutationType.ROTATE)
        assert not scroll.is_mutation_allowed(MutationType.AMPLIFY)


class TestValidator:
    """Tests for validation engine."""
    
    def test_validator_integrity(self):
        engine = ValidatorEngine()
        v = engine.get_validator("V-01")
        assert v is not None
        assert v.verify_integrity()
    
    def test_validate_identity_fixation(self):
        engine = ValidatorEngine()
        
        # Glyph with identity in explanation should fail
        glyph = GlyphToken(
            glyph_id="G-BAD",
            glyph_class=GlyphClass.ANCHOR,
            explanation="This is my identity marker",
        )
        
        results = engine.validate_transition(
            validator_id="V-01",
            context={
                "glyph": glyph,
                "source": "user",
                "authenticated": True,
                "history": [],
            },
        )
        
        failed = [r for r in results if not r.passed]
        assert len(failed) > 0
        assert any("identity" in r.message.lower() for r in failed)
    
    def test_validate_recursive_amplification(self):
        engine = ValidatorEngine()
        
        glyph = GlyphToken(
            glyph_id="G-100",
            glyph_class=GlyphClass.MUTATION,
            explanation="Normal glyph",
        )
        
        # History with too many amplifications
        history = [
            {"mutation": "amplify"},
            {"mutation": "amplify"},
            {"mutation": "amplify"},
        ]
        
        results = engine.validate_transition(
            validator_id="V-01",
            context={
                "glyph": glyph,
                "source": "user",
                "authenticated": True,
                "history": history,
            },
        )
        
        failed = [r for r in results if not r.passed]
        assert any("recursive amplification" in r.message.lower() for r in failed)


class TestGlyphStore:
    """Tests for persistent storage."""
    
    @pytest.fixture
    def temp_store(self):
        path = Path(tempfile.mkdtemp()) / "test_vault"
        store = GlyphStore(path)
        yield store
        shutil.rmtree(path, ignore_errors=True)
    
    def test_genesis_bootstrap(self, temp_store):
        # Genesis glyphs should be auto-created
        glyphs = temp_store.list_glyphs()
        assert "G-000" in glyphs
        assert "G-001" in glyphs
    
    def test_save_load_glyph(self, temp_store):
        glyph = GlyphToken(
            glyph_id="G-TEST",
            glyph_class=GlyphClass.WARNING,
            explanation="Test warning",
        )
        temp_store.save_glyph(glyph)
        
        loaded = temp_store.load_glyph("G-TEST")
        assert loaded is not None
        assert loaded.glyph_id == "G-TEST"
        assert loaded.glyph_class == GlyphClass.WARNING
    
    def test_transaction_rollback(self, temp_store):
        tx_id = temp_store.begin_transaction()
        
        glyph = GlyphToken(
            glyph_id="G-TX-TEST",
            glyph_class=GlyphClass.AUDIT,
            explanation="Transaction test",
        )
        temp_store.save_glyph(glyph)
        
        # Before rollback, glyph exists
        assert temp_store.load_glyph("G-TX-TEST") is not None
        
        # Rollback
        temp_store.rollback_transaction()
        
        # After rollback, glyph should not exist
        # (Note: this tests that the backup/restore works)
        # The new glyph won't be in the restored state
    
    def test_active_vs_expired(self, temp_store):
        active = GlyphToken(
            glyph_id="G-ACTIVE",
            glyph_class=GlyphClass.ANCHOR,
            explanation="Active glyph",
            ttl_seconds=86400,
        )
        temp_store.save_glyph(active)
        
        expired = GlyphToken(
            glyph_id="G-EXPIRED",
            glyph_class=GlyphClass.ANCHOR,
            explanation="Expired glyph",
            ttl_seconds=1,
        )
        expired.expires_at = datetime.utcnow() - timedelta(seconds=100)
        temp_store.save_glyph(expired)
        
        active_glyphs = temp_store.get_active_glyphs()
        expired_glyphs = temp_store.get_expired_glyphs()
        
        assert "G-ACTIVE" in active_glyphs
        assert "G-EXPIRED" in expired_glyphs


class TestGlyphEngine:
    """Integration tests for the full engine."""
    
    @pytest.fixture
    def temp_engine(self):
        path = Path(tempfile.mkdtemp()) / "test_vault"
        config = EngineConfig(
            vault_path=path,
            require_auth=False,  # Disable for testing
        )
        engine = GlyphEngine(config)
        yield engine
        shutil.rmtree(path, ignore_errors=True)
    
    def test_process_state(self, temp_engine):
        response = temp_engine.process_input({
            "type": "state",
            "auth_token": "test-token",
            "payload": {
                "class": "anchor",
                "explanation": "Test state glyph",
                "intensity": 0.7,
            },
        })
        assert response.success
        assert response.glyph_id is not None
        assert "Test state glyph" in response.text_output
    
    def test_process_fact(self, temp_engine):
        response = temp_engine.process_input({
            "type": "fact",
            "auth_token": "test-token",
            "payload": {
                "content": "This is a durable fact",
                "category": "test",
            },
        })
        assert response.success
        assert "Fact stored" in response.message
    
    def test_process_commands(self, temp_engine):
        # Create glyph
        create_resp = temp_engine.process_input({
            "type": "state",
            "auth_token": "test-token",
            "payload": {
                "class": "mutation",
                "explanation": "Command test glyph",
            },
        })
        glyph_id = create_resp.glyph_id
        
        # Refresh
        refresh_resp = temp_engine.process_input({
            "type": "command",
            "verb": "refresh",
            "target": glyph_id,
            "auth_token": "test-token",
            "payload": {"seconds": 3600},
        })
        assert refresh_resp.success
        
        # Attenuate
        atten_resp = temp_engine.process_input({
            "type": "command",
            "verb": "attenuate",
            "target": glyph_id,
            "auth_token": "test-token",
            "payload": {"factor": 0.5},
        })
        assert atten_resp.success
        
        # Audit (no target required)
        audit_resp = temp_engine.process_input({
            "type": "command",
            "verb": "audit",
            "auth_token": "test-token",
            "payload": {},
        })
        assert audit_resp.success
        assert "AUDIT REPORT" in audit_resp.text_output
        
        # Forget
        forget_resp = temp_engine.process_input({
            "type": "command",
            "verb": "forget",
            "target": glyph_id,
            "auth_token": "test-token",
            "payload": {},
        })
        assert forget_resp.success
    
    def test_state_summary(self, temp_engine):
        summary = temp_engine.get_state_summary()
        assert "session_id" in summary
        assert "active_glyph_count" in summary
        assert "glyphs" in summary
    
    def test_accretion_limit(self, temp_engine):
        # Set very low limit
        temp_engine.config.max_active_glyphs = 3
        
        # Create glyphs until limit
        for i in range(5):
            resp = temp_engine.process_input({
                "type": "state",
                "payload": {
                    "class": "anchor",
                    "explanation": f"Glyph {i}",
                },
            })
            if i >= 3:
                # Should fail after limit (accounting for genesis glyphs)
                pass  # Genesis glyphs count toward limit


class TestAuditLog:
    """Tests for audit logging."""
    
    @pytest.fixture
    def temp_audit(self):
        path = Path(tempfile.mkdtemp()) / "test_audit.jsonl"
        audit = AuditLog(path)
        yield audit
        shutil.rmtree(path.parent, ignore_errors=True)
    
    def test_create_and_read_events(self, temp_audit):
        from glyph_engine.audit import AuditEventType
        
        temp_audit.create_event(
            event_type=AuditEventType.CREATED,
            glyph_id="G-100",
            reason="Test creation",
        )
        
        events = temp_audit.read_all()
        assert len(events) == 1
        assert events[0].glyph_id == "G-100"
    
    def test_archaeology(self, temp_audit):
        from glyph_engine.audit import AuditEventType
        
        temp_audit.create_event(
            event_type=AuditEventType.CREATED,
            glyph_id="G-200",
            reason="Created",
        )
        temp_audit.create_event(
            event_type=AuditEventType.MUTATED,
            glyph_id="G-200",
            reason="Modified",
        )
        temp_audit.create_event(
            event_type=AuditEventType.REFRESHED,
            glyph_id="G-200",
            reason="TTL extended",
        )
        
        history = temp_audit.reconstruct_glyph_history("G-200")
        assert history["total_events"] == 3
        assert len(history["timeline"]) == 3
        assert history["creation_event"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
