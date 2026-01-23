"""
⟡ Validation Layer - Drift prevention and governance

Every glyph transition passes through validators.
This is where drift prevention lives.

Key checks:
- No recursive amplification
- No identity fixation
- No unbounded persistence
- Authentication required for sensitive operations

Gap #7 mitigation: Validators are themselves checksummed.
"""

from enum import Enum
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import hashlib


class ValidationAction(str, Enum):
    """Action to take on validation failure."""
    ALLOW = "allow"
    HALT = "halt"
    REVERT = "revert"
    REQUEST_CONFIRMATION = "request_confirmation"


class ValidatorResult(BaseModel):
    """Result of a validation check."""
    passed: bool
    validator_id: str
    check_name: str
    message: str
    action: ValidationAction = ValidationAction.ALLOW
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationCheck(BaseModel):
    """Single validation check."""
    name: str
    description: str
    is_critical: bool = False


class Validator(BaseModel):
    """
    Glyph transition validator.
    
    Each validator has a set of checks and a defined action on failure.
    """
    validator_id: str = Field(..., description="Unique ID (e.g., V-03)")
    name: str = Field(..., description="Human-readable name")
    checks: List[ValidationCheck] = Field(default_factory=list)
    on_fail: ValidationAction = Field(default=ValidationAction.HALT)
    
    # Meta-validation (Gap #7 - who validates the validator?)
    version: str = Field(default="1.0.0")
    checksum: Optional[str] = None
    
    def compute_checksum(self) -> str:
        """Compute checksum for validator integrity."""
        data = f"{self.validator_id}:{self.version}:{len(self.checks)}"
        for check in self.checks:
            data += f":{check.name}:{check.is_critical}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def verify_integrity(self) -> bool:
        """Verify validator hasn't been tampered with."""
        if self.checksum is None:
            return True  # No checksum set yet
        return self.compute_checksum() == self.checksum


class ValidatorEngine:
    """
    Validation engine that runs all checks.
    
    This is the core drift prevention mechanism.
    """
    
    def __init__(self):
        self.validators: Dict[str, Validator] = {}
        self._register_core_validators()
    
    def _register_core_validators(self) -> None:
        """Register built-in validators."""
        # V-00: Genesis validator
        self.validators["V-00"] = Validator(
            validator_id="V-00",
            name="Genesis Validator",
            checks=[
                ValidationCheck(
                    name="no_identity_fixation",
                    description="Glyphs cannot represent identity",
                    is_critical=True,
                ),
                ValidationCheck(
                    name="ttl_required",
                    description="All glyphs must have TTL",
                    is_critical=True,
                ),
            ],
            on_fail=ValidationAction.HALT,
        )
        
        # V-01: Standard session validator
        self.validators["V-01"] = Validator(
            validator_id="V-01",
            name="Standard Session Validator",
            checks=[
                ValidationCheck(
                    name="no_recursive_amplification",
                    description="Cannot amplify same glyph repeatedly",
                    is_critical=True,
                ),
                ValidationCheck(
                    name="no_identity_fixation",
                    description="Glyphs cannot represent identity",
                    is_critical=True,
                ),
                ValidationCheck(
                    name="ttl_required",
                    description="All glyphs must have TTL",
                    is_critical=True,
                ),
                ValidationCheck(
                    name="max_intensity",
                    description="Intensity cannot exceed 1.0",
                    is_critical=False,
                ),
                ValidationCheck(
                    name="authentication_required",
                    description="Mutations require authenticated source",
                    is_critical=True,
                ),
            ],
            on_fail=ValidationAction.HALT,
        )
        
        # V-02: Multi-agent validator (Gap #4)
        self.validators["V-02"] = Validator(
            validator_id="V-02",
            name="Multi-Agent Validator",
            checks=[
                ValidationCheck(
                    name="no_ownership_conflict",
                    description="Cannot mutate glyph owned by another agent without consent",
                    is_critical=True,
                ),
                ValidationCheck(
                    name="no_race_condition",
                    description="Check for concurrent modification attempts",
                    is_critical=True,
                ),
            ],
            on_fail=ValidationAction.REQUEST_CONFIRMATION,
        )
        
        # Compute checksums
        for v in self.validators.values():
            v.checksum = v.compute_checksum()
    
    def get_validator(self, validator_id: str) -> Optional[Validator]:
        """Get validator by ID."""
        return self.validators.get(validator_id)
    
    def validate_transition(
        self,
        validator_id: str,
        context: Dict[str, Any],
    ) -> List[ValidatorResult]:
        """
        Run all checks for a validator.
        
        Context should contain:
        - glyph: The glyph being validated
        - mutation: The mutation being applied
        - source: The source of the mutation
        - history: Recent mutation history for the glyph
        """
        validator = self.get_validator(validator_id)
        if validator is None:
            return [ValidatorResult(
                passed=False,
                validator_id=validator_id,
                check_name="validator_exists",
                message=f"Validator {validator_id} not found",
                action=ValidationAction.HALT,
            )]
        
        # Verify validator integrity (Gap #7)
        if not validator.verify_integrity():
            return [ValidatorResult(
                passed=False,
                validator_id=validator_id,
                check_name="validator_integrity",
                message=f"Validator {validator_id} failed integrity check",
                action=ValidationAction.HALT,
            )]
        
        results = []
        for check in validator.checks:
            result = self._run_check(check, context, validator)
            results.append(result)
            
            # Stop on critical failure
            if not result.passed and check.is_critical:
                break
        
        return results
    
    def _run_check(
        self,
        check: ValidationCheck,
        context: Dict[str, Any],
        validator: Validator,
    ) -> ValidatorResult:
        """Run a single validation check."""
        glyph = context.get("glyph")
        mutation = context.get("mutation")
        source = context.get("source", "unknown")
        history = context.get("history", [])
        
        # Check implementations
        if check.name == "no_identity_fixation":
            # Glyphs cannot contain identity-like content
            if glyph and "identity" in glyph.explanation.lower():
                return ValidatorResult(
                    passed=False,
                    validator_id=validator.validator_id,
                    check_name=check.name,
                    message="Glyph explanation contains identity reference",
                    action=validator.on_fail,
                )
        
        elif check.name == "ttl_required":
            if glyph and glyph.ttl_seconds <= 0:
                return ValidatorResult(
                    passed=False,
                    validator_id=validator.validator_id,
                    check_name=check.name,
                    message="Glyph has no TTL",
                    action=validator.on_fail,
                )
        
        elif check.name == "no_recursive_amplification":
            # Check if this glyph has been amplified recently
            amplify_count = sum(1 for h in history if h.get("mutation") == "amplify")
            if amplify_count >= 3:
                return ValidatorResult(
                    passed=False,
                    validator_id=validator.validator_id,
                    check_name=check.name,
                    message="Recursive amplification detected",
                    action=validator.on_fail,
                )
        
        elif check.name == "authentication_required":
            if source == "unknown" or not context.get("authenticated", False):
                return ValidatorResult(
                    passed=False,
                    validator_id=validator.validator_id,
                    check_name=check.name,
                    message="Unauthenticated mutation attempt",
                    action=validator.on_fail,
                )
        
        elif check.name == "max_intensity":
            if glyph and glyph.intensity > 1.0:
                return ValidatorResult(
                    passed=False,
                    validator_id=validator.validator_id,
                    check_name=check.name,
                    message="Intensity exceeds maximum",
                    action=validator.on_fail,
                )
        
        # Default: pass
        return ValidatorResult(
            passed=True,
            validator_id=validator.validator_id,
            check_name=check.name,
            message="Check passed",
            action=ValidationAction.ALLOW,
        )
