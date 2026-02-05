# /app/services/fast_cache.py
import random

class FastReflexCache:
    """
    Zero-Latency Reflex Layer.
    Bypasses LLM for common greetings/short phrases to lower average API latency.
    """
    
    def __init__(self):
        self.common_inputs = {
            "hi": ["Hello ji!", "Haan bolo?", "Hi, who is this?", "Namaste."],
            "hello": ["Hello?", "Yes?", "Hello ji, kaun?", "Haan boliye."],
            "hey": ["Yes?", "Who is this?", "Haan bhai bolo."],
            "good morning": ["Good morning ji.", "Morning. Who is this?"],
            "namaste": ["Namaste.", "Ram Ram ji. Kaun?"],
            "ok": ["Hmm.", "Ok.", "Accha."],
            "okay": ["Ok ji.", "Thik hai."],
            "yes": ["Hmm.", "Bolo."],
            "no": ["Ok.", "Why?"],
        }

    def get_cached_reply(self, text: str) -> str:
        """Returns a cached reply if available, else None."""
        clean_text = text.strip().lower()
        
        # Remove common punctuation for better matching
        clean_text = clean_text.strip(".,?!")
        
        if clean_text in self.common_inputs:
            return random.choice(self.common_inputs[clean_text])
        return None

# Singleton
fast_cache = FastReflexCache()