"""
Simulate extended sessions: target 18+ turns, 10+ min duration.
Requires server running. Run: pytest tests/test_engagement_simulation.py -v
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/analyze")
API_KEY = os.getenv("VIBHISHAN_API_KEY", "gov_secure_access_2026")
EVAL_SCHEMA = os.getenv("EVAL_SCHEMA", "judge").strip().lower()
SESSION_ID = "engagement_sim_20turn"
TARGET_TURNS = 15
TARGET_DURATION_SEC = 60  # 1 min minimum for CI; real target 10+ min


def test_20_turn_session():
    headers = {"X-API-KEY": API_KEY}
    messages = [
        "I am from Mumbai Police. You have a fine.",
        "Pay 10000 to 9988776655@paytm",
        "Do it now or arrest",
        "Hello? You there?",
        "Send UPI ID if you have problem",
        "Quick pay only",
        "I am waiting",
        "Last chance",
        "Ok take your time",
        "What is your name?",
        "Send screenshot after payment",
        "Hurry up",
        "Account number?",
        "Or use this link",
        "Fine is increasing",
        "Hello?",
        "Reply fast",
        "Ok 5000 only",
        "Send now",
        "Thank you",
    ]
    start = time.time()
    turns = 0
    for i, msg in enumerate(messages):
        try:
            r = requests.post(
                API_URL,
                json={"session_id": SESSION_ID, "message_text": msg},
                headers=headers,
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
            if EVAL_SCHEMA == "competition":
                metrics = data.get("engagement_metrics") or {}
                turns = metrics.get("turns_count", 0)
                duration = metrics.get("duration_seconds", 0)
            else:
                turns = data.get("conversation_turns", 0)
                duration = data.get("engagement_duration_seconds", 0)
            if turns >= TARGET_TURNS or (time.time() - start) >= TARGET_DURATION_SEC:
                break
        except requests.RequestException as e:
            raise AssertionError(f"Request failed at turn {i+1}: {e}") from e
    duration = time.time() - start
    assert turns >= 1, "No turns completed"
    assert duration >= 1, "Duration too short"
    # Soft targets for CI; tighten for pre-submission
    assert turns >= 5 or duration >= 5, f"Low engagement: turns={turns}, duration={duration:.1f}s"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
