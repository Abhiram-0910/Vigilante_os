import requests
import json
import time
import uuid

# TARGET PORT 8001
BASE_URL = "http://localhost:8001"
API_URL = f"{BASE_URL}/analyze_judge"
AUDIT_URL = f"{BASE_URL}/audit/verify-chain"
API_KEY = "gov_secure_access_2026"

def print_result(name, success, info=""):
    # Avoid Unicode on Windows cp1252 consoles
    symbol = "[PASS]" if success else "[FAIL]"
    print(f"{symbol} | {name:30} | {info}")

def test_audit():
    try:
        r = requests.get(AUDIT_URL)
        r.raise_for_status()
        data = r.json()
        print_result("Audit Chain Integrity", data.get("status") == "VERIFIED", f"Blocks: {data.get('blocks_checked')}")
    except Exception as e:
        print_result("Audit Chain Integrity", False, str(e))

def test_analyze():
    payload = {
        "session_id": str(uuid.uuid4()),
        "message_text": "Hello, interested in job.",
        "source": "whatsapp",
        "timestamp": "2026-02-04T12:00:00Z"
    }
    headers = {"X-API-KEY": API_KEY}
    
    start = time.time()
    try:
        r = requests.post(API_URL, json=payload, headers=headers)
        elapsed = (time.time() - start) * 1000
        r.raise_for_status()
        data = r.json()
        
        required = [
            "session_id",
            "scam_detected",
            "confidence_score",
            "agent_reply",
            "extracted_intelligence",
            "conversation_turns",
            "engagement_duration_seconds",
        ]
        print_result("Response Schema", all(k in data for k in required), "Validated")
        print_result("Latency (Normal)", elapsed < 1000, f"{elapsed:.1f}ms")
        print_result("Hinglish Presence", "yaar" in data.get("agent_reply", "").lower() or "..." in data.get("agent_reply", ""), "Detected")
        
    except Exception as e:
        print_result("Response Contract", False, str(e))

if __name__ == "__main__":
    print("="*60)
    print(" VIBHISHAN #1 RANK CERTIFICATION (Port 8001)")
    print("="*60)
    test_analyze()
    test_audit()
    print("="*60)
