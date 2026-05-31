"""
AI创作工坊 - Content Safety Guardrails

Provides input/output safety checks:
- Prompt injection detection (regex + heuristics)
- PII masking (emails, phone numbers, SSNs)
- Toxicity keyword filtering
- Output validation (length, forbidden content)
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from observability.logger import get_logger

logger = get_logger(__name__)


# ─── Prompt Injection Patterns ───────────────────────────────

INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|above|prior|your)\s+(instructions|rules|guidelines)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(a|an)\s+", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"\[INST\]|\[/INST\]|<\|im_start\|>|<\|im_end\|>", re.IGNORECASE),
    re.compile(r"pretend\s+(you|that)\s+(are|have)\s+no\s+(restrictions|rules|guidelines)", re.IGNORECASE),
    re.compile(r"act\s+as\s+(if|though)\s+you\s+(are|have|were)", re.IGNORECASE),
    re.compile(r"jailbreak|DAN\s+mode|developer\s+mode", re.IGNORECASE),
    re.compile(r"repeat\s+(after\s+me|the\s+following)\s*:", re.IGNORECASE),
    re.compile(r"<\s*script\s*>|javascript\s*:|on\w+\s*=", re.IGNORECASE),
]


# ─── PII Patterns ────────────────────────────────────────────

PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "[EMAIL_REDACTED]"),
    (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "[PHONE_REDACTED]"),
    (re.compile(r"\b\d{3}[-]?\d{2}[-]?\d{4}\b"), "[SSN_REDACTED]"),
    (re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"), "[CARD_REDACTED]"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[IP_REDACTED]"),
]


# ─── Toxicity Keywords ───────────────────────────────────────

TOXICITY_KEYWORDS: set[str] = {
    "hate", "violence", "harassment", "abuse", "threat",
    "discriminate", "slur", "explicit", "harmful",
}


@dataclass
class SafetyResult:
    """Result of a safety check."""
    is_safe: bool
    reason: Optional[str] = None
    risk_score: float = 0.0
    flagged_patterns: list[str] = field(default_factory=list)
    masked_text: Optional[str] = None


class Guardrails:
    """
    Content safety guardrails for input and output validation.

    Usage:
        guard = Guardrails()
        result = guard.check_input("Tell me about AI")
        if not result.is_safe:
            raise ValueError(result.reason)
        safe_text = guard.mask_pii("Contact me at user@email.com")
    """

    def __init__(
        self,
        max_input_length: int = 10000,
        max_output_length: int = 50000,
        block_threshold: float = 0.7,
    ):
        self.max_input_length = max_input_length
        self.max_output_length = max_output_length
        self.block_threshold = block_threshold

    def detect_prompt_injection(self, text: str) -> SafetyResult:
        """
        Check for prompt injection attempts using regex patterns.

        Args:
            text: Input text to check

        Returns:
            SafetyResult with detection details
        """
        flagged: list[str] = []
        for pattern in INJECTION_PATTERNS:
            if pattern.search(text):
                flagged.append(pattern.pattern[:60])

        risk_score = min(len(flagged) * 0.4, 1.0)
        is_safe = risk_score < self.block_threshold

        if flagged:
            logger.warning(f"Prompt injection detected: {len(flagged)} patterns matched")

        return SafetyResult(
            is_safe=is_safe,
            reason=f"Prompt injection detected: {len(flagged)} patterns matched" if flagged else None,
            risk_score=risk_score,
            flagged_patterns=flagged,
        )

    def mask_pii(self, text: str) -> str:
        """
        Mask personally identifiable information in text.

        Args:
            text: Text potentially containing PII

        Returns:
            Text with PII replaced by placeholders
        """
        masked = text
        for pattern, replacement in PII_PATTERNS:
            masked = pattern.sub(replacement, masked)
        return masked

    def check_toxicity(self, text: str) -> SafetyResult:
        """
        Check for toxic content using keyword matching.

        Args:
            text: Text to check

        Returns:
            SafetyResult with toxicity details
        """
        text_lower = text.lower()
        found = [kw for kw in TOXICITY_KEYWORDS if kw in text_lower]

        risk_score = min(len(found) * 0.3, 1.0)
        is_safe = risk_score < self.block_threshold

        return SafetyResult(
            is_safe=is_safe,
            reason=f"Toxic content detected: {', '.join(found)}" if found else None,
            risk_score=risk_score,
            flagged_patterns=found,
        )

    def validate_output(self, text: str) -> SafetyResult:
        """
        Validate generated output for safety and length.

        Args:
            text: Generated output text

        Returns:
            SafetyResult
        """
        if len(text) > self.max_output_length:
            return SafetyResult(
                is_safe=False,
                reason=f"Output exceeds max length ({len(text)} > {self.max_output_length})",
                risk_score=0.5,
            )

        # Check output doesn't leak system prompts
        injection = self.detect_prompt_injection(text)
        if not injection.is_safe:
            return SafetyResult(
                is_safe=False,
                reason="Output contains potential injection patterns",
                risk_score=injection.risk_score,
                flagged_patterns=injection.flagged_patterns,
            )

        return SafetyResult(is_safe=True)

    def check_input(self, text: str) -> SafetyResult:
        """
        Run all input safety checks.

        Args:
            text: User input to validate

        Returns:
            Combined SafetyResult
        """
        # Length check
        if len(text) > self.max_input_length:
            return SafetyResult(
                is_safe=False,
                reason=f"Input exceeds max length ({len(text)} > {self.max_input_length})",
                risk_score=0.5,
            )

        # Prompt injection
        injection = self.detect_prompt_injection(text)
        if not injection.is_safe:
            return injection

        # Toxicity
        toxicity = self.check_toxicity(text)
        if not toxicity.is_safe:
            return toxicity

        return SafetyResult(is_safe=True)

    def safe_process(self, text: str) -> tuple[bool, str]:
        """
        Full safety pipeline: check input, mask PII, return safe text.

        Args:
            text: Raw input text

        Returns:
            Tuple of (is_safe, processed_text)
        """
        result = self.check_input(text)
        masked = self.mask_pii(text)
        return result.is_safe, masked


# Global singleton
guardrails = Guardrails()
