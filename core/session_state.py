"""
Session state — the UserData dataclass that holds all per-session runtime state.
Shared across all agents via LiveKit's AgentSession.

Not configuration — this is runtime state (contact info, search results, flow flags).
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from livekit.agents import RunContext
from config.settings import RT_MODEL  # noqa: F401 — re-exported for backward compat


@dataclass
class UserData:
    # Contact info (collected naturally during conversation)
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    preferred_contact: Optional[str] = None  # "phone" | "whatsapp" | "email"

    # Appointment
    schedule_date: Optional[str] = None
    schedule_time: Optional[str] = None

    # Lead assessment (LLM-driven, not keyword-based)
    lead_score: int = 0              # 0-10, set by LLM via assess_lead_interest
    lead_level: str = "MILD"         # HOT/WARM/COOL/MILD, set by LLM
    lead_reasoning: str = ""         # LLM's explanation for the score

    # Search state
    search_count: int = 0
    last_search_results: List[Dict] = field(default_factory=list)

    # Flow control
    expert_offered: bool = False
    expert_accepted: bool = False
    consent_given: bool = False      # GDPR: explicit consent to be contacted

    # Conversation
    conversation_summary: Optional[str] = None  # Agent-written summary via function tool
    _history_saved: bool = False


RunContext_T = RunContext[UserData]
