"""
Qualification agents — Q1 (purchase timing), Q2 (next step), Q3 (reachability).
These ask a question, show buttons, and transition to the next agent.

Used by: agents/main_agent.py (connect_to_expert → PurchaseTimingAgent)
"""

import json
import asyncio
import logging
from livekit.agents import function_tool
from agents.base import BaseAgent, safe_generate_reply
from core.session_state import RunContext_T
from config.services import SERVICES
from config.messages import QUALIFICATION_QUESTIONS
from config.language import get_language_prefix, get_language_instruction
from config.settings import LLM_TEMPERATURE_WORKFLOW
import prompt.static_workflow as prompts

logger = logging.getLogger(__name__)


async def _question_enter(agent, question: str, buttons: dict, label: str):
    """Shared on_enter — guaranteed not to crash the agent."""
    logger.info(f"{label} on_enter called")
    # Inject language instruction into the question
    question_with_language = get_language_prefix() + question + get_language_instruction()
    await safe_generate_reply(agent.session, agent.room, question_with_language)

    try:
        await asyncio.sleep(0.5)
        await agent.room.local_participant.send_text(
            json.dumps(buttons), topic="trigger"
        )
    except Exception as e:
        logger.error(f"{label} send_text failed: {e}")


class PurchaseTimingAgent(BaseAgent):
    """Q1: Wann möchten Sie Ihre Behandlung buchen?"""

    async def on_enter(self):
        await _question_enter(
            self,
            question=QUALIFICATION_QUESTIONS["purchase_timing"],
            buttons=SERVICES["purchase_timing"],
            label="PurchaseTimingAgent",
        )

    @function_tool
    async def select_purchase_timing(self, context: RunContext_T, selection: str):
        """
        Call this when user clicks a timing button or says their preferred timing.

        selection: Must be one of:
        - "sofort" = Sofort / innerhalb von 7 Tagen
        - "2_4_wochen" = In 2–4 Wochen
        - "spaeter" = In 1–3 Monaten oder später
        """
        logger.info(f"PurchaseTimingAgent: selection={selection}")
        self.userdata.purchase_timing = selection
        return NextStepAgent(
            instructions=prompts.NextStepPrompt,
            room=self.room,
            chat_ctx=None,
            userdata=self.userdata,
            add_instruction=False,
            temperature=LLM_TEMPERATURE_WORKFLOW,
        )


class NextStepAgent(BaseAgent):
    """Q2: Was möchten Sie als Nächstes tun?"""

    async def on_enter(self):
        await _question_enter(
            self,
            question=QUALIFICATION_QUESTIONS["next_step"],
            buttons=SERVICES["service_options"],
            label="NextStepAgent",
        )

    @function_tool
    async def select_next_step(self, context: RunContext_T, selection: str):
        """
        Call this when user clicks a next step button or says their preference.

        selection: Must be one of:
        - "beratungstermin" = Beratungstermin vereinbaren
        - "preis_details" = Preise und Details erfahren
        - "weiter_umsehen" = In Ruhe weiter umschauen
        """
        logger.info(f"NextStepAgent: selection={selection}")
        self.userdata.next_step = selection
        # Import here to avoid circular import (ReachabilityAgent is in the same file)
        return ReachabilityAgent(
            instructions=prompts.ReachabilityPrompt,
            room=self.room,
            chat_ctx=None,
            userdata=self.userdata,
            add_instruction=False,
            temperature=LLM_TEMPERATURE_WORKFLOW,
        )


class ReachabilityAgent(BaseAgent):
    """Q3: Wie dürfen wir Sie am besten erreichen?"""

    async def on_enter(self):
        await _question_enter(
            self,
            question=QUALIFICATION_QUESTIONS["reachability"],
            buttons=SERVICES["reachability"],
            label="ReachabilityAgent",
        )

    @function_tool
    async def select_reachability(self, context: RunContext_T, selection: str):
        """
        Call this when user clicks a reachability button or says their preference.

        selection: Must be one of:
        - "telefon_heute" = Telefon – heute
        - "whatsapp_heute" = WhatsApp – heute
        - "email_woche" = E-Mail – diese Woche
        """
        logger.info(f"ReachabilityAgent: selection={selection}")
        self.userdata.reachability = selection
        from agents.contact_agents import GetUserNameAgent
        return GetUserNameAgent(
            instructions=prompts.GetUserNamePrompt,
            room=self.room,
            chat_ctx=None,
            userdata=self.userdata,
            add_instruction=False,
            temperature=LLM_TEMPERATURE_WORKFLOW,
        )
