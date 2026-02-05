# app/services/multi_agent_brain.py
import asyncio
import json
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.language_models import BaseLanguageModel

from app.core.state import AgentState
from app.services.rl_brain import select_action
from app.services.game_theory import GameTheoryEngine

game_engine = GameTheoryEngine()


@dataclass
class AgentProposal:
    agent_name: str
    tactic: str
    confidence: float          # 0.0–1.0
    reasoning: str
    proposed_reply_snippet: str  # short preview / style example


@dataclass
class SwarmDecision:
    chosen_tactic: str
    confidence: float
    reasoning_summary: str
    top_proposals: List[AgentProposal]
    metadata: Dict[str, Any] = None


class DynamicSwarm:
    """
    No hardcoded agents, no fixed tactic list.
    
    The LLM itself decides:
    - how many agents to spawn
    - what their personas/roles should be
    - what tactics are possible in this situation
    
    Then we run them in parallel.
    """
    
    def __init__(self, strong_llm: BaseLanguageModel):
        from app.core.config import SETTINGS
        from langchain_groq import ChatGroq
        
        # ACCELERATED TRAINING MODE: Use 8B model to bypass rate limits during RL state exploration
        if SETTINGS.TRAINING_MODE:
             self.strong_llm = ChatGroq(
                 model_name="llama-3.1-8b-instant", 
                 temperature=0.7,
                 api_key=SETTINGS.GROQ_API_KEY
             )
        else:
             self.strong_llm = strong_llm
             
        self.fast_llm = ChatGroq(
            model_name="llama-3.1-8b-instant", 
            temperature=0.3,
            api_key=SETTINGS.GROQ_API_KEY
        )

    async def _run_single_agent(
        self,
        agent_description: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[AgentProposal]:
        prompt = ChatPromptTemplate.from_template(
            """You are acting as: {agent_description}

Current situation:
Scam type: {scam_type}
Last scammer message: {last_message}
Previous tactic used: {previous_tactic}
Goal right now: {current_goal}

Your task:
1. Choose ONE effective next tactic from what makes sense in this context.
2. Give it a short, clear name (e.g. "fake-payment-proof", "emotional-bait", "kyc-delay-loop")
3. Write 1–2 sentences explaining why you chose it.
4. Estimate your confidence (0.0–1.0)
5. Write the full suggested reply text (no placeholders) that you would send.

Return only JSON:
{{
  "tactic": "short-tactic-name",
  "confidence": 0.85,
  "reasoning": "...",
  "reply_snippet": "Full reply text goes here..."
}}
"""
        )

        chain = prompt | self.fast_llm | JsonOutputParser()

        try:
            result = await chain.ainvoke({
                "agent_description": agent_description["description"],
                "scam_type": context.get("scam_type", "unknown"),
                "last_message": context.get("last_message", ""),
                "previous_tactic": context.get("previous_tactic", "none"),
                "current_goal": context.get("current_goal", "waste time + extract intel")
            })

            return AgentProposal(
                agent_name=agent_description["name"],
                tactic=result.get("tactic", "wait-and-see"),
                confidence=float(result.get("confidence", 0.5)),
                reasoning=result.get("reasoning", ""),
                proposed_reply_snippet=result.get("reply_snippet", "")
            )
        except Exception as e:
            print(f"Agent failed ({agent_description['name']}): {e}")
            return None

    async def deliberate(self, state: AgentState) -> SwarmDecision:
        # ── Step 1: Ask strong model to invent 3–5 suitable agents for THIS situation ──
        planner_prompt = ChatPromptTemplate.from_template(
            """Given this scam conversation context:

Scam type: {scam_type}
Last message: {last_message}
History summary: {history_summary}
RL Recommended Tactic: {rl_tactic} 
Game Theory Optimal Move: {gt_move}
Current goal: waste time + extract maximum intel without detection

Invent 3–5 different agent personas/roles that would be useful right now.
For each give:
- short name
- one-sentence description/persona

ELITE TACTICS:
1. 'Merchant Code' Bait: "Beta, GPay says I need your 'Merchant Code' or UPI to verify you first. Can you send it?"
2. 'Cognitive Overload' (OTP): "Wait... was it 829... or 928? My glasses are broken. One minute beta."
3. 'Cross-Channel Lure': "Link isn't opening on my old phone. Send UPI ID directly please."

Also, provide a Profiling assessment of the scammer's current state.

Return only JSON:
{{
  "profile": {{
     "scam_type": "KYC/Lottery/Job/etc",
     "threat_score": 0-100,
     "scammer_mood": "Aggressive/Patient/etc"
  }},
  "agents": [
    {{"name": "Saroj", "description": "confused emotional elderly Grandma (Hindi/Hinglish)"}},
    {{"name": "Saroj_Tamil", "description": "confused elderly Grandma (Tamil/Tanglish)"}},
    {{"name": "Saroj_Telugu", "description": "confused elderly Grandma (Telugu/Tanglish variant)"}},
    {{"name": "Housewife", "description": "concerned multitasking housewife, sounds busy with kitchen/kids (Useful for Product/Domestic Scams)"}},
    {{"name": "Tech_Bro", "description": "young impatient professional, uses slang like 'bro', 'yaar'. (Useful for Tech Support Scams)"}},
    {{"name": "Investment_Pro", "description": "curious but greedy young professional interested in crypto/stocks. (Useful for Investment Scams)"}},
    {{"name": "Aggressive_Lawyer", "description": "highly skeptical and threatening with legal IPC codes"}}
  ]
}}
"""
        )

        planner_result = {}
        try:
            # ── Step 0: Formal Strategy Selection (RL + Game Theory) ──
            turn_count = len(state.get("message_history", [])) // 2
            scam_score = state.get("scam_score", 50)
            rl_tactic, _ = select_action(turn_count, scam_score)
            
            # Game Theory parameters (simulated inputs for LP solver)
            gt_move = game_engine.calculate_optimal_move(
                scammer_aggression=state.get("metadata", {}).get("scammer_mood", "patient") == "aggressive",
                intel_gathered=len(state.get("extracted_data", {}).get("upi_ids", [])) / 3.0
            )

            planner_result = await planner_chain.ainvoke({
                "scam_type": state.get("scam_type", "unknown"),
                "last_message": state.get("last_message", ""),
                "history_summary": "\n".join(state.get("message_history", [])[-6:]),
                "rl_tactic": rl_tactic,
                "gt_move": gt_move
            })

            agents_raw = planner_result.get("agents", [])

            if not isinstance(agents_raw, list):
                agents_raw = []

            # Take 2 high-quality agents for speed/rate-limit efficiency
            agents = agents_raw[:2]
            if len(agents) < 1:
                # fallback minimal set
                agents = [
                    {"name": "Saroj", "description": "confused emotional elderly Grandma"},
                    {"name": "Housewife", "description": "concerned multitasking housewife"},
                    {"name": "Cautious Uncle", "description": "skeptical middle-aged Indian man"},
                ]

        except Exception:
            # ultra-safe fallback
            planner_result = {"profile": {"scam_type": "Unknown", "threat_score": 50}}
            agents = [
                {"name": "Default Helper", "description": "polite helpful person trying to resolve issue"},
            ]

        # ── Step 2: Run chosen agents in parallel ───────────────────────────────
        context = {
            "scam_type": state.get("scam_type", "unknown"),
            "last_message": state.get("last_message", ""),
            "previous_tactic": state.get("current_tactic", "none"),
            "current_goal": "waste time + extract intel",
        }

        tasks = [self._run_single_agent(agent, context) for agent in agents]
        proposals = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter valid proposals
        valid_proposals = [p for p in proposals if isinstance(p, AgentProposal)]

        if not valid_proposals:
            return SwarmDecision(
                chosen_tactic="safe-chat",
                confidence=0.4,
                reasoning_summary="All agents failed → fallback",
                top_proposals=[]
            )

        # ── Step 3: Weighted vote + Consolidated Profiling ───────────────────
        tactic_scores: Dict[str, float] = {}
        for prop in valid_proposals:
            t = prop.tactic
            tactic_scores[t] = tactic_scores.get(t, 0) + prop.confidence

        # Winner
        if tactic_scores:
            best_tactic = max(tactic_scores, key=tactic_scores.get)
            total_conf = sum(tactic_scores.values())
            confidence = tactic_scores[best_tactic] / total_conf if total_conf > 0 else 0.5
        else:
            best_tactic = "safe-chat"
            confidence = 0.5

        # Consolidate profiling metadata from the planner's previous response
        # or ask agents to include it. For <1s, we use the planner's initial assessment.
        
        return SwarmDecision(
            chosen_tactic=best_tactic,
            confidence=round(confidence, 2),
            reasoning_summary=f"Consolidated choice: {best_tactic} based on swarm consensus.",
            top_proposals=valid_proposals[:3],
            metadata=planner_result.get("profile", {})
        )


# Alias for backward compatibility with agents.py import
MultiAgentSwarm = DynamicSwarm