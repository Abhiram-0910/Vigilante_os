import json
import os
import numpy as np

DB_FILE = "voice_fingerprints.json"

def get_voice_fingerprint(audio_path: str) -> list:
    """
    STUB: Audio processing is disabled for Render deployment.
    """
    return []

def identify_speaker(new_fingerprint: list) -> tuple:
    """
    STUB: Audio processing is disabled for Render deployment.
    """
    return None, 0.0

def save_fingerprint(session_id: str, fingerprint: list):
    """Saves the new voice print."""
    if not fingerprint:
        return
        
    db = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                db = json.load(f)
        except:
            db = {}
    
    db[session_id] = fingerprint
    
    with open(DB_FILE, "w") as f:
        json.dump(db, f)
