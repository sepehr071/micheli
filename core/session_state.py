"""
Session state — the UserData dataclass that holds all per-session runtime state.
Shared across all agents via LiveKit's AgentSession.

Not configuration — this is runtime state (contact info, search results, flow flags).
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from livekit.agents import RunContext
from config.settings import RT_MODEL  # noqa: F401 — re-exported for backward compat
from utils.filter_state import UserPreferences, FilterValidationResult


@dataclass
class UserData:
    # Contact info (collected during qualification flow)
    summary_context: Any = None
    ret_count: Optional[int] = 0
    email: Optional[str] = None
    phoneNumber: Optional[str] = None
    name: Optional[str] = None
    schedule_date: Optional[str] = None
    schedule_time: Optional[str] = None

    # Search results (legacy field name, holds treatment results)
    ret_car: List[Dict] = field(default_factory=list)

    # Flow control flags
    expert_accepted: bool = False
    expert_offer_count: int = 0
    name_collected: bool = False
    current_signal_level: str = "MILD"
    pending_expert_buttons: bool = False

    # Filter state
    filter_preferences: UserPreferences = field(default_factory=UserPreferences)
    last_validation: Optional[FilterValidationResult] = None

    # Budget tracking
    response_count: int = 0
    budget_asked: bool = False

    # Qualification responses
    purchase_timing: Optional[str] = None
    next_step: Optional[str] = None
    reachability: Optional[str] = None

    # Signal counts for lead scoring
    last_hot_count: int = 0
    last_warm_count: int = 0
    last_cool_count: int = 0
    last_confidence: float = 0

    # Conversation history
    all_retrieved_products: List[Dict] = field(default_factory=list)
    conversation_summary: Optional[str] = None  # Agent-written summary via function tool
    _history_saved: bool = False


RunContext_T = RunContext[UserData]
