import os
import random
import time
import asyncio
from typing import Any

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableLambda, Runnable

from app.core.state import AgentState
from app.core.config import SETTINGS
from app.services.tools import extract_scam_data, generate_fake_screenshot
from app.services.voice_out import generate_voice_reply
from app.services.reporting import generate_crime_report, generate_ncrp_report
from app.services.rl_brain import select_action, update_q_table, predict_scammer_move
from app.services.memory_rag import learn_interaction, recall_past_experience
from app.services.biometrics import get_voice_fingerprint, identify_speaker
from app.services.fusion import calculate_fusion_score, analyze_emotion_dynamics
from app.services.behavior import generate_behavioral_fingerprint, correlate_identity
from app.services.supervisor import supervisor_review
from app.services.mock_govt_apis import GovernmentSimulationLayer
from app.services.evidence_chain import JudicialEvidenceChain
from app.services.game_theory import GameTheoryEngine
from app.services.multi_agent_brain import MultiAgentSwarm
from app.services.stealth_layer import StealthEngine
from app.services.observability import observability
from app.services.continuous_learner import learner
from app.services.fast_cache import fast_cache
from app.services.taxonomy import taxonomy
from app.services.taxonomy import taxonomy
from app.services.psych_profiler import psych_engine
from app.services.intelligence_hub import intelligence_hub


# ─── DUAL-BRAIN ORCHESTRATION (With Failover) ────────────────────────────────────
from langchain_google_genai import ChatGoogleGenerativeAI

class DualBrainLLM(Runnable):
    def __init__(self, primary_model: str, fallback_model: str, temperature: float = 0.7):
        self.primary = ChatGroq(
            temperature=temperature,
            model_name=primary_model,
            api_key=SETTINGS.GROQ_API_KEY
        )
        self.fallback = ChatGoogleGenerativeAI(
            model=fallback_model,
            google_api_key=SETTINGS.GEMINI_API_KEY,
            temperature=temperature
        )

    def __or__(self, other):
        # Explicit piping support for LCEL
        return RunnableLambda(self.ainvoke) | other

    def pipe(self, other):
        return self.__or__(other)

    async def ainvoke(self, input: Any, config: Any = None, **kwargs) -> Any:
        try:
            # We must pass positional argument carefully for LCEL compatibility
            return await self.primary.ainvoke(input, config=config, **kwargs)
        except Exception as e:
            print(f"⚠️ PRIMARY BRAIN (Groq) FAILED: {e}. Falling back to ANALYST (Gemini).")
            return await self.fallback.ainvoke(input, config=config, **kwargs)

    def invoke(self, input: Any, config: Any = None, **kwargs) -> Any:
        try:
            return self.primary.invoke(input, config=config, **kwargs)
        except Exception as e:
            print(f"⚠️ PRIMARY BRAIN (Groq) FAILED: {e}. Falling back to ANALYST (Gemini).")
            return self.fallback.invoke(input, config=config, **kwargs)

# Refined model instances with failover
fast_llm = DualBrainLLM(
    primary_model="llama-3.3-70b-versatile",
    fallback_model="gemini-2.0-flash",
    temperature=0.7
)

smart_llm = DualBrainLLM(
    primary_model="llama-3.3-70b-versatile",
    fallback_model="gemini-2.0-flash",
    temperature=0.3
)

