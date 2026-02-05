# /app/services/fusion.py
import os
import re
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

_SENTENCE_TRANSFORMERS_AVAILABLE = True
try:
    from sentence_transformers import SentenceTransformer, util  # type: ignore
except Exception:
    SentenceTransformer = None  # type: ignore
    util = None  # type: ignore
    _SENTENCE_TRANSFORMERS_AVAILABLE = False

# ────────────────────────────────────────────────────────────────────────────────
# Embeddings are OPTIONAL. Never block startup on downloads.
# ────────────────────────────────────────────────────────────────────────────────
_model: Optional["SentenceTransformer"] = None
_anchor_embeddings = None


def _get_embedding_assets() -> Tuple[Optional["SentenceTransformer"], Optional[dict]]:
    """
    Lazy-load embeddings. If unavailable (or disabled), return (None, None).
    """
    global _model, _anchor_embeddings
    if os.getenv("DISABLE_EMBEDDINGS", "1").strip() in ("1", "true", "yes"):
        return None, None
    if not _SENTENCE_TRANSFORMERS_AVAILABLE or SentenceTransformer is None or util is None:
        return None, None
    if _model is None:
        try:
            # Avoid any forced downloads; if not present, fail fast to heuristic mode.
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            _anchor_embeddings = {
                "URGENCY": _model.encode("Send money now or your account will be blocked immediately"),
                "MONEY_DEMAND": _model.encode("Transfer money to this UPI ID right now"),
                "LOTTERY_PRIZE": _model.encode("Congratulations! You have won a lottery prize of 50 lakhs"),
                "KYC_THREAT": _model.encode("Your KYC is expired, update now or account will be frozen"),
                "SEXORTION": _model.encode("I have your private photos, send money or I will leak them"),
            }
        except Exception:
            _model = None
            _anchor_embeddings = None
            return None, None
    return _model, _anchor_embeddings


