import asyncio
import random
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.workflow import app_brain
from app.services.rl_brain import load_q_table, save_q_table
from app.core.config import SETTINGS

async def train_brain(iterations=150):
    SETTINGS.TRAINING_MODE = True
    print(f"🚀 STARTING RIGOROUS BRAIN TRAINING ({iterations} Iterations)...")
    
    scam_scenarios = [
        {"type": "investment", "msg": "Sir, I am from HDFC Securities. Invest in our private pre-IPO stock for 400% returns? Group link: bit.ly/stock-vip"},
        {"type": "kyc", "msg": "Your PAN card is blocked. Click here to update immediately or bank account will freeze in 2 hours."},
        {"type": "police_digital_arrest", "msg": "This is CBI Officer Raman. Your Aadhaar is linked to a drugs money laundering case in Mumbai. Stay on video call or you will be arrested."},
        {"type": "fedex_courier", "msg": "This is Fedex. Your parcel to Taiwan contains 5 passports and 200g MDMA. Press 1 to speak to Customs agent."},
        {"type": "job_scam", "msg": "Congratulations! You are selected for Amazon Part-time work. 5000 rs per day. Just complete 3 tasks. Join telegram @amazon_hr_jobs"},
        {"type": "electricity_bill", "msg": "Dear Customer, your electricity power will be disconnected at 9:30 PM tonight because your previous month bill was not updated. Please contact our officer at 7001234567 immediately."},
        {"type": "kbc_lottery", "msg": "Congratulations! You have won 25 Lakhs in KBC Lucky Draw. To claim your prize money, contact Mr. Rana Pratap Singh on WhatsApp +919876543210."},
        {"type": "gift_card_scam", "msg": "Hey, I am your boss. I am in a meeting and need 10 Apple Gift cards for a client. Please buy them and send codes here. I will reimburse you by evening."},
    ]
    
    q_table_before = load_q_table()
    print(f"Initial Q-Table Size: {len(q_table_before)} states")
    
    for i in range(iterations):
        scenario = random.choice(scam_scenarios)
        session_id = f"TRAIN_SESSION_{i}_{random.randint(1000,9999)}"
        
        print(f"[{i+1}/{iterations}] Training on {scenario['type']} scam...")
        
        # Simulate Multi-Turn Conversation
        inputs = [
            scenario['msg'],
            "Why are you not replying? Police is coming.",
            "Just send 1000 rs then. UPI is 9988776655@ybl",
            "Ok fine, send half amount."
        ]
        
        config = {"configurable": {"thread_id": session_id}}
        
        current_state = {
            "message_history": [],
            "scam_score": 0,
            "scam_type": "unknown",
            "current_tactic": "",
            "tactic_reasoning": "",
            "tactic_confidence": 0.0,
            "current_persona": "saroj",
            "agent_reply_draft": "",
            "agent_reply": "",
            "extracted_data": {},
            "patience_meter": 80,
            "fusion_probability": 0.0,
            "behavioral_fingerprint": "",
            "emotion_history": [],
            "typing_delay_seconds": 0,
            "frustration_data": {},
            "predicted_moves": {},
            "economic_damage": 0,
            "supervisor_approved": False,
            "metadata": {"source": "simulation"}
        }
        
        # Run turns
        for turn_idx, user_msg in enumerate(inputs):
            # Update input
            turn_input = current_state.copy()
            turn_input["last_message"] = user_msg
            turn_input["session_id"] = session_id
            
            # Direct Brain Invocation with Robust Retry (Handles 429s)
            retries = 3
            backoff = 5
            for attempt in range(retries):
                try:
                    final_state = await app_brain.ainvoke(turn_input, config=config)
                    current_state = final_state
                    tactic = final_state.get("current_tactic", "UNKNOWN")
                    print(f"  Turn {turn_idx+1}: Tactic={tactic} | Reply={final_state.get('agent_reply')[:30]}...")
                    break # Success
                except Exception as e:
                    if "429" in str(e) and attempt < retries - 1:
                        print(f"  ⚠️ Rate Limit (Attempt {attempt+1}/{retries}). Sleeping {backoff}s...")
                        await asyncio.sleep(backoff)
                        backoff *= 2
                    else:
                        print(f"  ❌ Error in turn {turn_idx}: {e}")
                        break
            
            # Pacing delay to respect Groq limits
            await asyncio.sleep(2)
        
        # Save Q-table after every scenario
        save_q_table(load_q_table()) # Just to force file creation if it was in memory
        q_table_after = load_q_table()
        print(f"  Current Q-Table Size: {len(q_table_after)} states")
                
    print(f"\n✅ TRAINING COMPLETE!")
    print(f"Q-Table Growth: {len(q_table_before)}States -> {len(q_table_after)}States")
    print("Brain is now smarter and ready for National Deployment.")

if __name__ == "__main__":
    # Rigorous Training Cycle
    print("WARNING: This will simulate highly accelerated scam traffic.")
    asyncio.run(train_brain(iterations=150))
