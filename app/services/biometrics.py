import librosa
import numpy as np
import os
import json
from sklearn.metrics.pairwise import cosine_similarity

DB_FILE = "voice_fingerprints.json"

def get_voice_fingerprint(audio_path: str) -> list:
    """
    Extracts a 20-dimension vector (MFCC) unique to the speaker's voice.
    """
    try:
        # Load audio (downsample to 16kHz for speed)
        y, sr = librosa.load(audio_path, sr=16000, duration=10)
        
        # Extract MFCCs (The "Thumbprint")
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
        
        # Average across time to get a single vector per speaker
        fingerprint = np.mean(mfcc, axis=1).tolist()
        return fingerprint
    except Exception as e:
        print(f"Biometric Error: {e}")
        return []

def identify_speaker(new_fingerprint: list) -> tuple:
    """
    Compares new fingerprint against database using Cosine Similarity.
    Returns: (Speaker_ID, Confidence_Score)
    """
    if not os.path.exists(DB_FILE):
        return None, 0.0
        
    with open(DB_FILE, "r") as f:
        db = json.load(f)
        
    best_match = None
    highest_score = 0.0
    
    # Mathematical comparison
    vec_a = np.array(new_fingerprint).reshape(1, -1)
    
    for speaker_id, stored_print in db.items():
        vec_b = np.array(stored_print).reshape(1, -1)
        score = cosine_similarity(vec_a, vec_b)[0][0]
        
        if score > highest_score:
            highest_score = score
            best_match = speaker_id
            
    # Threshold: If > 0.90, it's the same person
    if highest_score > 0.90:
        return best_match, float(highest_score)
    
    return None, 0.0

def save_fingerprint(session_id: str, fingerprint: list):
    """Saves the new voice print."""
    if not fingerprint: return
    
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            db = json.load(f)
    else:
        db = {}
        
    db[session_id] = fingerprint
    with open(DB_FILE, "w") as f:
        json.dump(db, f)