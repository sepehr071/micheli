"""
Messages package — re-exports all symbols for backward compatibility.
Usage: from config.messages import AGENT_MESSAGES (unchanged)
"""

from config.messages.agent import AGENT_MESSAGES
from config.messages.ui import UI_BUTTONS
from config.messages.search import CONVERSATION_RULES
from config.messages.email import EMAIL_TEMPLATES, EMAIL_SUMMARY_PROMPT
from config.messages.qualification import QUALIFICATION_QUESTIONS, FALLBACK_NOT_PROVIDED
from config.messages.history import HISTORY_FORMAT