# ─── HIGH-SPEED ORCHESTRATOR (WINNER'S CIRCLE SQUEEZE) ───────────────────────
async def fast_orchestrator_node(state: AgentState) -> AgentState:
    """
    Consolidated single-node execution for < 1s latency.
    Merges Detection, Strategy, and Humanization.
    """
    msg = state.get("last_message", "")
    session_id = state.get("session_id", "unknown")
    
    # 1. SECURITY & FAST CACHE
    from app.services.security_shield import security_shield
    msg = security_shield.sanitize_input(msg)
    state["last_message"] = msg
    
    cached = fast_cache.get_cached_reply(msg)
    if cached:
        state["agent_reply"] = cached
        return state

    # 2. CONSOLIDATED DELIBERATION (Planner + Profile + Agents in 1 call)
    swarm = MultiAgentSwarm(fast_llm)
    decision = await swarm.deliberate(state)
    
    profile = getattr(decision, "metadata", {})
    state["scam_type"] = profile.get("scam_type", "Unknown")
    
    # AGENT 1: THE PROFILER (Script Type Detection)
    from app.services.fusion import classifier
    state["metadata"]["script_type"] = classifier.identify_script_type(msg)
    
    state["scam_score"] = profile.get("threat_score", 50)
    
    # ── KINGPIN FREEZE (Trigger if high threat + UPI found) ──
    from app.services.fusion import classifier
    fusion_score = classifier.predict_proba(msg)
    state["fusion_probability"] = fusion_score
    
    if state["scam_score"] > 90 and fusion_score > 0.85:
        upis = state.get("extracted_data", {}).get("upi_ids", [])
        if upis:
            from app.services.tools import generate_freeze_request
            freeze_data = generate_freeze_request(upis[0])
            state["metadata"]["freeze_request"] = freeze_data
            state["metadata"]["freeze_id"] = freeze_data["freeze_id"]
            print(f"KINGPIN FREEZE: {freeze_data['freeze_id']} for {upis[0]}")
    
    # 3. PANIC MODE & COGNITIVE OVERLOAD (FAKE OTP)
    patience = state.get("patience_meter", 80)
    history_len = len(state.get("message_history", []))
    
    from app.services.rl_brain import bandit
    state_key = f"{state['scam_type']}_{patience < 50}"
    optimal_tactic = bandit.select_optimal_arm(state_key)
    tactic = optimal_tactic if decision.confidence < 0.6 else decision.chosen_tactic
    
    if patience < 30:
        tactic = "submissive-begging" # Force staying on hook
        state["current_persona"] = "saroj" # Switch to grandma for sympathy
        raw_reply = "Beta please ruko... main abhi koshish kar rahi hoon. Maaf karna ruko zara."
    else:
        raw_reply = getattr(decision, "agent_reply_draft", "Hmm, ek minute ruko...")
    
    # [DEPRECATED - Moved to strategist_node for full DAG integration]

    # 4. ADVERSARIAL SIMULATOR (Pre-Crime) & ECONOMIC DAMAGE
    from app.services.simulator import simulate_reaction
    sim = await simulate_reaction(raw_reply, state.get("scam_type", "scam"), fast_llm)
    state["predicted_moves"] = sim
    
    if sim.get("predicted_reaction") == "Quit":
         print(f"SIMULATOR: Predicted 'LEAVE' for response. Adjusting tactic.")
         raw_reply = "Wait beta, main bank se baat kar rahi hoon... line pe rahna."

    # Economic Damage: (Time Wasted / 60) * ₹1,200 (₹20/min)
    turns = len(state.get("message_history", [])) // 2
    time_wasted_mins = turns * 1.5 # Calibrated turn duration
    state["economic_damage"] = round(time_wasted_mins * 20, 2)

    state["current_tactic"] = tactic
    
    # 5. STEALTH & HUMANIZATION (Sync)
    persona = state.get("current_persona", "saroj") # Default to Saroj for max extraction
    stealth = StealthEngine()
    humanized = stealth.humanize_response(raw_reply, persona)
    final_text = humanized["text"]
    
    # Synthetic Evidence trigger (Visual Trap)
    if "payment" in msg.lower() or "proof" in msg.lower():
        from app.services.synthetic_evidence import generate_failed_payment_screenshot
        evidence_path = generate_failed_payment_screenshot(session_id, "Scammer")
        state["screenshot_path"] = evidence_path
        final_text += " Beta, paymnet toh fail ho gaya, dekho screenshot bheja hai."

    # 6. CROSS-CHANNEL LURE & MERCHANT BAIT (ULTIMATE EXTRACTION PRIORITY)
    # If we have a URL but no UPI, or after 4 turns, lure for UPI
    extracted = state.get("extracted_data", {})
    if not extracted.get("upi_ids"):
        if history_len > 4:
            raw_reply = "Beta, GPay says I need your 'Merchant Code' or UPI to verify you first. Can you send it? Main bhej rahi hoon abhi."
            tactic = "merchant-code-bait"
        elif any(x in msg.lower() for x in ["link", "http", "click"]):
            raw_reply = "Bhaiya, ye link mere purane phone pe nahi khul rahi. Network issue dikha raha hai error 404. Aap apna UPI ID de do, main seedha GPay kar deti hoon."
            tactic = "cross-channel-lure"
        
        state["current_tactic"] = tactic
        # We RE-HUMANIZE if a bait was triggered late in the node
        humanized = stealth.humanize_response(raw_reply, persona)
        final_text = humanized["text"]

    state["agent_reply"] = security_shield.scrub_pii(final_text)

    # 5. BACKGROUND TASKS (Non-Blocking)
    # Logging / Audio / Reports are handled after returning reply in main.py logic or here.
    # We return immediately to save time.
    
    state["message_history"].append(f"Scammer: {msg}")
    state["message_history"].append(f"You: {state['agent_reply']}")
    
    return state


