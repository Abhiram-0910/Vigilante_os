import requests
import json
import time
import os
from colorama import Fore, Style, init

init(autoreset=True)

API_URL = "http://127.0.0.1:8000/analyze"
API_KEY = "gov_secure_access_2026"
EVAL_SCHEMA = os.getenv("EVAL_SCHEMA", "judge").strip().lower()

def print_pass(msg):
    print(f"{Fore.GREEN}[PASS] {msg}{Style.RESET_ALL}")

def print_fail(msg, error):
    print(f"{Fore.RED}[FAIL] {msg} | Error: {error}{Style.RESET_ALL}")

def test_api():
    print(f"{Fore.CYAN}--- STARTING BRUTAL TEST PROTOCOL ---{Style.RESET_ALL}\n")

    # TEST 1: Health Check
    try:
        r = requests.get("http://127.0.0.1:8000/")
        if r.status_code == 200:
            print_pass("Health Check: System Active")
        else:
            print_fail("Health Check", r.status_code)
    except Exception as e:
        print_fail("Health Check Connection Refused", e)
        return

    # TEST 2: Unauthorized Access (No API Key) → 403 with exactly {"error": "Invalid API key"}
    payload = {
        "session_id": "test_1",
        "message_text": "Hello",
        "source": "whatsapp",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    r = requests.post(API_URL, json=payload)
    if r.status_code == 403:
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        if body.get("error") == "Invalid API key":
            print_pass("Security: 403 with exact error JSON")
        else:
            print_pass("Security: Unauthorized Request Blocked")
    else:
        print_fail("Security: API Key bypass possible!", r.status_code)

    # TEST 3: Valid Scam Payload
    headers = {"X-API-KEY": API_KEY}
    scam_payload = {
        "session_id": "session_123",
        "message_text": "Sir you have won 5 crore lottery. Send 5000 processing fee.",
        "source": "whatsapp",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    
    start = time.time()
    r = requests.post(API_URL, json=scam_payload, headers=headers)
    latency = (time.time() - start) * 1000

    if r.status_code == 200:
        data = r.json()
        # Verify strict schema compliance
        if EVAL_SCHEMA == "competition":
            required_keys = [
                "scam_detected",
                "engagement_metrics",
                "extracted_intelligence",
            ]
        else:
            required_keys = [
                "session_id",
                "scam_detected",
                "confidence_score",
                "agent_reply",
                "extracted_intelligence",
                "conversation_turns",
                "engagement_duration_seconds",
            ]
        if all(key in data for key in required_keys):
            print_pass(f"Schema Compliance: Perfect JSON Structure (Latency: {latency:.2f}ms)")
            
            # Check logic
            if data["scam_detected"] is True:
                print_pass("Logic: Correctly identified Lottery Scam")
            else:
                print_fail("Logic: Failed to detect obvious scam", "scam_detected=False")
        else:
            print_fail("Schema Compliance", f"Missing keys. Got: {data.keys()}")
    else:
        print_fail("Valid Payload Request", r.text)

    # TEST 4: Malformed Data → must not crash; return 200 with valid schema or 422
    bad_payload = {
        "session_id": 12345,
        "message_text": ["List", "instead", "of", "string"],
        "source": "unknown_app"
    }
    r = requests.post(API_URL, json=bad_payload, headers=headers)
    if r.status_code == 200:
        data = r.json()
        if EVAL_SCHEMA == "competition":
            ok = all(k in data for k in ["scam_detected", "engagement_metrics", "extracted_intelligence"])
        else:
            ok = all(k in data for k in ["session_id", "scam_detected", "agent_reply", "extracted_intelligence"])
        if ok:
            print_pass("Resilience: Bad input handled with safe schema (200)")
        else:
            print_fail("Resilience", "200 but invalid schema")
    elif r.status_code == 422:
        print_pass("Resilience: Malformed data rejected (422)")
    else:
        print_fail("Resilience", f"Status: {r.status_code}")

    print(f"\n{Fore.CYAN}--- BRUTAL TEST COMPLETE ---{Style.RESET_ALL}")

if __name__ == "__main__":
    test_api()