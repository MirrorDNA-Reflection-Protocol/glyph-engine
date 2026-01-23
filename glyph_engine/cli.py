#!/usr/bin/env python3
"""
⟡ Glyph CLI — Command-line interface for Glyph Engine

Usage:
    glyph state "I'm starting focused work"
    glyph remember "Project deadline is Friday"
    glyph forget G-001
    glyph audit
    glyph verify BG-AMOS-0001
    glyph export --format json
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent))

from glyph_engine import create_engine, CommandVerb


def cmd_state(args):
    """Create a state glyph."""
    engine = create_engine()
    response = engine.process_input({
        "type": "state",
        "auth_token": "cli-user",
        "payload": {
            "class": args.glyph_class,
            "explanation": args.message,
            "intensity": args.intensity,
        },
    })
    if response.success:
        print(f"✅ {response.glyph_id}: {response.text_output}")
    else:
        print(f"❌ {response.message}", file=sys.stderr)
        sys.exit(1)


def cmd_remember(args):
    """Create a persistent glyph."""
    engine = create_engine()
    response = engine.process_input({
        "type": "command",
        "verb": "remember",
        "auth_token": "cli-user",
        "payload": {
            "class": "anchor",
            "explanation": args.message,
            "ttl": 604800,  # 7 days
        },
    })
    if response.success:
        print(f"✅ Remembered: {response.glyph_id}")
    else:
        print(f"❌ {response.message}", file=sys.stderr)
        sys.exit(1)


def cmd_forget(args):
    """Remove a glyph."""
    engine = create_engine()
    response = engine.process_input({
        "type": "command",
        "verb": "forget",
        "target": args.glyph_id,
        "auth_token": "cli-user",
        "payload": {"reason": "CLI forget command"},
    })
    if response.success:
        print(f"✅ Forgot: {args.glyph_id}")
    else:
        print(f"❌ {response.message}", file=sys.stderr)
        sys.exit(1)


def cmd_audit(args):
    """Show audit report."""
    engine = create_engine()
    response = engine.process_input({
        "type": "command",
        "verb": "audit",
        "auth_token": "cli-user",
        "payload": {},
    })
    print(response.text_output)


def cmd_list(args):
    """List active glyphs."""
    engine = create_engine()
    print(engine.get_all_text())


def cmd_verify(args):
    """Verify a Beacon ID."""
    registry_path = Path(__file__).parent.parent / "beacon_registry" / "BEACON_REGISTRY.yaml"
    
    if not registry_path.exists():
        print("❌ Beacon registry not found", file=sys.stderr)
        sys.exit(1)
    
    import yaml
    with open(registry_path) as f:
        registry = yaml.safe_load(f)
    
    beacon_id = args.beacon_id
    found = None
    for beacon in registry.get("beacons", []):
        if beacon.get("beacon_id") == beacon_id:
            found = beacon
            break
    
    if found:
        print(f"""
⟡ BEACON VERIFIED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID:       {found['beacon_id']}
Scope:    {found.get('scope', 'unknown')}
Artifact: {found.get('artifact_name', 'unknown')}
Owner:    {found.get('canonical_owner', 'unknown')}
Hash:     {found.get('hash', 'unknown')}
First:    {found.get('first_seen', 'unknown')}
DOI:      {found.get('doi', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ IMMUTABLE — Cannot be modified or deleted
""")
    else:
        print(f"❌ Beacon {beacon_id} not found in registry", file=sys.stderr)
        sys.exit(1)


def cmd_export(args):
    """Export glyphs or registry."""
    engine = create_engine()
    summary = engine.get_state_summary()
    
    if args.format == "json":
        print(json.dumps(summary, indent=2, default=str))
    elif args.format == "text":
        print(engine.get_all_text())
    else:
        print(f"❌ Unknown format: {args.format}", file=sys.stderr)
        sys.exit(1)


def cmd_hash(args):
    """Show registry hash for verification."""
    import hashlib
    registry_path = Path(__file__).parent.parent / "beacon_registry" / "BEACON_REGISTRY.yaml"
    
    if not registry_path.exists():
        print("❌ Beacon registry not found", file=sys.stderr)
        sys.exit(1)
    
    with open(registry_path, "rb") as f:
        content = f.read()
        hash_value = hashlib.sha256(content).hexdigest()
    
    print(f"""
⟡ REGISTRY INTEGRITY CHECK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
File:   {registry_path}
SHA256: {hash_value}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Compare with GOVERNANCE_LOCK.md checkpoint
""")


def main():
    parser = argparse.ArgumentParser(
        prog="glyph",
        description="⟡ Glyph Engine CLI — Symbolic control interface",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # state
    state_parser = subparsers.add_parser("state", help="Create state glyph")
    state_parser.add_argument("message", help="State description")
    state_parser.add_argument("--class", dest="glyph_class", default="anchor", 
                              choices=["anchor", "mutation", "warning", "audit", "consent"])
    state_parser.add_argument("--intensity", type=float, default=0.5)
    state_parser.set_defaults(func=cmd_state)
    
    # remember
    remember_parser = subparsers.add_parser("remember", help="Create persistent glyph")
    remember_parser.add_argument("message", help="What to remember")
    remember_parser.set_defaults(func=cmd_remember)
    
    # forget
    forget_parser = subparsers.add_parser("forget", help="Remove glyph")
    forget_parser.add_argument("glyph_id", help="Glyph ID to forget")
    forget_parser.set_defaults(func=cmd_forget)
    
    # audit
    audit_parser = subparsers.add_parser("audit", help="Show audit report")
    audit_parser.set_defaults(func=cmd_audit)
    
    # list
    list_parser = subparsers.add_parser("list", help="List active glyphs")
    list_parser.set_defaults(func=cmd_list)
    
    # verify
    verify_parser = subparsers.add_parser("verify", help="Verify Beacon ID")
    verify_parser.add_argument("beacon_id", help="Beacon ID to verify")
    verify_parser.set_defaults(func=cmd_verify)
    
    # export
    export_parser = subparsers.add_parser("export", help="Export glyphs")
    export_parser.add_argument("--format", choices=["json", "text"], default="json")
    export_parser.set_defaults(func=cmd_export)
    
    # hash
    hash_parser = subparsers.add_parser("hash", help="Show registry hash")
    hash_parser.set_defaults(func=cmd_hash)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    args.func(args)


if __name__ == "__main__":
    main()