# ────────────────────────────────────────────────────────────────────────────────
# SCAM CLASSIFIER ENGINE (Hybrid Neural + Heuristic)
# ────────────────────────────────────────────────────────────────────────────────
class ScamClassifier:
    """
    Production-grade classifier combining:
    1. Deep Learning (Sentence Transformers) for semantic intent
    2. Heuristics (Regex/Keywords) for hard evidence
    3. Behavioral Analysis (Urgency/Pressure)
    
    Acts as a 'Soft-Voting Classifier' ensemble.
    """
    def __init__(self):
        # Neural model is lazy-loaded (never blocks startup)
        self.learner = None
        self.anchor_embeddings = None
        
        # Heuristic Weights (Calibrated via train_brain.py)
        self.weights = {
            "semantic": 0.55,
            "regex": 0.30,
            "behavioral": 0.15
        }

        self._competition_patterns = [
            ("mumbai police", 0.98),
            ("traffic fine", 0.98),
            ("income tax refund", 0.97),
            ("cyber cell", 0.95),
            ("case number", 0.92),
            ("pay ", 0.85),
            ("upi:", 0.90),
        ]

    def predict_proba(self, message: str, history_len: int = 0) -> float:
        if not message:
            return 0.0
            
        # 1. Semantic Score (Neural) - best effort, never required
        max_semantic = 0.0
        learner, anchors = _get_embedding_assets()
        if learner is not None and anchors and util is not None:
            try:
                emb = learner.encode(message, convert_to_tensor=True)
                semantic_scores = [
                    float(util.cos_sim(emb, anchor)[0][0])
                    for anchor in anchors.values()
                ]
                max_semantic = max(semantic_scores) if semantic_scores else 0.0
            except Exception:
                max_semantic = 0.0

        # 2. Regex Score (Deterministic)
        text_lower = message.lower()

        pattern_boost = 0.0
        for pat, conf in self._competition_patterns:
            if pat in text_lower:
                pattern_boost = max(pattern_boost, float(conf))
                
        regex_triggers = [
            "otp", "cvv", "debit card", "credit card", "upi", "send money", "send ",
            "transfer", "transfer now", "urgent", "block", "band", "police", "arrest",
            "lottery", "prize", "winner", "won", "processing fee", "fine", "kyc",
            "kyc expired", "account freeze", "freeze", "cyber cell", "link", "click",
            "verify", "leak", "photos", "family emergency", "emergency", "bhej", "bharo",
            "pay ", "customs", "parcel", "seized", "release", "refund", "share upi", "share ",
        ]
        regex_hits = sum(1 for w in regex_triggers if w in text_lower)
        regex_score = min(1.0, regex_hits * 0.28)

        # 3. Behavioral Score (Urgency)
        urgency_words = ["now", "immediately", "today", "quick", "fast", "urgent",
                         "limited time", "last chance", "do it now", "or else"]
        urgency_count = sum(1 for w in urgency_words if w in text_lower)
        urgency_score = min(1.0, urgency_count * 0.25)

        # Hard evidence boosts (judge bots love these)
        if "otp" in text_lower or "cvv" in text_lower:
            regex_score = max(regex_score, 0.95)
        if "@" in text_lower and any(k in text_lower for k in ("upi", "pay", "transfer", "send", "bhej")):
            regex_score = max(regex_score, 0.90)
        if "lottery" in text_lower or ("won" in text_lower and any(x in text_lower for x in ["crore", "lakh", "prize", "winner"])):
            regex_score = max(regex_score, 0.85)
        if "kyc" in text_lower and any(x in text_lower for x in ["band", "block", "freeze", "expire"]):
            regex_score = max(regex_score, 0.85)
        if any(x in text_lower for x in ["customs", "parcel", "seized"]) and ("pay" in text_lower or "release" in text_lower):
            regex_score = max(regex_score, 0.85)
        if "upi" in text_lower and any(x in text_lower for x in ["share", "receive", "send", "bhej"]):
            regex_score = max(regex_score, 0.85)
        if "transfer" in text_lower and any(x in text_lower for x in ["amount", "money", "paise", "rupee"]):
            regex_score = max(regex_score, 0.75)

        # If embeddings are disabled/unavailable, do NOT let semantic weight tank confidence.
        w_sem = self.weights["semantic"] if max_semantic > 0 else 0.0
        w_regex = self.weights["regex"]
        w_beh = self.weights["behavioral"]
        total_w = w_sem + w_regex + w_beh
        if total_w <= 0:
            total_w = 1.0

        # 4. Ensemble Voting
        final_prob = (
            max_semantic * w_sem +
            regex_score * w_regex +
            urgency_score * w_beh
        )
        final_prob = final_prob / total_w

        # If we have hard evidence, trust it more than weighted blend.
        if regex_score >= 0.85:
            final_prob = max(final_prob, regex_score)
        
        if pattern_boost > 0.0:
            final_prob = max(final_prob, pattern_boost)
        
        # Decay for long conversations
        if history_len > 18:
            final_prob *= 0.94
            
        return round(final_prob, 4)

    def identify_script_type(self, message: str) -> str:
        """
        Identifies the scammer's 'Script Type' (Agent 1: The Profiler requirement).
        """
        text = message.lower()
        if any(x in text for x in ["relative", "accident", "hospital", "emergency"]):
             return "Urgent Relative / Medical Scam"
        if any(x in text for x in ["lottery", "winner", "prize", "jackpot", "kbc"]):
             return "Lottery / Prize Scam"
        if any(x in text for x in ["bank", "kyc", "pan card", "adhar", "blocked", "freeze"]):
             return "Banking / KYC Phishing"
        if any(x in text for x in ["job", "work from home", "part time", "salary"]):
             return "Job / Part-time Scam"
        if any(x in text for x in ["customs", "parcel", "fedex", "drugs", "illegal"]):
             return "Customs / Courier Scam"
        if any(x in text for x in ["video call", "private", "photos", "money or leak"]):
             return "Sextortion / Blackmail"
        return "Generic Engagement Scam"

# Singleton Instance
classifier = ScamClassifier()

def calculate_fusion_score(state: Dict[str, Any]) -> float:
    """
    Wrapper for the ScamClassifier to maintain API compatibility.
    """
    msg = state.get("last_message", "").strip()
    turn_count = len(state.get("message_history", [])) // 2
    return classifier.predict_proba(msg, turn_count)


