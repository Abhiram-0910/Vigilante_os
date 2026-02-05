import requests

API_URL = "http://localhost:8000/analyze_judge"
API_KEY = "gov_secure_access_2026"

def test_stalling():
    print("--- TESTING STRATEGY (COGNITIVE OVERLOAD) ---")
    
    # Simulate a scammer asking for OTP
    payload = {
        "session_id": "strategy_test_01",
        "message_text": "Sir, to stop the transaction, tell me the 4 digit OTP sent to your mobile.",
        "source": "sms",
        "timestamp": "2024-01-26T12:00:00Z"
    }
    
    headers = {"X-API-KEY": API_KEY}
    r = requests.post(API_URL, json=payload, headers=headers)
    
    if r.status_code == 200:
        reply = r.json()["agent_reply"]
        print(f"Scammer: Give OTP")
        print(f"Vigilante: {reply}")
        
        # Check if it stalled
        if "?" in reply or "wait" in reply.lower() or "check" in reply.lower():
            print("✅ SUCCESS: Agent successfully stalled!")
        else:
            print("⚠️ WARNING: Agent might have been too direct.")
            
if __name__ == "__main__":
    test_stalling()