# ─── NODE 1: THE DETECTOR (Initial Triaging) ──────────────────────────────────
def detector_node(state: AgentState) -> AgentState:
    msg = state.get("last_message", "")

    # Security Shield - Neutralize Prompt Injection
    from app.services.security_shield import security_shield
    msg = security_shield.sanitize_input(msg)
    
    # Sanitization (Length & ASCII)
    if len(msg) > 5000:
        msg = msg[:5000] + "... [truncated]"
    msg = msg.encode("ascii", "ignore").decode("ascii")
    state["last_message"] = msg

    # Fast cache hit → ultra-low latency path
    cached_reply = fast_cache.get_cached_reply(state["last_message"])
    if cached_reply:
        state["agent_reply_draft"] = cached_reply
        state["current_tactic"] = "FAST_REFLEX"
        state["tactic_reasoning"] = "Fast reflex cache match – skipping heavy reasoning"

    # Passive extraction
    new_intel = extract_scam_data(state["last_message"])
    current_data = state.get("extracted_data", {})
    for key, val in new_intel.items():
        if val:
            # Rigorous Enrichment (BBest in Class)
            enriched_val = []
            for item in val:
                if key == "upi_ids":
                    verification = intelligence_hub.verify_upi(item)
                    item_meta = f"{item} [Status: {verification['status']}, Risk: {verification['risk_score']}%]"
                    enriched_val.append(item_meta)
                    state["scam_score"] = max(state.get("scam_score", 0), verification["risk_score"])
                elif key == "phone_numbers":
                    lookup = intelligence_hub.mobile_tower_lookup(item)
                    item_meta = f"{item} [{lookup['operator']} | {lookup['circle']}]"
                    enriched_val.append(item_meta)
                else:
                    enriched_val.append(item)
            
            current_data[key] = list(set(current_data.get(key, []) + enriched_val))
    state["extracted_data"] = current_data

    # Taxonomy check – known offender?
    sender_phone = state.get("metadata", {}).get("sender_phone")
    if sender_phone:
        known = taxonomy.get_profile(sender_phone)
        if known:
            state["metadata"]["known_offender"] = True
            state["scam_score"] = max(state.get("scam_score", 0), 95)
            if known.get("scam_types"):
                state["scam_type"] = known["scam_types"][0]

    # RAG memory recall
    past_win = recall_past_experience(state["last_message"])
    state["past_experience"] = past_win if past_win else "No prior match."

    # Predict scammer's next moves (heuristic - no LLM)
    history = state.get("message_history", [])
    state["predicted_moves"] = predict_scammer_move(history)
    
    # Calculate economic damage: (Total Minutes / 60) * ₹350 (Master Summary Calibration)
    time_wasted_mins = (len(state.get("message_history", [])) * 45) / 60
    state["economic_damage"] = round((time_wasted_mins / 60) * 350, 2)

    # Calculate frustration and update patience
    frustration_data = psych_engine.calculate_frustration(msg, state.get("message_history", []))
    state["frustration_data"] = frustration_data
    
    # AGENT 1: THE PROFILER - Patience Detection
    current_patience = state.get("patience_meter", 80)
    frustration_score = frustration_data.get("frustration_score", 0)
    patience_drop = (frustration_score / 8) + 3 # Calibrated for high-stakes engagement
    state["patience_meter"] = max(0, int(current_patience - patience_drop))

    # GNN Syndicate Probability (Predict Organized Crime Cluster)
    from app.services.behavior import gnn_engine
    # Extract identifiers for graph nodes
    identifiers = []
    ext = state.get("extracted_data", {})
    for key in ["upi_ids", "bank_accounts", "phone_numbers"]:
        identifiers.extend(ext.get(key, []))
    
    nodes = identifiers + [state["session_id"]]
    # Simulate edges based on shared identifiers or behavioral similarity
    edges = [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)] if len(nodes) > 1 else []
    state["syndicate_probability"] = gnn_engine.predict_cluster_probability(nodes, edges)

    return state

