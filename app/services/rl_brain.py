import json
import os
import random
import numpy as np

Q_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "q_table.json")
ACTIONS = ["NORMAL_CHAT", "STALL_CONFUSION", "STALL_FAKE_DATA", "BAIT_FOR_INTEL", "DEPLOY_FAKE_PROOF", "SUBMISSIVE_APOLOGY"]

# Hyperparameters
# ── ADVANCED DIFFERENTIATOR: MULTI-ARMED BANDIT & POMDP ──
# We treat tactic selection as a Multi-armed Bandit problem (Reward vs Regret)
# with POMDP (Partially Observable Markov Decision Process) properties
# due to unknown scammer intent and state uncertainty.
ALPHA = 0.1   # Learning Rate
GAMMA = 0.9   # Discount Factor
EPSILON = 0.1 # Base Exploration Rate

# ── THOMPSON SAMPLING PARAMS (Bandit Logic) ──
# Success count and trials for each (State, Action) pair
ALPHA_BANDIT = 1.0
BETA_BANDIT = 1.0

BANDIT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "bandit_stats.json")

def load_bandit_stats():
    if os.path.exists(BANDIT_FILE):
        try:
            with open(BANDIT_FILE, "r") as f:
                data = json.load(f)
                # Convert keys from list [state, action] back to tuple (state, action)
                success = {tuple(k): v for k, v in data.get("success", [])}
                failure = {tuple(k): v for k, v in data.get("failure", [])}
                return success, failure
        except:
            return {}, {}
    return {}, {}

def save_bandit_stats(success, failure):
    data = {
        "success": [[list(k), v] for k, v in success.items()],
        "failure": [[list(k), v] for k, v in failure.items()]
    }
    with open(BANDIT_FILE, "w") as f:
        json.dump(data, f)

