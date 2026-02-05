import requests
import random
import time
import uuid
from datetime import datetime, timedelta

API_URL = "http://localhost:8000/analyze_judge"
API_KEY = "gov_secure_access_2026"
HEADERS = {"X-API-KEY": API_KEY}

# Data Pools for realism
SCAM_TYPES = ["KYC Fraud", "Lottery Scam", "Sextortion", "Job Scam", "Electricity Bill"]
LOCATIONS = [
    {"lat": 28.7041, "lon": 77.1025, "region": "Delhi"},
    {"lat": 19.0760, "lon": 72.8777, "region": "Mumbai"},
    {"lat": 22.5726, "lon": 88.3639, "region": "Kolkata"},
    {"lat": 12.9716, "lon": 77.5946, "region": "Bangalore"},
    {"lat": 26.8467, "lon": 80.9462, "region": "Lucknow"},
    {"lat": 25.3176, "lon": 82.9739, "region": "Varanasi"}, # Jamtara vibes
]

# Shared identifiers to create "Syndicates" (Red Lines)
SHARED_UPIS = ["raju@sbi", "scam_boss@paytm", "fast_money@ybl"]

def generate_fake_traffic(n=50):
    print(f"🚀 SEEDING {n} INTERACTIONS FOR DASHBOARD...")
    
    for i in range(n):
        # 1. Randomize context
        loc = random.choice(LOCATIONS)
        scam_type = random.choice(SCAM_TYPES)
        
        # 2. Inject Syndicate Links (20% chance to share a known UPI)
        if random.random() < 0.20:
            msg_text = f"Pay immediately to {random.choice(SHARED_UPIS)} or police will come."
        else:
            msg_text = f"Sir you won lottery! Send fees to {uuid.uuid4().hex[:6]}@upi."

        # 3. Payload
        payload = {
            "session_id": f"seed_{uuid.uuid4().hex[:8]}",
            "message_text": msg_text,
            "source": random.choice(["whatsapp", "sms", "telegram"]),
            "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 120))).isoformat(),
            "metadata": {
                "lat": loc["lat"] + random.uniform(-0.1, 0.1), # Jitter location
                "lon": loc["lon"] + random.uniform(-0.1, 0.1),
                "sender_phone": f"+91{random.randint(6000000000, 9999999999)}"
            }
        }

        # 4. Fire Request (ignore errors, just filling DB)
        try:
            requests.post(API_URL, json=payload, headers=HEADERS, timeout=1)
            print(f"  [+] Seeded {scam_type} in {loc['region']}")
        except:
            pass
        
        # Fast burst
        time.sleep(0.05)

    print("\n✅ DASHBOARD PRE-SEEDED. '4D Intelligence' graph is now active.")

if __name__ == "__main__":
    generate_fake_traffic(50)