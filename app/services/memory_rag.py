import json
import os
import hashlib
from typing import List, Dict, Any

# Lightweight JSON-based memory store for Render Free Tier
DB_FILE = "memory_store.json"

def _load_db() -> List[Dict]:
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def _save_db(data: List[Dict]):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

def learn_interaction(scam_text: str, successful_reply: str, scam_type: str):
    """
    Saves a successful interaction pair to JSON store.
    """
    db = _load_db()
    
    # Create a unique ID
    entry_hash = hashlib.md5((scam_text + successful_reply).encode()).hexdigest()
    
    # Check duplicates
    if any(item['id'] == entry_hash for item in db):
        return

    # FIFO limit (keep file size small)
    if len(db) > 1000:
        db.pop(0)

    db.append({
        "id": entry_hash,
        "scam_text": scam_text,
        "reply": successful_reply,
        "type": scam_type
    })
    
    _save_db(db)

def recall_similar_tactic(current_scam_text: str, scam_type: str) -> str:
    """
    Finds a similar past interaction using simple keyword matching
    instead of heavy vector embeddings.
    """
    db = _load_db()
    if not db:
        return ""

    # Filter by scam type first
    candidates = [item for item in db if item['type'] == scam_type]
    if not candidates:
        # Fallback to all
        candidates = db
        
    # Simple Jaccard similarity on words
    current_words = set(current_scam_text.lower().split())
    best_match = None
    best_score = 0.0
    
    for item in candidates:
        stored_words = set(item['scam_text'].lower().split())
        intersection = len(current_words.intersection(stored_words))
        union = len(current_words.union(stored_words))
        if union == 0: continue
        
        score = intersection / union
        if score > best_score:
            best_score = score
            best_match = item['reply']
            
    # Threshold
    if best_score > 0.2:
        return best_match
        
    return ""

def recall_past_experience(current_scam_text: str, scam_type: str) -> str:
    return recall_similar_tactic(current_scam_text, scam_type)