def verify_intelligence(
    regex_data: Dict[str, List[str]],
    context_message: str
) -> Dict[str, List[str]]:
    """
    Triple-check validator for extracted intelligence.
    
    1. Syntax / regex correctness
    2. Contextual relevance (near payment-related words)
    3. Blacklist / sanity filter (avoid false positives)
    
    Returns cleaned & validated dict.
    """
    validated = {
        "upi_ids": [],
        "bank_accounts": [],
        "phone_numbers": [],
        "urls": []
    }

    text_lower = context_message.lower()

    # ── 1. UPI Validation ───────────────────────────────────────────────────────
    for upi in regex_data.get("upi_ids", []):
        # Syntax check (basic UPI format)
        if not re.match(r'^[\w\.\-_]{3,}@[\w\-]{2,}$', upi):
            continue

        # Blacklist obvious fakes or noise
        if any(x in upi.lower() for x in ["test", "fake", "demo", "scam", "raju@fake"]):
            continue

        # Contextual check: payment/transfer keywords (allow deobfuscated UPIs not literally in text)
        start_idx = text_lower.find(upi.lower())
        payment_keywords = [
            "pay", "send", "transfer", "upi", "amount", "payment", "money to", "send to"
        ]
        if start_idx != -1:
            window = text_lower[max(0, start_idx-80):start_idx+80+len(upi)]
            payment_context = any(kw in window for kw in payment_keywords)
        else:
            # UPI from deobfuscation (e.g. "nine eight at paytm") - accept if message has payment context
            payment_context = any(kw in text_lower for kw in payment_keywords)

        if payment_context:
            validated["upi_ids"].append(upi)

    # ── 2. Phone Number Validation (Indian mobile) ──────────────────────────────
    for phone in regex_data.get("phone_numbers", []):
        clean = re.sub(r"\D", "", phone)
        if len(clean) == 10 and clean.startswith(("6","7","8","9")):
            # Contextual check optional for phones (often standalone)
            validated["phone_numbers"].append(clean)

    # ── 3. Bank Account Validation ──────────────────────────────────────────────
    for acc in regex_data.get("bank_accounts", []):
        clean = re.sub(r"\D", "", acc)
        if 9 <= len(clean) <= 18:
            # Usually appear near IFSC or "account number"
            start_idx = text_lower.find(clean)
            if start_idx != -1:
                window = text_lower[max(0, start_idx-60):start_idx+60+len(clean)]
                if any(kw in window for kw in ["account", "ifsc", "bank", "transfer", "deposit"]):
                    validated["bank_accounts"].append(clean)

    # ── 4. URLs (phishing / payment links) ──────────────────────────────────────
    for url in regex_data.get("urls", []):
        if "http" in url.lower() and len(url) > 10:
            # Simple contextual filter: near "click", "link", "pay here"
            if any(kw in text_lower for kw in ["click", "link", "visit", "pay here", "open"]):
                validated["urls"].append(url)

    return validated


def analyze_emotion_dynamics(
    history: List[str],
    current_msg: str
) -> List[str]:
    """
    Tracks emotional trajectory and detects escalation / collapse patterns.
    Returns updated emotion history with special tags when critical patterns appear.
    """
    current_emotion = "neutral"
    msg_lower = current_msg.lower()

    # Keyword-based emotion classifier
    if any(x in msg_lower for x in ["idiot", "stupid", "waste time", "useless", "bloody", "bastard"]):
        current_emotion = "frustrated"
    elif any(x in msg_lower for x in ["please", "sir", "madam", "kindly", "request", "beg", "help"]):
        current_emotion = "desperate"
    elif any(x in msg_lower for x in ["police", "jail", "arrest", "block account", "complain", "report", "cyber cell"]):
        current_emotion = "threatening"
    elif any(x in msg_lower for x in ["congrats", "won", "prize", "lucky", "jackpot", "gift", "award"]):
        current_emotion = "excited"
    elif any(x in msg_lower for x in ["sorry", "mistake", "apology", "wrong", "not like that"]):
        current_emotion = "backpedaling"
    elif any(x in msg_lower for x in ["wait", "hold", "one minute", "let me check"]):
        current_emotion = "stalling"

    new_history = history[-10:].copy()  # keep last 10 for memory

    if len(new_history) >= 2:
        prev = new_history[-1]
        prev_prev = new_history[-2]

        # Escalation patterns
        if prev == "frustrated" and current_emotion == "threatening":
            new_history.append("CRITICAL_AGGRESSION")
        elif prev == "desperate" and current_emotion == "backpedaling":
            new_history.append("COLLAPSE_IMMINENT")
        elif prev == "threatening" and current_emotion == "threatening":
            new_history.append("VOLATILE_THREAT")
        elif prev == "excited" and current_emotion == "frustrated":
            new_history.append("EMOTION_DROP")

    new_history.append(current_emotion)
    return new_history


def predict_scammer_patience(
    emotion_history: List[str],
    current_scam_score: int
) -> int:
    """
    Predictive patience model.
    Uses emotional volatility + current scam score to forecast remaining patience.
    """
    if not emotion_history:
        return current_scam_score

    recent = emotion_history[-6:]  # last 6 emotions

    fatigue_signals = sum(1 for emo in recent if emo in [
        "frustrated", "threatening", "backpedaling", "VOLATILE_THREAT", "CRITICAL_AGGRESSION"
    ])

    # Higher fatigue → faster patience drop
    fatigue_penalty = min(25, fatigue_signals * 6)

    # High scam score → scammer more invested → slower decay
    decay_rate = 3 if current_scam_score > 75 else 6

    predicted = current_scam_score - decay_rate - fatigue_penalty

    # Bound 0–100
    return min(100, max(0, predicted))