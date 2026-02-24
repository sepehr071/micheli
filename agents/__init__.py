"""
Agent classes — all LiveKit Agent subclasses for the voice assistant.

main_agent.py      ConversationAgent (main conversation, search, lead qualification)
email_agents.py    CompletionAgent (email sending, summary, restart)
base.py            BaseAgent (shared init + transcription)
"""

from agents.base import BaseAgent
from agents.main_agent import ConversationAgent
from agents.email_agents import CompletionAgent
