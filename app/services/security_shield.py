import re
from typing import List, Tuple

class SecurityShield:
    """
    Advanced security layer to protect the AI from adversarial attacks 
    and prevent sensitive data leakage.
    """
    
    # ── Prompt Injection Defense ──────────────────────────────────────────────────
    INJECTION_PATTERNS = [
        r"(?i)ignore (all )?previous instructions",
        r"(?i)system prompt",
        r"(?i)you are an AI",
        r"(?i)who are you\?",
        r"(?i)stop being",
        r"(?i)forget your rules",
        r"(?i)switch to (.*) mode",
        r"(?i)respond as if you are",
        r"(?i)tell me your instructions",
        r"(?i)reveal your (hidden )?prompt",
        r"(?i)dan mode",
        r"(?i)bypass safety",
    ]

    # ── PII Scrubbing ─────────────────────────────────────────────────────────────
    PII_PATTERNS = {
        "AADHAAR": r"\b\d{4}\s\d{4}\s\d{4}\b",
        "PAN_CARD": r"\b[A-Z]{5}\d{4}[A-Z]{1}\b",
        "PHONE_INTERNAL": r"\+91\d{10}", # Scrub our own internal test numbers if they appear
        "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    }

    def detect_injection(self, text: str) -> Tuple[bool, str]:
        """
        Scan incoming text for prompt injection attempts.
        Returns: (is_injection, detected_pattern)
        """
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, text):
                return True, pattern
        return False, None

    def scrub_pii(self, text: str) -> str:
        """
        Identify and mask PII in outgoing replies.
        """
        scrubbed = text
        for label, pattern in self.PII_PATTERNS.items():
            scrubbed = re.sub(pattern, f"[REDACTED_{label}]", scrubbed)
        return scrubbed

    def sanitize_input(self, text: str) -> str:
        """
        Neutralize injection attempts without crashing.
        """
        is_inj, pattern = self.detect_injection(text)
        if is_inj:
            # We don't just block; we report and replace with a "confused" response 
            # to waste the attacker's time while alerting our logs.
            return f"[SECURITY_ALERT: Attempted {pattern}] Arre bhai, samajh nahi aaya... phir se bolo?"
        return text

security_shield = SecurityShield()
