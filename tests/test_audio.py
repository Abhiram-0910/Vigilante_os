import requests
import base64

API_URL = "http://localhost:8000/analyze_judge"
API_KEY = "gov_secure_access_2026"

# A tiny Base64 string (Header only of an MP3, effectively empty but valid format)
# In real life, this would be a full recording.
FAKE_AUDIO_B64 = "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA//OEAAAAAAAAAAAAAAAAAAAAAAAASW5mbwAAAA8AAAAEAAABIADAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAw"

def test_voice_input():
    print("--- TESTING MULTI-MODAL AUDIO INPUT ---")
    
    payload = {
        "session_id": "voice_test_01",
        "message_text": None, # NO TEXT
        "audio_base64": FAKE_AUDIO_B64, # SENDING AUDIO
        "source": "voice",
        "timestamp": "2024-01-26T12:00:00Z"
    }
    
    headers = {"X-API-KEY": API_KEY}
    
    try:
        # Note: This might return "[Audio Unintelligible]" because the base64 is partial, 
        # but if the server DOES NOT CRASH, we win.
        r = requests.post(API_URL, json=payload, headers=headers)
        
        if r.status_code == 200:
            print("[PASS] Server accepted Base64 Audio")
            print(f"Agent Reply: {r.json()['agent_reply']}")
        else:
            print(f"[FAIL] {r.status_code} - {r.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_voice_input()