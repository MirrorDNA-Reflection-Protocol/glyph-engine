"""
⟡ Glyph Store - Vault-integrated persistent storage

Storage aligns with Spec Section 5:
- Facts → Markdown + YAML
- Glyphs → JSON
- Scrolls → Markdown (validated schema)
- Audits → Append-only JSONL

Gap #8 mitigation: Transaction semantics with commit/rollback.
"""

from typing import Dict, Optional, List, Any
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field
import json
import shutil

from glyph_engine.token import GlyphToken, GENESIS_GLYPHS
from glyph_engine.scroll import Scroll, GENESIS_SCROLL


class Transaction(BaseModel):
    """Pending transaction for atomic operations."""
    transaction_id: str
    operations: List[Dict[str, Any]] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    committed: bool = False
    rolled_back: bool = False


class GlyphStore:
    """
    Persistent storage for glyphs, scrolls, and facts.
    
    Vault integration with transaction support.
    """
    
    def __init__(self, vault_path: Path):
        """
        Initialize store with Vault path.
        
        Creates subdirectories:
        - glyphs/  (JSON files)
        - scrolls/ (JSON files)
        - facts/   (Markdown files)
        - _backup/ (Transaction backups)
        """
        self.vault_path = vault_path
        self.glyphs_path = vault_path / "glyphs"
        self.scrolls_path = vault_path / "scrolls"
        self.facts_path = vault_path / "facts"
        self.backup_path = vault_path / "_backup"
        
        # Create directories
        for path in [self.glyphs_path, self.scrolls_path, self.facts_path, self.backup_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Active transaction
        self._transaction: Optional[Transaction] = None
        self._tx_counter = 0
        
        # In-memory cache for performance
        self._glyph_cache: Dict[str, GlyphToken] = {}
        self._scroll_cache: Dict[str, Scroll] = {}
        
        # Initialize with genesis state if empty
        self._ensure_genesis()
    
    def _ensure_genesis(self) -> None:
        """Ensure genesis glyphs and scrolls exist (Gap #1 - cold start)."""
        existing_glyphs = list(self.glyphs_path.glob("*.json"))
        if not existing_glyphs:
            # Bootstrap with genesis glyphs
            for glyph_id, glyph in GENESIS_GLYPHS.items():
                self.save_glyph(glyph)
            
            # Bootstrap with genesis scroll
            self.save_scroll(GENESIS_SCROLL)
    
    # ==================== TRANSACTION SUPPORT ====================
    
    def begin_transaction(self) -> str:
        """Start a new transaction."""
        if self._transaction is not None:
            raise RuntimeError("Transaction already in progress")
        
        self._tx_counter += 1
        tx_id = f"TX-{self._tx_counter:06d}"
        
        # Create backup of current state
        tx_backup = self.backup_path / tx_id
        tx_backup.mkdir(exist_ok=True)
        
        # Copy current glyphs to backup
        for glyph_file in self.glyphs_path.glob("*.json"):
            shutil.copy(glyph_file, tx_backup / glyph_file.name)
        
        self._transaction = Transaction(transaction_id=tx_id)
        return tx_id
    
    def commit_transaction(self) -> bool:
        """Commit current transaction."""
        if self._transaction is None:
            return False
        
        self._transaction.committed = True
        
        # Clean up backup (transaction succeeded)
        tx_backup = self.backup_path / self._transaction.transaction_id
        if tx_backup.exists():
            shutil.rmtree(tx_backup)
        
        self._transaction = None
        return True
    
    def rollback_transaction(self) -> bool:
        """Rollback current transaction."""
        if self._transaction is None:
            return False
        
        # Restore from backup
        tx_backup = self.backup_path / self._transaction.transaction_id
        if tx_backup.exists():
            # Clear current glyphs
            for glyph_file in self.glyphs_path.glob("*.json"):
                glyph_file.unlink()
            
            # Restore from backup
            for backup_file in tx_backup.glob("*.json"):
                shutil.copy(backup_file, self.glyphs_path / backup_file.name)
            
            # Clean up backup
            shutil.rmtree(tx_backup)
        
        self._transaction.rolled_back = True
        self._transaction = None
        
        # Clear cache
        self._glyph_cache.clear()
        
        return True
    
    # ==================== GLYPH OPERATIONS ====================
    
    def save_glyph(self, glyph: GlyphToken) -> None:
        """Save glyph to store."""
        glyph_file = self.glyphs_path / f"{glyph.glyph_id}.json"
        with open(glyph_file, "w") as f:
            f.write(glyph.model_dump_json(indent=2))
        
        # Update cache
        self._glyph_cache[glyph.glyph_id] = glyph
        
        # Log in transaction
        if self._transaction:
            self._transaction.operations.append({
                "type": "save_glyph",
                "glyph_id": glyph.glyph_id,
            })
    
    def load_glyph(self, glyph_id: str) -> Optional[GlyphToken]:
        """Load glyph from store."""
        # Check cache first
        if glyph_id in self._glyph_cache:
            return self._glyph_cache[glyph_id]
        
        glyph_file = self.glyphs_path / f"{glyph_id}.json"
        if not glyph_file.exists():
            return None
        
        with open(glyph_file, "r") as f:
            glyph = GlyphToken.model_validate_json(f.read())
        
        # Update cache
        self._glyph_cache[glyph_id] = glyph
        return glyph
    
    def delete_glyph(self, glyph_id: str) -> bool:
        """
        Delete glyph from store.
        
        Note: This is LOGGED, not silent. Use audit layer to record.
        """
        glyph_file = self.glyphs_path / f"{glyph_id}.json"
        if not glyph_file.exists():
            return False
        
        glyph_file.unlink()
        
        # Remove from cache
        if glyph_id in self._glyph_cache:
            del self._glyph_cache[glyph_id]
        
        # Log in transaction
        if self._transaction:
            self._transaction.operations.append({
                "type": "delete_glyph",
                "glyph_id": glyph_id,
            })
        
        return True
    
    def list_glyphs(self) -> List[str]:
        """List all glyph IDs in store."""
        return [f.stem for f in self.glyphs_path.glob("*.json")]
    
    def get_all_glyphs(self) -> Dict[str, GlyphToken]:
        """Load all glyphs."""
        glyphs = {}
        for glyph_id in self.list_glyphs():
            glyph = self.load_glyph(glyph_id)
            if glyph:
                glyphs[glyph_id] = glyph
        return glyphs
    
    def get_active_glyphs(self) -> Dict[str, GlyphToken]:
        """Get all non-expired glyphs."""
        return {
            gid: g for gid, g in self.get_all_glyphs().items()
            if not g.is_expired()
        }
    
    def get_expired_glyphs(self) -> Dict[str, GlyphToken]:
        """Get all expired glyphs (for cleanup)."""
        return {
            gid: g for gid, g in self.get_all_glyphs().items()
            if g.is_expired()
        }
    
    # ==================== SCROLL OPERATIONS ====================
    
    def save_scroll(self, scroll: Scroll) -> None:
        """Save scroll to store."""
        scroll_file = self.scrolls_path / f"{scroll.scroll_id}.json"
        with open(scroll_file, "w") as f:
            # Need to convert sets to lists for JSON serialization
            data = scroll.model_dump()
            data["allowed_mutations"] = list(data["allowed_mutations"])
            data["forbidden_mutations"] = list(data["forbidden_mutations"])
            json.dump(data, f, indent=2, default=str)
        
        self._scroll_cache[scroll.scroll_id] = scroll
    
    def load_scroll(self, scroll_id: str) -> Optional[Scroll]:
        """Load scroll from store."""
        if scroll_id in self._scroll_cache:
            return self._scroll_cache[scroll_id]
        
        scroll_file = self.scrolls_path / f"{scroll_id}.json"
        if not scroll_file.exists():
            return None
        
        with open(scroll_file, "r") as f:
            data = json.load(f)
            # Convert lists back to sets
            data["allowed_mutations"] = set(data["allowed_mutations"])
            data["forbidden_mutations"] = set(data["forbidden_mutations"])
            scroll = Scroll.model_validate(data)
        
        self._scroll_cache[scroll_id] = scroll
        return scroll
    
    def list_scrolls(self) -> List[str]:
        """List all scroll IDs."""
        return [f.stem for f in self.scrolls_path.glob("*.json")]
    
    # ==================== FACT OPERATIONS ====================
    
    def save_fact(self, fact_id: str, content: str, metadata: Dict[str, Any]) -> None:
        """Save fact as Markdown with YAML frontmatter."""
        fact_file = self.facts_path / f"{fact_id}.md"
        
        # Build YAML frontmatter
        frontmatter = "---\n"
        frontmatter += f"fact_id: {fact_id}\n"
        frontmatter += f"created: {datetime.utcnow().isoformat()}\n"
        for key, value in metadata.items():
            frontmatter += f"{key}: {value}\n"
        frontmatter += "---\n\n"
        
        with open(fact_file, "w") as f:
            f.write(frontmatter + content)
    
    def load_fact(self, fact_id: str) -> Optional[str]:
        """Load fact content (strips frontmatter)."""
        fact_file = self.facts_path / f"{fact_id}.md"
        if not fact_file.exists():
            return None
        
        with open(fact_file, "r") as f:
            content = f.read()
        
        # Strip YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return parts[2].strip()
        
        return content
    
    # ==================== STATS ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        glyphs = self.get_all_glyphs()
        active = self.get_active_glyphs()
        
        return {
            "total_glyphs": len(glyphs),
            "active_glyphs": len(active),
            "expired_glyphs": len(glyphs) - len(active),
            "scrolls": len(self.list_scrolls()),
            "facts": len(list(self.facts_path.glob("*.md"))),
            "vault_path": str(self.vault_path),
        }