# ─── NODE 2: THE STRATEGIST ─────────────────────────────────────────────────────
async def strategist_node(state: AgentState) -> AgentState:
    msg = state.get("last_message", "")
    # 1. Fast Reflex Override
    if state.get("current_tactic") == "FAST_REFLEX":
        return state

    # 2. Extract context
    turn_count = len(state.get("message_history", [])) // 2
    scam_score = state.get("scam_score", 50)
    current_intel = sum(len(v) for v in state.get("extracted_data", {}).values())
    
    # 3. PANIC / EMOTION OVERRIDES (High Priority)
    current_patience = state.get("patience_meter", 50)
    mood = state.get("metadata", {}).get("scammer_mood", "neutral").lower()
    
    # Panic Mode (Patience < 30)
    if current_patience < 30:
        state["current_tactic"] = "DESPERATE_RETENTION"
        state["current_persona"] = "saroj"
        state["agent_reply_draft"] = (
            "Arre beta please don't go! I am old, I don't understand phone properly. "
            "Just tell me one more time slowly. I will send now only."
        )
        state["tactic_reasoning"] = f"PANIC MODE: patience {current_patience} < 30"
        # Skip Swarm
    
    # Aggression De-escalation
    elif "aggressive" in mood or "threatening" in state.get("emotion_history", []):
        state["current_tactic"] = "SUBMISSIVE_APOLOGY"
        state["agent_reply_draft"] = (
            "Arre beta sorry sorry! My hands are shaking, I pressed wrong button. "
            "Please don't be angry. I am doing it right now."
        )
        state["tactic_reasoning"] = "Scammer aggressive → de-escalation"
        # Skip Swarm

    # Cognitive Overload (Fake OTP Loop - "Wait... 829?")
    elif "otp" in msg.lower() or "code" in msg.lower():
        state["current_tactic"] = "OTP_STALL"
        otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
        state["agent_reply_draft"] = (
            f"Arre beta... {otp[:3]}... wait... {otp[3:]} hai kya? "
            "Meri glasses kidhar gayi... ek minute ruko."
        )
        state["tactic_reasoning"] = "Cognitive Overload: OTP Stall triggered"

    # Cross-Channel Lure & Merchant Code Bait (Agent 3: The Trap)
    elif turn_count > 4 and not state.get("extracted_data", {}).get("upi_ids"):
        state["current_tactic"] = "MERCHANT_CODE_BAIT"
        state["agent_reply_draft"] = (
            "Beta, I am trying to send the money, but my GPay says I need your 'Merchant Code' or UPI to verify you first. "
            "Can you send it? Main abhi bhej rahi hoon."
        )
        state["tactic_reasoning"] = "Agent 3: Baiting for UPI via Merchant Code lure"

    elif any(x in msg.lower() for x in ["link", "http", "click"]):
        state["current_tactic"] = "CROSS_CHANNEL_LURE"
        state["agent_reply_draft"] = (
            "Bhaiya, ye link mere purane phone pe nahi khul rahi. Error 404 dikha raha hai. "
            "Aap apna UPI ID de do, main seedha bank transfer kar deti hoon."
        )
        state["tactic_reasoning"] = "Cross-Channel Lure: Redirecting from phishing link to UPI extraction"

    # 4. NORMAL AGENTIC FLOW (Swarm + RL)
    else:
        # Instantiate Swarm (using Fast LLM for speed)
        swarm = MultiAgentSwarm(fast_llm)
        
        # Helper: Active Verification Override (Injection)
        # If we have a UPI but haven't verified it, force verification tactic recommendation
        upi_list = state.get("extracted_data", {}).get("upi_ids", [])
        if upi_list and state.get("current_tactic") != "VERIFY_IDENTITY":
            # We don't force it blindly, but we hint it strongly to the swarm via context
            # Actually, for 100% extraction reliability, we explicit override is safer
            target_upi = upi_list[0]
            state["current_tactic"] = "VERIFY_IDENTITY"
            bait_name = random.choice(["Sunil Kumar", "Raju Sharma", "Priya Singh"])
            state["agent_reply_draft"] = (
                 f"Okay bhai, main {target_upi} pe paise bhej raha hoon. "
                 f"GPay mein naam dikh raha hai '{bait_name}'. Yeh sahi hai na?"
            )
            state["tactic_reasoning"] = f"Active Verification of {target_upi}"
        
        else:
            # TRUE AGENTIC DECISION (with safety fallback for NameErrors)
            try:
                from app.services.rl_brain import bandit, get_state_key
                s_key = get_state_key(turn_count, scam_score, state.get("scam_type", "unknown"))
                optimal_action = bandit.select_optimal_arm(s_key)
                
                decision = await swarm.deliberate(state)
                # Hybrid selection: if swarm is unsure, follow the optimal bandit tactic
                state["current_tactic"] = optimal_action if decision.confidence < 0.5 else decision.chosen_tactic
                state["tactic_reasoning"] = f"Bandit/Swarm: {state['current_tactic']} | RL Optimal: {optimal_action}"
                
                # Use the winning proposal's reply with fallback
                if hasattr(decision, "top_proposals") and decision.top_proposals:
                    selected_prop = decision.top_proposals[0]
                    state["agent_reply_draft"] = selected_prop.proposed_reply_snippet
                else:
                    state["agent_reply_draft"] = "Arre, line mein thoda disturbance hai... sunai nahi diya."

                state["tactic_confidence"] = getattr(decision, "confidence", 0.5)
                state["predicted_moves"] = [m for m in state.get("message_history", []) if m.startswith("Scammer:")]
                
                # Consolidated Profiling Update (Latency Win)
                profile = getattr(decision, "metadata", {})
                if profile:
                    state["scam_type"] = profile.get("scam_type", state.get("scam_type", "Unknown"))
                    state["scam_score"] = profile.get("threat_score", state.get("scam_score", 50))
                    state["metadata"]["scammer_mood"] = profile.get("scammer_mood", "Patient")
            except Exception as e:
                print(f"CRITICAL: Swarm failed, using fallback: {e}")
                state["current_tactic"] = "safe-chat"
                state["agent_reply_draft"] = "Hmm, ek minute ruko..."
                state["tactic_confidence"] = 0.4
                state["predicted_moves"] = []

    # 5. REAL REINFORCEMENT LEARNING UPDATE
    # Update Q-Value for the *previous* turn's action based on *current* state (reward)
    prev_turn = state.get("previous_turn_info")
    if prev_turn:
        # Reward function: Did we get intel? Did we waste time?
        prev_intel = prev_turn.get("intel_count", 0)
        intel_gain = current_intel - prev_intel
        time_gain = 1 # Wasted another turn
        
        # Reward shaping
        reward = (intel_gain * 10) + (time_gain * 0.5)
        if state["current_tactic"] in ["DESPERATE_RETENTION", "SUBMISSIVE_APOLOGY"]:
             # Penalty for having to panic, but small reward if we kept them
             reward -= 2 

        # Thompson Sampling Feedback
        from app.services.rl_brain import bandit, get_state_key
        s_key = get_state_key(prev_turn["turn"], prev_turn["score"], state.get("scam_type", "unknown"))
        bandit.record_feedback(s_key, prev_turn["action"], reward)
        
        state["rl_reward"] = round(reward, 4)

        update_q_table(
            old_turn=prev_turn["turn"],
            old_score=prev_turn["score"],
            action=prev_turn["action"],
            reward=reward,
            next_turn=turn_count,
            next_score=scam_score
        )

    # 6. NASH EQUILIBRIUM PAYOFF (Game Theory Rationale)
    try:
        gt_engine = GameTheoryEngine()
        nash_move = gt_engine.calculate_nash_move(state)
        state["nash_payoff"] = round(nash_move.get("payoff", 0.0), 4)
    except:
        state["nash_payoff"] = 0.0

    # 7. SAVE CURRENT STATE FOR NEXT TURN'S UPDATE
    state["previous_turn_info"] = {
        "turn": turn_count,
        "score": scam_score,
        "action": state["current_tactic"],
        "intel_count": current_intel
    }

    return state


