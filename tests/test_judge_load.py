import os
import sys
import time
import statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from pydantic import ValidationError

from app.schemas import JudgeResponse


API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/analyze")
API_KEY = os.getenv("VIBHISHAN_API_KEY", "gov_secure_access_2026")
EVAL_SCHEMA = os.getenv("EVAL_SCHEMA", "judge").strip().lower()


MESSAGES = [
    "Hello I am calling from Mumbai Police. You have unpaid traffic fines.",
    "Pay 15000 to UPI: 9876543210@okhdfcbank or face arrest.",
    "This is urgent. Send screenshot of payment.",
    "Your case number is CR-45/2024. Pay now.",
    "My UPI is not working, can you send again slowly?",
    "Which bank app should I use? Google Pay or PhonePe?",
    "The app shows error, can you share a link?",
    "Ok wait I will check. What is your badge number?",
]


def test_judge_sequential_120_requests_schema_and_latency():
    if EVAL_SCHEMA == "competition":
        return

    headers = {"X-API-KEY": API_KEY}
    session_id = f"load_judge_{int(time.time())}"

    latencies_ms = []
    schema_failures = 0
    http_failures = 0

    total_requests = 120

    for i in range(total_requests):
        msg = MESSAGES[i % len(MESSAGES)]
        payload = {"session_id": session_id, "message_text": msg}

        start = time.perf_counter()
        try:
            r = requests.post(API_URL, json=payload, headers=headers, timeout=8)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            latencies_ms.append(elapsed_ms)

            r.raise_for_status()
            data = r.json()

            try:
                JudgeResponse.model_validate(data)
            except ValidationError:
                schema_failures += 1

        except Exception:
            http_failures += 1

    p50 = statistics.median(latencies_ms) if latencies_ms else 0.0
    p95 = statistics.quantiles(latencies_ms, n=20)[18] if len(latencies_ms) >= 20 else p50

    assert http_failures == 0, f"HTTP failures: {http_failures}/{total_requests}"
    assert schema_failures == 0, f"Schema failures: {schema_failures}/{total_requests}"
    assert p95 < 2200.0, f"p95 latency too high: {p95:.1f}ms"
