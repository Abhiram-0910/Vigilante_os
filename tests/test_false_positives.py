"""
False positive tests: legitimate messages must NOT be flagged as scams.
Judges send these; scam_detected must be False (or very low confidence).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/analyze")
API_KEY = os.getenv("VIBHISHAN_API_KEY", "gov_secure_access_2026")

LEGITIMATE_MESSAGES = [
    "Hi, how are you today?",
    "Can you help me with my account?",
    "I need customer support",
    "Hello",
    "Good morning",
    "Thanks for your help",
    "When will my order arrive?",
    "What is your return policy?",
    "I have a question about my booking",
    "Ok",
]


def test_false_positive_rate():
    """Legitimate messages must not be flagged as scams (scam_detected=False)."""
    headers = {"X-API-KEY": API_KEY}
    failures = []
    for msg in LEGITIMATE_MESSAGES:
        try:
            r = requests.post(
                API_URL,
                json={
                    "session_id": f"fp_{hash(msg) % 10**8}",
                    "message_text": msg,
                },
                headers=headers,
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            if data.get("scam_detected") is True:
                failures.append((msg, "scam_detected=True"))
        except Exception as e:
            failures.append((msg, str(e)))
    assert not failures, (
        f"False positives (legitimate messages flagged as scam): {failures}"
    )


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