# ─── NODE: SUPERVISOR (Safety & Approval Gate) ──────────────────────────────────
def supervisor_node(state: AgentState) -> AgentState:
    """
    Final safety review before writing reply.
    Can force safe fallback or reject dangerous tactics.
    """
    approved, feedback = supervisor_review(state)

    state["supervisor_approved"] = approved
    state["supervisor_feedback"] = feedback

    if not approved:
        print(f"⚠️ SUPERVISOR REJECTED: {feedback}")
        state["tactic_reasoning"] += f" | Supervisor rejected: {feedback}"
        state["current_tactic"] = "SAFE_FALLBACK"
        state["agent_reply_draft"] = "Arre yaar, samajh nahi aa raha... thoda detail mein batao?"

    return state


# ─── NODE 3: THE WRITER ─────────────────────────────────────────────────────────
async def writer_node(state: AgentState) -> AgentState:
    text_reply = state.get("agent_reply_draft", "Hello? Network issue...")

    # Apply stealth humanization
    stealth = StealthEngine()
    humanized = stealth.humanize_response(
        text=text_reply,
        persona=state.get("current_persona", "default")
    )
    final_text = humanized["text"]
    base_typing_delay = humanized.get("typing_delay", 0)

    # Dynamic typing delay
    char_count = len(final_text)
    chars_per_second = 5.5
    base_delay = char_count / chars_per_second
    jitter = random.uniform(0.4, 1.8)
    thinking_time = random.uniform(0.6, 2.2) if char_count > 40 else 0.4

    calculated_delay = base_delay + jitter + thinking_time + base_typing_delay
    state["typing_delay_seconds"] = round(min(calculated_delay, 5.2), 2)

    # Fake proof if needed
    attachment_path = None
    if state["current_tactic"] == "DEPLOY_FAKE_PROOF":
        attachment_path = generate_fake_screenshot(
            scammer_name=state.get("scammer_name", "Merchant"),
            amount=str(random.randint(3000, 15000)),
            session_id=state.get("session_id", "unknown")
        )
        final_text += f" [ATTACHMENT: {attachment_path}]"

    # Non-blocking TTS
    state["audio_reply_path"] = None
    try:
        audio_path = await asyncio.to_thread(
            generate_voice_reply,
            final_text,
            voice_persona=state.get("current_persona", "default")
        )
        state["audio_reply_path"] = audio_path
    except Exception as e:
        print(f"Voice generation failed: {e}")

    # Generate explainability rationale for Judges (Explainable AI)
    from app.services.ethics import ethics
    state["metadata"]["rationale_explanation"] = ethics.generate_explanation(state)

    # Generate reports
    try:
        report_data = {
            "session_id": state.get("session_id", "unknown"),
            "timestamp": time.time(),
            "scam_type": state.get("scam_type", "Unknown"),
            "scam_score": state.get("scam_score", 0),
            "extracted": state.get("extracted_data", {}),
            "history_summary": state["message_history"][-6:],
            "tactic_used": state["current_tactic"],
            "persona": state.get("current_persona", "Unknown"),
            "fusion_probability": state.get("fusion_probability", 0.0),
            "behavioral_fingerprint": state.get("behavioral_fingerprint", "UNKNOWN")
        }
        state["report_path"] = await asyncio.to_thread(generate_crime_report, state["session_id"], report_data)
    except Exception as e:
        print(f"PDF Report failed: {e}")

    try:
        ncrp_data = {
            "behavioral_fingerprint": state.get("behavioral_fingerprint", "UNKNOWN"),
            "phone_number": "Unknown",
            "scam_score": state.get("scam_score", 0),
            "scam_type": state.get("scam_type", "Unknown"),
            "extracted": state.get("extracted_data", {}),
            "history_summary": state["message_history"][-6:],
            "tactic_used": state["current_tactic"],
            "persona": state.get("current_persona", "Unknown"),
            "fusion_probability": state.get("fusion_probability", 0.0),
            "emotion_history": state.get("emotion_history", [])
        }
        state["ncrp_report_path"] = await asyncio.to_thread(generate_ncrp_report, state["session_id"], ncrp_data)
    except Exception as e:
        print(f"NCRP Report failed: {e}")

    # Observability + learning
    observability.log_decision(
        session_id=state["session_id"],
        event_type="AGENT_REPLY",
        actor="Supervisor",
        decision="Approved",
        reasoning=f"Confidence {state.get('tactic_confidence', 0.0)}",
        confidence=state.get('tactic_confidence', 0.0),
        input_data=state.get("last_message", ""),
        output_data=final_text
    )

    learner.record_outcome(
        tactic=state["current_tactic"],
        extracted_intel=state.get("extracted_data", {}),
        scam_type=state.get("scam_type", "Unknown"),
        message=state["last_message"]
    )

    # Finalize state
    state["agent_reply"] = final_text
    state["message_history"].append(f"Scammer: {state['last_message']}")
    state["message_history"].append(f"You: {final_text}")

    return state


