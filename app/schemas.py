from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Literal, Any
from enum import Enum


class MessageSource(str, Enum):
    WHATSAPP = "whatsapp"
    SMS = "sms"
    TELEGRAM = "telegram"
    VOICE = "voice"

Role = Literal["scammer", "user", "assistant", "system"]


class ConversationTurn(BaseModel):
    role: Role
    content: str

class IncomingMessage(BaseModel):
    session_id: str = Field(..., description="Unique ID for this conversation thread")
    message_text: Optional[str] = Field(None, description="Text content (if SMS/Text/WhatsApp/Telegram)")
    audio_base64: Optional[str] = Field(None, description="Base64 encoded MP3/WAV/OGG data (if Voice)")
    # IMPORTANT: evaluation bots may omit these fields; keep optional to avoid 422.
    source: Optional[MessageSource] = Field(default=None, description="Channel / source of the incoming message")
    timestamp: Optional[str] = Field(default=None, description="ISO 8601 timestamp with timezone")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Extra context (phone number, device info, etc.)")

    # Multi-turn support: judges may pass history; we also persist by session_id.
    conversation_history: List[ConversationTurn] = Field(
        default_factory=list,
        description="Optional prior turns for multi-turn evaluation"
    )


# ── Output Schemas ───────────────────────────────────────────────────────────────

class ScamStatus(str, Enum):
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    CONFIRMED_SCAM = "confirmed_scam"


class ExtractedIntel(BaseModel):
    intent_category: str = Field(default="unknown", description="Detected scam/intent type")
    upi_ids: List[str] = Field(default=[], description="Extracted UPI IDs / VPA")
    bank_accounts: List[str] = Field(default=[], description="Extracted bank account numbers + IFSC")
    phone_numbers: List[str] = Field(default=[], description="Extracted phone numbers (with country prefix if possible)")
    urls: List[str] = Field(default=[], description="Extracted URLs / phishing / payment links")
    
    # Voice & freeze-related fields
    is_ai_voice: bool = Field(
        default=False,
        description="Whether the incoming voice message was classified as AI-generated / deepfake"
    )
    freeze_request_id: Optional[str] = Field(
        default=None,
        description="Freeze request ID returned by the banking / UPI fraud freeze API (if triggered)"
    )


class EngagementMetrics(BaseModel):
    conversation_turns: int = Field(..., description="Number of turns/messages exchanged")
    scammer_patience_score: int = Field(..., description="0–100 score of how long the scammer stayed engaged")
    time_wasted_seconds: float = Field(..., description="Total time the scammer spent in conversation")
    
    # UPDATED: Now required (no default) – forces calculation in writer_node
    suggested_typing_delay: float = Field(
        ...,
        description="Calculated typing delay (seconds) to simulate realistic human typing behavior"
    )


class AgentResponse(BaseModel):
    session_id: str = Field(..., description="Echo of the incoming session ID")
    status: ScamStatus
    agent_reply: str = Field(..., description="The next message to send to the scammer/victim")
    extracted_intelligence: ExtractedIntel
    metrics: EngagementMetrics
    processing_time_ms: float = Field(..., description="Backend processing time (for performance monitoring)")


# ── Judge/Evaluation Response Contract ───────────────────────────────────────────
class JudgeExtractedIntelligence(BaseModel):
    upi_ids: List[str] = Field(default_factory=list)
    bank_accounts: List[str] = Field(default_factory=list)
    phone_numbers: List[str] = Field(default_factory=list)
    urls: List[str] = Field(default_factory=list)


class JudgeResponse(BaseModel):
    """
    Strict, flat-ish JSON contract commonly used by automated evaluators.
    Keep field names EXACT.
    """
    session_id: str
    scam_detected: bool
    confidence_score: float = Field(ge=0.0, le=1.0)
    agent_reply: str
    extracted_intelligence: JudgeExtractedIntelligence
    conversation_turns: int = Field(ge=0)
    engagement_duration_seconds: float = Field(ge=0.0)


class CompetitionEngagementMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    duration_seconds: float
    turns_count: int


CompetitionIntelType = Literal["UPI_ID", "BANK_ACCOUNT", "PHISHING_LINK"]


class CompetitionExtractedIntelligenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: CompetitionIntelType
    value: str
    confidence: float


class CompetitionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scam_detected: bool
    engagement_metrics: CompetitionEngagementMetrics
    extracted_intelligence: List[CompetitionExtractedIntelligenceItem]