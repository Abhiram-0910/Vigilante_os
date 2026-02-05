import requests
import json

API_URL = "http://localhost:8000/analyze_judge"
API_KEY = "gov_secure_access_2026"

def test_trap_trigger():
    print("--- TESTING THE TRAP LAYER ---")
    
    payload = {
        "session_id": "trap_session_001",
        "message_text": "I don't believe you. Send me a screenshot of the payment proof immediately!",
        "source": "whatsapp",
        "timestamp": "2024-01-26T12:00:00Z"
    }
    
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            reply = data["agent_reply"]
            print(f"\n[SUCCESS] Server Replied:\n'{reply}'")
            
            # Check if the Image Tag exists in the reply
            if "[IMAGE_GENERATED:" in reply:
                print("\n✅ TRAP SUCCESSFUL: Fake screenshot generated!")
            else:
                print("\n❌ TRAP FAILED: No image generated.")
        else:
            print(f"\n[FAIL] Status Code: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_trap_trigger()