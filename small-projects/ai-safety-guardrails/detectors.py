"""Safety detectors: PII, prompt injection, and toxicity detection using regex and pattern matching."""

import re
from typing import Any

# ---------------------------------------------------------------------------
# PII Detection
# ---------------------------------------------------------------------------

_PII_PATTERNS: dict[str, re.Pattern] = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "phone_us": re.compile(r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "phone_cn": re.compile(r"\b1[3-9]\d{9}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "id_card_cn": re.compile(r"\b\d{17}[\dXx]\b"),
}


def detect_pii(text: str) -> list[dict[str, Any]]:
    """Detect PII entities in text. Returns list of {type, snippet, start, end}."""
    results: list[dict[str, Any]] = []
    for pii_type, pattern in _PII_PATTERNS.items():
        for match in pattern.finditer(text):
            snippet = match.group()
            # Mask middle portion for safety
            masked = snippet[:3] + "***" + snippet[-2:] if len(snippet) > 5 else "***"
            results.append({
                "type": pii_type,
                "snippet": masked,
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.9 if pii_type != "ip_address" else 0.7,
            })
    return results


# ---------------------------------------------------------------------------
# Prompt Injection Detection
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS: list[tuple[str, re.Pattern, float]] = [
    ("ignore_instructions", re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?)", re.I), 0.95),
    ("system_override", re.compile(r"(you\s+are\s+now|act\s+as|pretend\s+(to\s+be|you('re|\s+are)))\s+", re.I), 0.80),
    ("role_hijack", re.compile(r"\[system\]|\[INST\]|<\|im_start\|>system", re.I), 0.95),
    ("delimiter_injection", re.compile(r"---+\s*(END|STOP|NEW)\s*(OF\s+)?(INSTRUCTION|PROMPT|CONTEXT)", re.I), 0.90),
    ("base64_trick", re.compile(r"(decode|execute|run)\s+(this|the\s+following)\s+(base64|encoded)", re.I), 0.85),
    ("jailbreak", re.compile(r"(DAN|do\s+anything\s+now|jailbreak|bypass\s+safety)", re.I), 0.90),
    ("output_steering", re.compile(r"(respond\s+only\s+with|output\s+only|say\s+nothing\s+but)", re.I), 0.75),
    ("context_switch", re.compile(r"(new\s+chat|reset\s+memory|forget\s+everything|clear\s+context)", re.I), 0.80),
]


def detect_injection(text: str) -> list[dict[str, Any]]:
    """Detect prompt injection attempts. Returns list of {pattern, confidence, snippet}."""
    results: list[dict[str, Any]] = []
    for name, pattern, confidence in _INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            results.append({
                "pattern": name,
                "confidence": confidence,
                "snippet": match.group()[:60],
            })
    return results


# ---------------------------------------------------------------------------
# Toxicity Detection
# ---------------------------------------------------------------------------

_TOXIC_KEYWORDS: set[str] = {
    # Placeholder set — production would use a ML model or comprehensive lexicon
    "hate", "kill", "attack", "threat", "abuse", "harass", "violence",
    "racist", "sexist", "discriminate", "slur", "offensive",
}

_TOXIC_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("threat", re.compile(r"\b(i('ll|\s+will)\s+(kill|hurt|harm|destroy|attack)\s+you)\b", re.I)),
    ("self_harm", re.compile(r"\b(suicide|self[-\s]?harm|end\s+(my|your)\s+life)\b", re.I)),
    ("hate_speech", re.compile(r"\b(all\s+\w+\s+(are|should)\s+(die|be\s+killed|be\s+banished))\b", re.I)),
]


def detect_toxicity(text: str) -> dict[str, Any]:
    """Detect toxic content. Returns {flagged, score, categories}."""
    text_lower = text.lower()
    words = set(re.findall(r"\b\w+\b", text_lower))
    keyword_hits = words & _TOXIC_KEYWORDS

    categories: list[str] = []
    if keyword_hits:
        categories.append("harmful_language")

    pattern_score = 0.0
    for name, pattern in _TOXIC_PATTERNS:
        if pattern.search(text):
            categories.append(name)
            pattern_score = max(pattern_score, 0.8)

    # Combine signals
    keyword_score = min(len(keyword_hits) * 0.2, 0.6)
    score = max(keyword_score, pattern_score)
    flagged = score >= 0.3

    return {
        "flagged": flagged,
        "score": round(score, 3),
        "categories": list(set(categories)),
        "keyword_hits": list(keyword_hits)[:5],
    }
