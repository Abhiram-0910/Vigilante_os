# app/services/game_theory.py
import numpy as np
from scipy.optimize import linprog
from typing import Tuple


class GameTheoryEngine:
    """
    Computes (approximate) Nash equilibrium mixed strategy for the defender (AI)
    in a zero-sum game against the scammer using linear programming.
    
    Returns: single action sampled from the optimal mixed strategy
    """
    
    def __init__(self):
        # Define the core payoff matrix once (AI = row player = maximizer)
        # Rows = AI actions, Columns = Scammer actions
        # Positive = good for AI (time wasted, intel gained, low risk)
        self.base_payoff = np.array([
            #      Push    Leave   Negotiate   Ghost
            [  4.0,   8.0,     2.0,      10.0 ],   # STALL / waste time
            [  6.0,   1.0,     5.0,      -2.0 ],   # BAIT / try to extract more
            [ -3.0,  -8.0,    -1.0,      12.0 ],   # THREATEN / provoke
            [ -1.0,   3.0,     1.5,       0.0 ],   # COMPLY / give in a little
        ])

        self.actions_ai = ["STALL", "BAIT", "THREATEN", "COMPLY"]
        self.actions_scammer = ["PUSH", "LEAVE", "NEGOTIATE", "GHOST"]

    def _adjust_payoff_for_state(
        self,
        aggression: float,          # 0.0 calm → 1.0 very angry
        intel_ratio: float          # 0.0 little intel → 1.0 lots already
    ) -> np.ndarray:
        """
        Dynamically adjust payoffs based on current state.
        """
        A = self.base_payoff.copy()

        # High aggression → baiting becomes riskier, stalling becomes safer
        if aggression > 0.75:
            A[1, :] -= 3.5          # bait risk ↑
            A[0, :] += 2.0          # stall reward ↑
            A[2, 0] += 4.0          # threaten better against pushy scammer

        # If we already have lots of intel → less incentive to bait
        if intel_ratio > 0.65:
            A[1, :] -= 2.5          # bait less valuable

        # Never let payoffs go too negative (keep game playable)
        A = np.clip(A, -12.0, 12.0)

        return A

    def calculate_nash_move(self, state: dict) -> dict:
        """
        New interface for Agentic Integration.
        Calculates move and returns payoff for rationale logging.
        """
        # Calculate aggression and intel ratio
        patience = state.get("patience_meter", 80)
        aggression = (100 - patience) / 100.0
        
        extracted = state.get("extracted_data", {})
        intel_count = sum(len(v) for v in extracted.values())
        intel_ratio = min(1.0, intel_count / 10.0)
        
        # Get state-adjusted payoff matrix
        A = self._adjust_payoff_for_state(aggression, intel_ratio)
        n_actions_ai = A.shape[0]
        n_actions_scammer = A.shape[1]

        # Solve LP
        c = [-1.0] + [0.0] * n_actions_ai
        A_ub = np.hstack([np.ones((n_actions_scammer, 1)), -A.T])
        b_ub = np.zeros(n_actions_scammer)
        A_eq = np.array([[0.0] + [1.0] * n_actions_ai])
        b_eq = np.array([1.0])
        bounds = [(None, None)] + [(0, 1) for _ in range(n_actions_ai)]

        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')

        if res.success:
            strategy_probs = res.x[1:]
            strategy_probs /= (strategy_probs.sum() + 1e-9)
            chosen_idx = np.random.choice(n_actions_ai, p=strategy_probs)
            return {
                "tactic": self.actions_ai[chosen_idx],
                "payoff": -res.fun,
                "confidence": strategy_probs[chosen_idx]
            }
        
        return {"tactic": "STALL", "payoff": 0.0, "confidence": 1.0}

    def calculate_optimal_move(
        self,
        scammer_aggression: float,
        intel_gathered: float       # can be count, score, normalized 0–1, etc.
    ) -> str:
        """
        Returns one action sampled from the Nash equilibrium mixed strategy.
        Uses linear programming to solve the zero-sum game.
        """
        # Normalize intel_gathered if needed (assume caller sends 0–1)
        intel_ratio = max(0.0, min(1.0, intel_gathered))

        # Get state-adjusted payoff matrix (AI wants to maximize)
        A = self._adjust_payoff_for_state(scammer_aggression, intel_ratio)

        n_actions_ai = A.shape[0]        # rows = our actions
        n_actions_scammer = A.shape[1]   # columns = adversary actions

        # ── Linear Program setup ─────────────────────────────────────────────
        # We solve for AI's mixed strategy x that maximizes minimum payoff v
        # → max v  s.t.  A^T x >= v * ones    and   sum(x) = 1, x >= 0

        # For scipy linprog (minimization): we minimize -v
        c = [-1.0] + [0.0] * n_actions_ai

        # Inequality constraints:  v - A^T x  <=  0   for each scammer action
        A_ub = np.hstack([np.ones((n_actions_scammer, 1)), -A.T])
        b_ub = np.zeros(n_actions_scammer)

        # Equality: sum(x) = 1
        A_eq = np.array([[0.0] + [1.0] * n_actions_ai])
        b_eq = np.array([1.0])

        # Bounds: v free, x_i ∈ [0,1]
        bounds = [(None, None)] + [(0, 1) for _ in range(n_actions_ai)]

        res = linprog(
            c,
            A_ub=A_ub,
            b_ub=b_ub,
            A_eq=A_eq,
            b_eq=b_eq,
            bounds=bounds,
            method='highs',           # modern reliable solver
            options={'presolve': True}
        )

        if res.success:
            # Optimal value v = -res.fun (because we minimized -v)
            strategy_probs = res.x[1:]                  # probabilities for our actions
            strategy_probs /= strategy_probs.sum()      # numerical safety

            # Sample one action from the mixed Nash strategy
            chosen_idx = np.random.choice(n_actions_ai, p=strategy_probs)
            chosen_action = self.actions_ai[chosen_idx]

            return chosen_action

        # Fallback when solver fails (rare with 'highs')
        # Return maximin pure strategy (most conservative)
        min_payoffs = np.min(A, axis=1)
        safe_idx = np.argmax(min_payoffs)
        return self.actions_ai[safe_idx]


# ── Optional: for debugging / logging ────────────────────────────────────────

    def explain_strategy(self, aggression: float, intel: float) -> dict:
        """Returns human-readable explanation (useful for observability)"""
        A = self._adjust_payoff_for_state(aggression, intel)
        min_payoffs = np.min(A, axis=1)
        best_pure = self.actions_ai[np.argmax(min_payoffs)]

        return {
            "aggression": aggression,
            "intel_ratio": intel,
            "best_pure_strategy": best_pure,
            "payoff_matrix": A.tolist(),
            "action_names": self.actions_ai
        }