from typing import Annotated, TypedDict, List, Dict, Any, Optional
import operator

class AgentState(TypedDict, total=False):
    """State for the VIBHISHAN Agentic Honeypot workflow."""
    session_id: str
    message_history: Annotated[List[str], operator.add]
    last_message: str
    scam_score: int
    scam_type: str
    current_tactic: str
    tactic_reasoning: str
    current_persona: str
    agent_reply_draft: str
    agent_reply: str
    extracted_data: Dict[str, List[str]]
    patience_meter: int
    audio_reply_path: Optional[str]
    report_path: Optional[str]
    ncrp_report_path: Optional[str]
    fusion_probability: float
    behavioral_fingerprint: str
    emotion_history: List[str]
    typing_delay_seconds: float
    past_experience: str
    metadata: Dict[str, Any]
    # Supervisor approval fields
    supervisor_approved: bool
    supervisor_feedback: str
    # Economic and profiling fields
    economic_damage: float
    frustration_data: Dict[str, Any]
    syndicate_probability: float
    # Predicted scammer moves
    predicted_moves: Dict[str, Any]
    # Mathematical Rationale
    rl_reward: float
    nash_payoff: float
    previous_turn_info: dict