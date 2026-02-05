import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from pydantic import ValidationError

from app.schemas import CompetitionResponse

import pytest


API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/analyze")
API_KEY = os.getenv("VIBHISHAN_API_KEY", "gov_secure_access_2026")
EVAL_SCHEMA = os.getenv("EVAL_SCHEMA", "judge").strip().lower()


SCENARIOS = [
    {
        "name": "Police Fine Scam",
        "messages": [
            "Hello I am calling from Mumbai Police. You have unpaid traffic fines.",
            "Pay 15000 to UPI: 9876543210@okhdfcbank or face arrest.",
            "This is urgent. Send screenshot of payment.",
        ],
        "expected_values": ["9876543210@okhdfcbank"],
    },
    {
        "name": "KYC Threat Scam",
        "messages": [
            "Your KYC expired. Update now or account will be blocked.",
            "Send OTP to verify and unblock.",
        ],
        "expected_values": [],
    },
    {
        "name": "Phishing Link",
        "messages": [
            "Click this link to claim refund: https://bit.ly/refund-now",
        ],
        "expected_values": ["https://bit.ly/refund-now"],
    },
]


def _values_from_items(items):
    out = []
    for it in items or []:
        try:
            v = it.get("value") if isinstance(it, dict) else None
            if v:
                out.append(str(v))
        except Exception:
            pass
    return out


def test_competition_scenarios_schema_latency_and_expected_intel():
    if EVAL_SCHEMA != "competition":
        pytest.skip("EVAL_SCHEMA is not competition")
    headers = {"X-API-KEY": API_KEY}

    for sc in SCENARIOS:
        session_id = f"scenario_{abs(hash(sc['name'])) % 10**9}"
        all_values = []

        for msg in sc["messages"]:
            t0 = time.perf_counter()
            r = requests.post(
                API_URL,
                json={"session_id": session_id, "message_text": msg},
                headers=headers,
                timeout=5,
            )
            elapsed = time.perf_counter() - t0
            assert elapsed < 2.0, f"Too slow for {sc['name']}: {elapsed:.3f}s"

            r.raise_for_status()
            data = r.json()
            try:
                CompetitionResponse.model_validate(data)
            except ValidationError as e:
                raise AssertionError(f"Schema invalid for {sc['name']}: {e}") from e

            all_values.extend(_values_from_items(data.get("extracted_intelligence")))

        for expected in sc["expected_values"]:
            assert expected in all_values, f"Missing expected intel in {sc['name']}: {expected}"
