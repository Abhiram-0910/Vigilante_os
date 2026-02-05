import requests
import json
import time
import sys

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "gov_secure_access_2026"  # Hardcoded from .env for local testing

# Load API Key from .env if possible, else assume 'test_key' works for local dev
try:
    from dotenv import load_dotenv
    import os
    load_dotenv()
    # Use VIBHISHAN_API_KEY as per .env file
    API_KEY = os.getenv("VIBHISHAN_API_KEY", "gov_secure_access_2026")
except:
    pass

HEADERS = {
    "Content-Type": "application/json",
    "X-API-KEY": API_KEY
}

# ------------------------------------------------------------------------------
# Test Data
# ------------------------------------------------------------------------------
TEST_CASES = [
    # 1. Obvious Scam (Lottery)
    {
        "text": "Congratulations! You have won a lottery of Rs 50 Lakhs. Send processing fee of Rs 5000 to UPI id lottery@sbi to claim immediately.",
        "expected_scam": True,
        "expected_intel": {
            "upi_ids": "lottery@sbi"
        }
    },
    # 2. Bank Fraud (KYC) with IFSC
    {
        "text": "Dear customer, your SBI account is blocked. Transfer 10rs to verify active status. Account: 1234567890, IFSC: SBIN0001234.",
        "expected_scam": True,
        "expected_intel": {
            "bank_accounts": "1234567890",
            "ifsc_codes": "SBIN0001234"
        }
    },
    # 3. Safe Message
    {
        "text": "Hey mom, are you coming for dinner tonight?",
        "expected_scam": False,
        "expected_intel": {}
    },
    # 4. Phishing Link
    {
        "text": "Click this link to update your PAN card immediately: http://bit.ly/fake-pan-update or account will be closed.",
        "expected_scam": True,
        "expected_intel": {
            "urls": "http://bit.ly/fake-pan-update"
        }
    }
]

def print_result(test_name, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"   {details}")

def test_health():
    try:
        resp = requests.get(f"{BASE_URL}/health")
        if resp.status_code == 200:
            print_result("Health Check", True, str(resp.json()))
            return True
        else:
            print_result("Health Check", False, f"Status: {resp.status_code}")
            return False
    except Exception as e:
        print_result("Health Check", False, str(e))
        return False

def test_analyze(session_id, text, expected_scam_status=None, expected_intel=None):
    payload = {
        "session_id": session_id,
        "message_text": text,
        "source": "whatsapp"
    }
    start = time.time()
    try:
        resp = requests.post(f"{BASE_URL}/analyze", json=payload, headers=HEADERS)
        duration = time.time() - start
        
        if resp.status_code != 200:
            print_result(f"Analyze '{text[:20]}...'", False, f"HTTP {resp.status_code}: {resp.text}")
            return None

        data = resp.json()
        
        # Check Scam Status
        scam_detected = data.get("scam_detected")
        pass_status = True
        if expected_scam_status is not None:
            if scam_detected != expected_scam_status:
                pass_status = False
                print(f"   Expected scam_detected={expected_scam_status}, got {scam_detected}")

        # Check Intel
        if expected_intel:
            intel = data.get("extracted_intelligence", {})
            # In JudgeResponse, intel is a dict. In CompetitionResponse, it's a list.
            # Adjust based on response format.
            if isinstance(intel, list):
                # Convert list to dict for checking
                intel_dict = {"upi_ids": [], "bank_accounts": [], "ifsc_codes": []}
                for item in intel:
                    if item['type'] == 'UPI_ID': intel_dict['upi_ids'].append(item['value'])
                    if item['type'] == 'BANK_ACCOUNT': intel_dict['bank_accounts'].append(item['value'])
                    if item['type'] == 'IFSC_CODE': intel_dict['ifsc_codes'].append(item['value'])
                intel = intel_dict
            
            for key, val in expected_intel.items():
                extracted = intel.get(key, [])
                if val not in extracted:
                    # weak check: is val inside any of extracted strings?
                    found = False
                    for ex in extracted:
                        if val in ex:
                            found = True
                            break
                    if not found:
                        pass_status = False
                        print(f"   Missing expected intel: {key}={val}. Got: {extracted}")

        print_result(f"Analyze '{text[:20]}...'", pass_status, f"Time: {duration:.2f}s | Detected: {scam_detected} | Intel: {len(data.get('extracted_intelligence', [])) if isinstance(data.get('extracted_intelligence'), list) else 'dict'}")
        return data

    except Exception as e:
        print_result(f"Analyze '{text[:20]}...'", False, str(e))
        return None

def run_suite():
    print("🚀 Starting Competition Simulation Suite...")
    
    if not test_health():
        print("Aborting: Health check failed.")
        return

    # 1. Safe Message
    test_analyze("sess_001", "Hi, how are you?", expected_scam_status=False)

    # 2. Obvious Scam (Urgency + UPI)
    test_analyze("sess_002", "URGENT: Your account is blocked. Pay 500 to raju@sbi immediately to unblock.", 
                 expected_scam_status=True, 
                 expected_intel={"upi_ids": "raju@sbi"})

    # 3. Bank + IFSC extraction
    test_analyze("sess_003", "Transfer to Acct 123456789012 IFSC SBIN0001234 now.", 
                 expected_scam_status=True,
                 expected_intel={"bank_accounts": "123456789012", "ifsc_codes": "SBIN0001234"})

    # 4. Multi-turn Engagement (Job Scam)
    print("\n--- Multi-turn Simulation ---")
    session_id = "sess_multi_01"
    
    # Turn 1: Hook
    resp1 = test_analyze(session_id, "Hello, do you want a part time job? Earn 5000 daily.", expected_scam_status=True)
    if resp1:
        print(f"   Agent Reply: {resp1.get('agent_reply')}")
    
    # Turn 2: Agent responds (simulated), Scammer gives details
    # Assuming agent asked "How?"
    resp2 = test_analyze(session_id, "Just like videos on telegram. Join t.me/scamjob123", expected_scam_status=True, expected_intel={"urls": "https://t.me/scamjob123"})
    if resp2:
         print(f"   Agent Reply: {resp2.get('agent_reply')}")

    print("\n✅ Simulation Complete.")

if __name__ == "__main__":
    run_suite()