def load_q_table():
    if os.path.exists(Q_FILE):
        try:
            with open(Q_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_q_table(q_table):
    try:
        with open(Q_FILE, "w") as f:
            json.dump(q_table, f)
    except Exception as e:
        print(f"Failed to save Q-table: {e}")

def get_state_key(turn_count, scam_score, scam_type="unknown"):
    """
    Discretizes the environment into granular states.
    WINNER'S EDGE: Including scam_type allows for specialized training.
    """
    phase = "EARLY" if turn_count < 3 else ("MID" if turn_count < 8 else "LATE")
    threat = "CRITICAL" if scam_score > 90 else ("HIGH" if scam_score > 70 else "LOW")
    s_type = scam_type.upper().replace(" ", "_")
    return f"{phase}_{threat}_{s_type}"

def select_action(turn_count, scam_score, scam_type="unknown"):
    q_table = load_q_table()
    state = get_state_key(turn_count, scam_score, scam_type)
    
    # Initialize state if new
    if state not in q_table:
        q_table[state] = {a: 0.0 for a in ACTIONS}
    
    # Epsilon-Greedy Strategy (Explore vs Exploit)
    if random.random() < EPSILON:
        return random.choice(ACTIONS), f"EXPLORATION: Experimental strategy test for {state}."
    else:
        # Exploit: Choose action with highest score
        actions = q_table[state]
        best_action = max(actions, key=actions.get)
        return best_action, f"EXPLOITATION: Optimal strategy for {state} scenario."

def update_q_table(old_turn, old_score, action, reward, next_turn, next_score, scam_type="unknown"):
    """
    True Q-Learning update using Bellman Equation:
    Q(s,a) = Q(s,a) + alpha * [reward + gamma * max(Q(s',a')) - Q(s,a)]
    """
    q_table = load_q_table()
    current_state_key = get_state_key(old_turn, old_score, scam_type)
    next_state_key = get_state_key(next_turn, next_score, scam_type)
    
    # Init states if missing
    if current_state_key not in q_table:
        q_table[current_state_key] = {a: 0.0 for a in ACTIONS}
    if next_state_key not in q_table:
        q_table[next_state_key] = {a: 0.0 for a in ACTIONS}
        
    # ECONOMIC REWARD SHARING: Reward for wasting scammer time (Rupees)
    # Calibrated to ₹20/min opportunity cost
    economic_reward = (reward / 350) * 10 
    total_reward = reward + economic_reward

    old_q = q_table[current_state_key].get(action, 0.0)
    
    # Calculate max Q for next state
    next_max_q = max(q_table[next_state_key].values())
    
    # Bellman Update
    new_q = old_q + ALPHA * (total_reward + GAMMA * next_max_q - old_q)
    
    q_table[current_state_key][action] = new_q
    save_q_table(q_table)

class DialogueBandit:
    """
    Implements a Multi-armed Bandit for context-aware dialogue strategy selection.
    Uses Thompson Sampling style logic if state is highly uncertain (POMDP).
    """
    def __init__(self):
        self.q_table = load_q_table()
        self.success_counts, self.failure_counts = load_bandit_stats()

    def select_optimal_arm(self, state_key: str) -> str:
        """
        Uses Thompson Sampling (drawing from Beta distributions) to pick action.
        This balances exploration vs exploitation optimally (Regret Minimization).
        """
        if state_key not in self.q_table:
            # Init state in Q-table to ensure consistency
            self.q_table[state_key] = {a: 0.0 for a in ACTIONS}
            save_q_table(self.q_table)
            return random.choice(ACTIONS)
        
        # Draw from Beta(alpha + successes, beta + failures) for each action
        samples = {}
        for action in ACTIONS:
            # Get alpha/beta from prior + evidence
            s = self.success_counts.get((state_key, action), 0)
            f = self.failure_counts.get((state_key, action), 0)
            samples[action] = np.random.beta(ALPHA_BANDIT + s, BETA_BANDIT + f)
            
        # Add Q-value influence (Hybrid RL-Bandit)
        for action in ACTIONS:
            q_val = self.q_table[state_key].get(action, 0.0)
            # Normalize Q-val to [0,1] for influence
            samples[action] += 0.2 * (1.0 / (1.0 + np.exp(-q_val))) # sigmoid
            
        return max(samples, key=samples.get)

    def record_feedback(self, state_key: str, action: str, reward: float):
        """Update Bandit counts based on outcome."""
        if reward > 5: # Threshold for 'success'
            self.success_counts[(state_key, action)] = self.success_counts.get((state_key, action), 0) + 1
        else:
            self.failure_counts[(state_key, action)] = self.failure_counts.get((state_key, action), 0) + 1
        
        # PERSIST SUCCESS/FAILURE
        save_bandit_stats(self.success_counts, self.failure_counts)

bandit = DialogueBandit()

# ────────────────────────────────────────────────────────────────────────────────
# UPGRADE 2: PREDICTIVE SCAMMER PROFILING
# ────────────────────────────────────────────────────────────────────────────────
def predict_scammer_move(history: list) -> dict:
    """
    Uses pattern recognition to predict what the scammer will do next.
    Returns a dict with predicted move, confidence, and recommended counter-strategy.
    """
    if not history:
        return {
            "predicted_move": "unknown",
            "confidence": 0.0,
            "counter_strategy": "maintain_persona",
            "expected_time_waste": "unknown"
        }

    last_msg = history[-1].lower()  # most recent scammer message

    prediction = {
        "predicted_move": "unknown",
        "confidence": 0.0,
        "counter_strategy": "maintain_persona",
        "expected_time_waste": "unknown"
    }

    # Heuristic-based prediction rules (can be expanded with ML later)
    if "otp" in last_msg or "code" in last_msg or "pin" in last_msg:
        prediction = {
            "predicted_move": "pressure_tactics",
            "confidence": 0.92,
            "counter_strategy": "STALL_CONFUSION",
            "expected_time_waste": "15 mins"
        }
    elif "police" in last_msg or "complaint" in last_msg or "block" in last_msg:
        prediction = {
            "predicted_move": "legal_threat",
            "confidence": 0.88,
            "counter_strategy": "SUBMISSIVE_APOLOGY",
            "expected_time_waste": "20 mins"
        }
    elif "link" in last_msg or "click" in last_msg or "open" in last_msg or "download" in last_msg:
        prediction = {
            "predicted_move": "credential_harvesting",
            "confidence": 0.95,
            "counter_strategy": "LURE_TO_UPI",
            "expected_time_waste": "10 mins"
        }
    elif "screenshot" in last_msg or "photo" in last_msg or "proof" in last_msg:
        prediction = {
            "predicted_move": "demand_proof",
            "confidence": 0.90,
            "counter_strategy": "DEPLOY_FAKE_PROOF",
            "expected_time_waste": "8 mins"
        }

    return prediction