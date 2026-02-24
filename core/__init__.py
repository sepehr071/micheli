"""
Core modules — session state, lead scoring, product search, response building.
These are framework-independent business logic used by the agent layer.
"""

from core.session_state import UserData, RunContext_T
from core.lead_scoring import detect_buying_signals, calculate_lead_degree
