# /app/services/psych_profiler.py
import re
import time

class PsychProfiler:
    def __init__(self):
        self.profanity_list = [
            "idiot", "stupid", "mad", "hell", "fuck", "bitch", "scam", "waste", "police", "jail",
            "kutta", "badmash", "haramkhor", "ganda", "pagal", "chutiya", "ullu", "bewaquf"
        ]
        
    def calculate_frustration(self, current_msg: str, history: list) -> dict:
        """
        Calculates Frustration Score based on Indian scammer behavior patterns.
        """
        score = 0
        reasons = []
        
        # 1. Profanity Check (Hindi/English Hybrid)
        clean_msg = current_msg.lower()
        profanity_hits = [w for w in self.profanity_list if w in clean_msg]
        if profanity_hits:
            score += 25 * len(profanity_hits)
            reasons.append(f"Verbal Aggression ({', '.join(profanity_hits[:2])})")
            
        # 2. CAPSLOCK RAGE (Signs of high stress)
        if len(current_msg) > 5 and sum(1 for c in current_msg if c.isupper()) / len(current_msg) > 0.7:
            score += 20
            reasons.append("Yelling (High Caps)")
            
        # 3. Urgency/Pressure Keywords (Metric 2 Correlation)
        urgency_words = ["now", "immediately", "fast", "quick", "within", "last warning", "final", "hurry"]
        urgency_count = sum(1 for w in urgency_words if w in clean_msg)
        if urgency_count > 0:
            score += 10 * urgency_count
            reasons.append("High Pressure Tactics")

        return {
            "frustration_score": min(100, score),
            "breaking_point_eta": f"{max(1, 8 - (score // 12))} turns",
            "psych_state": "Enraged" if score > 60 else "Highly Aggressive" if score > 40 else "Annoyed" if score > 20 else "Balanced"
        }

    def calculate_economic_damage(self, duration_seconds: float) -> float:
        """
        Calculates Opportunity Cost for the Scammer.
        Basis: ₹1,200/hr (Calibrated to 2024-2025 organizational overhead of major syndicates).
        """
        hourly_rate_inr = 1200.0 
        damage = (duration_seconds / 3600.0) * hourly_rate_inr
        return round(damage, 2)

psych_engine = PsychProfiler()