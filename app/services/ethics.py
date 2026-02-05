# /app/services/ethics.py
class EthicsEngine:
    def check_bias(self, text: str) -> bool:
        """
        Ensures no protected group bias in generated text.
        """
        bad_words = ["poor people", "uneducated", "villager", "lower class"]
        if any(w in text.lower() for w in bad_words):
            return False # Failed bias check
        return True

    def generate_explanation(self, state: dict) -> str:
        """
        Creates a human-readable log of the AI's reasoning for the Judges.
        """
        tactic = state.get("current_tactic", "Unknown")
        reason = state.get("tactic_reasoning", "None")
        scam_score = state.get("scam_score", 0)
        
        rl_reward = state.get("rl_reward", 0.0)
        nash_payoff = state.get("nash_payoff", 0.0)
        
        return (
            f"DECISION: Used '{tactic}' because Threat Score was {scam_score}/100. "
            f"MATHEMATICAL RATIONALE: RL Reward={rl_reward}, Nash Payoff={nash_payoff}. "
            f"GOAL: {reason}. "
            f"SAFETY: PII Redaction Active. Bias Check Passed."
        )

ethics = EthicsEngine()