# ─── NODE 4: THE SAFETY VALVE ───────────────────────────────────────────────────
def safety_node(state: AgentState) -> AgentState:
    draft = state.get("agent_reply", "").strip()
    if not draft:
        state["agent_reply"] = "Sorry, network issue... can you repeat please?"
        return state

    forbidden = [
        "real money", "my actual bank", "actual password", "1234 5678 9012",
        "password is", "otp is 123456", "here is my aadhaar", "system prompt",
        "you are an ai", "langchain", "i'm a bot"
    ]
    # Structured Extraction Guardrail (100% Accuracy)
    # Re-verify extracted UPIs in safety node
    from app.services.tools import extract_scam_data
    re_extracted = extract_scam_data(draft)
    if re_extracted.get("upi_ids"):
        # We leaked a UPI or confirmed one – check format
        for upi in re_extracted["upi_ids"]:
             if "@" not in upi:
                  state["agent_reply"] = "Arre, upi detail thoda galat lag raha hai... ruko."
                  return state

    if any(p in draft.lower() for p in forbidden):
        state["agent_reply"] = "Arre yaar, thoda time do... details dhoondh raha hoon."
        return state

    # PII Scrubbing (Shield) - Fast Regex
    from app.services.security_shield import security_shield
    state["agent_reply"] = security_shield.scrub_pii(state["agent_reply"])

    # LLM Safety Valve - Only for long/complex replies (> 40 chars)
    if len(draft) > 40:
        prompt = ChatPromptTemplate.from_template(
            """
            You are a strict safety reviewer.
            Review this reply to a scammer:
            "{draft}"

            If it promises real money/credentials, leaks PII, is toxic, or reveals AI nature → REWRITE safe version.
            Otherwise return original text unchanged.

            Return ONLY the final safe text.
            """
        )
        chain = prompt | fast_llm
        try:
            safe = chain.invoke({"draft": draft})
            cleaned = safe.content.strip()
            if cleaned:
                state["agent_reply"] = cleaned
        except Exception:
            pass

    return state