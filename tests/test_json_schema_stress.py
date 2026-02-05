"""
Validate JSON schema on N sample outputs: exact structure, no extra/missing keys.
Run with server: pytest tests/test_json_schema_stress.py -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from pydantic import ValidationError

from app.schemas import CompetitionResponse, JudgeResponse

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/analyze")
API_KEY = os.getenv("VIBHISHAN_API_KEY", "gov_secure_access_2026")
EVAL_SCHEMA = os.getenv("EVAL_SCHEMA", "judge").strip().lower()

PAYLOADS = [
    {"session_id": "schema_1", "message_text": "Hi"},
    {"session_id": "schema_2", "message_text": "Pay 5000 to 9988@paytm"},
    {"session_id": "schema_3", "message_text": ""},
    {"session_id": "schema_4", "message_text": "Your KYC expired. Update now."},
    {"session_id": "schema_5", "message_text": "Hello, is this support?"},
    {"session_id": "schema_6", "message_text": "Send OTP to verify"},
    {"session_id": "schema_7", "message_text": "Lottery winner! Fee 10000"},
    {"session_id": "schema_8", "message_text": "Account block. Transfer to 1234567890123456"},
    {"session_id": "schema_9", "message_text": "Call 98-88-77-66-55"},
    {"session_id": "schema_10", "message_text": "Click https://bit.ly/phish"},
]


def test_json_schema_on_responses():
    headers = {"X-API-KEY": API_KEY}
    for i, payload in enumerate(PAYLOADS):
        try:
            r = requests.post(API_URL, json=payload, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            if EVAL_SCHEMA == "competition":
                CompetitionResponse.model_validate(data)
            else:
                JudgeResponse.model_validate(data)
        except requests.RequestException as e:
            raise AssertionError(f"Request {i+1} failed: {e}") from e
        except ValidationError as e:
            raise AssertionError(f"Schema validation failed for payload {i+1}: {e}") from e


def test_required_keys_present():
    headers = {"X-API-KEY": API_KEY}
    r = requests.post(API_URL, json=PAYLOADS[0], headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    if EVAL_SCHEMA == "competition":
        required = ["scam_detected", "engagement_metrics", "extracted_intelligence"]
        for k in required:
            assert k in data, f"Missing key: {k}"
        metrics = data.get("engagement_metrics") or {}
        for k in ("duration_seconds", "turns_count"):
            assert k in metrics, f"engagement_metrics missing: {k}"
        assert isinstance(data.get("extracted_intelligence"), list), "extracted_intelligence must be list"
    else:
        required = [
            "session_id", "scam_detected", "confidence_score", "agent_reply",
            "extracted_intelligence", "conversation_turns", "engagement_duration_seconds",
        ]
        for k in required:
            assert k in data, f"Missing key: {k}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
