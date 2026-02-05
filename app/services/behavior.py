import hashlib


def generate_behavioral_fingerprint(text: str, voice_mfcc: list = None) -> str:
    """
    UPGRADE #2: Behavioral Fingerprint.
    Creates a unique ID based on typing style + voice signature.
    Format: [TYPE]_[LENGTH]_[VOCAB]_[VOICE_HASH]
    """
    # 1. Text Analysis
    avg_word_len = sum(len(w) for w in text.split()) / (len(text.split()) + 1)
    type_speed_tag = "SHORT" if len(text) < 20 else "LONG"
    
    vocab_tag = "URGENT" if "now" in text.lower() else "PASSIVE"
    
    # 2. Voice Hash (if available)
    voice_tag = "NOVOICE"
    if voice_mfcc:
        # Simple hash of the vector to get a consistent string
        voice_str = str(voice_mfcc[:5]) # First 5 dims
        voice_tag = hashlib.md5(voice_str.encode()).hexdigest()[:6]
        
    fingerprint = f"{type_speed_tag}_{vocab_tag}_{voice_tag}".upper()
    return fingerprint


def correlate_identity(fingerprint: str, upi_list: list) -> dict:
    """
    UPGRADE #51: Cross-Channel Intelligence Correlation.
    """
    # In-memory graph simulation for the hackathon
    syndicate_map = {
        "ALPHA": ["raju@sbi", "8887776661"],
        "BETA": ["link-shortener.com/scam"]
    }
    for upi in upi_list:
        if upi in syndicate_map["ALPHA"]:
            return {"syndicate": "ALPHA", "risk": "CRITICAL"}
    return {"syndicate": "NEW", "risk": "MEDIUM"}


class GNNPredictor:
    """
    Simulates a Graph Neural Network (GNN) for syndicate mapping.
    Predicts probability of a session belonging to an organized crime cluster.
    """
    def predict_cluster_probability(self, nodes: list, edges: list) -> float:
        # Logistic activation simulation based on edge density
        if not nodes: return 0.0
        density = len(edges) / len(nodes)
        prob = 1 / (1 + 2.718**(-density))
        return round(prob, 4)


gnn_engine = GNNPredictor()