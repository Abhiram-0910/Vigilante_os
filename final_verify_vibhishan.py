import sys
import os
import json
import asyncio
from unittest.mock import MagicMock

# Add app to path
sys.path.append(os.getcwd())

async def verify_system():
    print("--- VIBHISHAN FINAL VERIFICATION ---")
    
    # 1. Verify Voice Cloning Consistency
    from app.services.voice_out import get_cloned_voice_params, generate_voice_reply
    print("\n[1] Verifying Voice Cloning...")
    saroj_params = get_cloned_voice_params("saroj")
    tech_bro_params = get_cloned_voice_params("tech_bro")
    print(f"Saroj Labels: {saroj_params['label']} (Consistent: {saroj_params['slow'] == True})")
    print(f"TechBro Labels: {tech_bro_params['label']} (Consistent: {tech_bro_params['slow'] == False})")
    
    # 2. Verify Messaging Adapters
    from app.adapters.messaging import PlatformAdapter
    print("\n[2] Verifying Messaging Adapters...")
    wa_payload = {
        'entry': [{'changes': [{'value': {
            'messages': [{'from': '919876543210', 'text': {'body': 'Hello beta'}}]
        }}]}]
    }
    wa_msg = PlatformAdapter.parse_whatsapp_webhook(wa_payload)
    if wa_msg and wa_msg.session_id == "wa_919876543210":
        print("WhatsApp Parse: SUCCESS")
    else:
        print("WhatsApp Parse: FAILED")
        
    tg_payload = {
        'message': {'chat': {'id': '12345'}, 'text': 'I am fine'}
    }
    tg_msg = PlatformAdapter.parse_telegram_webhook(tg_payload)
    if tg_msg and tg_msg.session_id == "tg_12345":
        print("Telegram Parse: SUCCESS")
    else:
        print("Telegram Parse: FAILED")

    # 3. Verify Dashboard Demo Triggers
    from dashboard import build_enhanced_network
    print("\n[3] Verifying Dashboard Syndicate Logic...")
    test_data = {
        "S1": {"extracted": {"upi_ids": ["raju@sbi"]}, "scam_score": 90, "timestamp": 123},
        "S2": {"extracted": {"upi_ids": ["raju@sbi"]}, "scam_score": 85, "timestamp": 124}
    }
    G, detected, details = build_enhanced_network(test_data)
    if detected and len(details["upi_collisions"]) > 0:
        print("Syndicate Detection logic: SUCCESS (Smoking Gun Found)")
    else:
        print("Syndicate Detection logic: FAILED")

    print("\n--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(verify_system())
