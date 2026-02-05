import random


def decide_next_move(state: dict) -> tuple[str, str]:
    """
    Strategic decision engine using simple game-theory-inspired rules.
    Aims to maximize time wasted and intelligence extracted while staying safe.
    
    Returns: (tactic: str, reasoning: str)
    """
    history = state.get("message_history", [])
    history_len = len(history) // 2   # number of full turns
    scam_score = state.get("scam_score", 50)
    last_msg = state.get("last_message", "").lower()
    scam_type = state.get("scam_type", "Unknown").lower()
    patience = state.get("patience_meter", 80)

    # ──────────────────────────────────────────────────────────────────────────────
    # Point #1: Cognitive Overload Protocol (Stateful stalling progression)
    # If we've already sent a fake OTP → progress to technical confusion
    # This prevents repeating the same tactic and maximizes time waste
    # ──────────────────────────────────────────────────────────────────────────────
    if any("OTP" in str(msg) for msg in history):
        return "STALL_CONFUSION", "Progressing from fake data to technical difficulty to maximize time waste."

    # Default / fallback
    tactic = "NORMAL_CHAT"
    reasoning = "Continuing standard low-suspicion engagement."

    # ──────────────────────────────────────────────────────────────────────────────
    # RULE 1: CROSS-CHANNEL LURE – Detect phishing link / external redirect attempt
    # ──────────────────────────────────────────────────────────────────────────────
    if any(x in last_msg for x in ["http", ".com", ".in", "click", "link", "open", "visit"]):
        tactic = "LURE_TO_UPI"
        reasoning = (
            "Scammer is pushing external link/channel. "
            "Countering by claiming device incompatibility and asking for UPI instead."
        )
        return tactic, reasoning

    # ──────────────────────────────────────────────────────────────────────────────
    # RULE 2: EMOTIONAL ADAPTATION – Detect rising anger/frustration
    # ──────────────────────────────────────────────────────────────────────────────
    anger_keywords = [
        "idiot", "stupid", "waste", "time", "fast", "quick", "hurry", "now",
        "block", "police", "report", "complaint", "useless", "fool", "bakwas"
    ]
    if any(word in last_msg for word in anger_keywords):
        tactic = "SUBMISSIVE_APOLOGY"
        reasoning = (
            "Scammer showing aggression/frustration. "
            "De-escalating with submissive apology to calm them and prolong engagement."
        )
        return tactic, reasoning

    # ──────────────────────────────────────────────────────────────────────────────
    # RULE 3: THE TRAP – Scammer asks for visual proof
    # ──────────────────────────────────────────────────────────────────────────────
    proof_keywords = ["screenshot", "photo", "proof", "receipt", "pic", "picture", "send image"]
    if any(x in last_msg for x in proof_keywords):
        tactic = "DEPLOY_FAKE_PROOF"
        reasoning = "Scammer demanded visual proof → deploying synthetic failed payment screenshot."
        return tactic, reasoning

    # ──────────────────────────────────────────────────────────────────────────────
    # RULE 4: COGNITIVE OVERLOAD – Scammer asks for OTP / PIN / payment
    # ──────────────────────────────────────────────────────────────────────────────
    value_trigger_words = ["otp", "pin", "code", "cvv", "pay", "transfer", "send money", "amount"]
    if any(x in last_msg for x in value_trigger_words):
        if random.random() > 0.6:  # slightly biased toward confusion (cheaper)
            tactic = "STALL_CONFUSION"
            reasoning = "Scammer requesting sensitive value → simulating technical confusion to stall."
        else:
            tactic = "STALL_FAKE_DATA"
            reasoning = "Scammer requesting sensitive value → providing fake/partial/incorrect data."
        return tactic, reasoning

    # ──────────────────────────────────────────────────────────────────────────────
    # RULE 5: LATE-GAME BAIT – Try to reverse extract after enough turns
    # ──────────────────────────────────────────────────────────────────────────────
    if history_len >= 5 or patience < 40:
        tactic = "BAIT_FOR_INTEL"
        reasoning = (
            "Conversation mature enough / scammer patience low → "
            "attempting to bait UPI ID / bank details under pretext."
        )
        return tactic, reasoning

    # ──────────────────────────────────────────────────────────────────────────────
    # RULE 6: EARLY-GAME TRUST BUILDING
    # ──────────────────────────────────────────────────────────────────────────────
    if history_len <= 2:
        tactic = "FEIGN_IGNORANCE"
        reasoning = "Early stage → acting naive/confused to build trust and lower defenses."
        return tactic, reasoning

    # Default: keep them talking
    return tactic, reasoning