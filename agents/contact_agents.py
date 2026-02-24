"""
Contact collection agents — name, email, phone, and call scheduling.
These collect user contact info with validation and smart skipping.

Used by: agents/qualification_agents.py (ReachabilityAgent → GetUserNameAgent)
"""

import json
import logging
from datetime import date
from livekit.agents import function_tool
from agents.base import BaseAgent
from core.session_state import RunContext_T
from utils.filter_extraction import is_valid_email_syntax
from config.messages import AGENT_MESSAGES
from config.services import get_reachability_phone_keys, get_reachability_email_keys
from config.settings import LLM_TEMPERATURE_WORKFLOW
import prompt.static_workflow as prompts

logger = logging.getLogger(__name__)


class GetUserNameAgent(BaseAgent):
    async def on_enter(self):
        logger.info("GetUserNameAgent on_enter called")

        try:
            await self.room.local_participant.send_text(
                json.dumps({"clean": True}), topic="clean"
            )
        except Exception as e:
            logger.error(f"GetUserNameAgent clean message failed: {e}")

        # Skip if name already collected
        if self.userdata.name_collected:
            logger.info("Name already collected, moving to email/phone collection")
            return _create_email_phone_agent(self)

        await self._safe_reply(AGENT_MESSAGES["ask_name"])

    @function_tool
    async def collect_user_name(self, context: RunContext_T, name: str):
        """
        Call this ONLY when the user provides their name. Never call this tool preemptively.
        name (required): The name provided by the user.
        """
        logger.info(f"Collecting name={name}")
        self.userdata.name = name.capitalize().strip()
        self.userdata.name_collected = True
        return _create_email_phone_agent(self)


class GetUserEmailPhoneAgent(BaseAgent):
    """Smart contact collection — asks for phone OR email based on reachability preference."""

    async def on_enter(self):
        logger.info("GetUserEmailPhoneAgent on_enter called")

        # Get current language-specific reachability keys
        phone_keys = get_reachability_phone_keys()
        email_keys = get_reachability_email_keys()

        needs_phone = self.userdata.reachability in phone_keys
        needs_email = self.userdata.reachability in email_keys

        # Skip if already have needed info
        if needs_phone and self.userdata.phoneNumber:
            logger.info("Phone already collected, skipping to scheduling")
            return _create_schedule_agent(self)

        if needs_email and self.userdata.email:
            logger.info("Email already collected, skipping to scheduling")
            return _create_schedule_agent(self)

        # Ask for appropriate contact info
        if needs_phone:
            await self._safe_reply(AGENT_MESSAGES["ask_phone"])
        elif needs_email:
            await self._safe_reply(AGENT_MESSAGES["ask_email"])
        else:
            await self._safe_reply(AGENT_MESSAGES["ask_email_and_phone"])

    @function_tool
    async def collect_phone(self, context: RunContext_T, phoneNumber: str):
        """
        Call this when the user provides their phone number.
        phoneNumber (required): The phone number provided by the user.
        """
        logger.info(f"Collecting phone: phoneNumber={phoneNumber}")
        self.userdata.phoneNumber = phoneNumber.strip()
        return _create_schedule_agent(self)

    @function_tool
    async def collect_email(self, context: RunContext_T, email: str):
        """
        Call this when the user provides their email address.
        email (required): The email address provided by the user.
        """
        logger.info(f"Collecting email: email={email}")
        if is_valid_email_syntax(email):
            self.userdata.email = email.lower().strip()
            return _create_schedule_agent(self)
        else:
            logger.info("Email is invalid")
            await self._safe_reply(AGENT_MESSAGES["invalid_email"])

    @function_tool
    async def collect_contact_info(self, context: RunContext_T, email: str, phoneNumber: str):
        """
        Call this ONLY when the user provides BOTH phone number and email address (fallback for old flow).
        email (required): The email address provided by the user.
        phoneNumber (required): The phone number provided by the user.
        """
        logger.info(f"Collecting both: email={email}, phoneNumber={phoneNumber}")
        if is_valid_email_syntax(email):
            self.userdata.email = email.lower().strip()
            self.userdata.phoneNumber = phoneNumber.strip()
            return _create_schedule_agent(self)
        else:
            logger.info("Email is invalid")
            await self._safe_reply(AGENT_MESSAGES["invalid_email"])


class ScheduleCallAgent(BaseAgent):
    async def on_enter(self):
        logger.info("ScheduleCallAgent on_enter called")
        await self._safe_reply(AGENT_MESSAGES["schedule_call"])

    @function_tool
    async def schedule_call(self, context: RunContext_T, schedule_date: str, schedule_time: str):
        """
        Call this when the user approves the call schedule.
        schedule_date (required): The date agreed upon for the call. always return date in DD.MM.YYYY format.
        schedule_time (required): The time agreed upon for the call.
        """
        logger.info(f"Scheduling call on date={schedule_date}, time={schedule_time}")
        self.userdata.schedule_date = schedule_date
        self.userdata.schedule_time = schedule_time

        await self._safe_reply(AGENT_MESSAGES["confirm_schedule"])

        # GUARANTEED: always advance
        from agents.email_agents import SendEmailAgent
        return SendEmailAgent(
            instructions=prompts.BaseAgentPrompt,
            room=self.room,
            chat_ctx=self.chat_ctx,
            userdata=self.userdata,
            add_instruction=False,
            temperature=LLM_TEMPERATURE_WORKFLOW,
        )


# --- Helpers ---

def _select_contact_prompt(reachability: str) -> str:
    """Select the right prompt based on reachability preference."""
    phone_keys = get_reachability_phone_keys()
    email_keys = get_reachability_email_keys()

    if reachability in phone_keys:
        return prompts.GetUserPhoneOnlyPrompt
    elif reachability in email_keys:
        return prompts.GetUserEmailOnlyPrompt
    return prompts.GetUserEmailPrompt


def _create_email_phone_agent(agent):
    """Create GetUserEmailPhoneAgent with correct prompt and date context."""
    today = date.today()
    weekday = today.strftime("%A")
    prompt = _select_contact_prompt(agent.userdata.reachability)
    return GetUserEmailPhoneAgent(
        instructions=prompt + f"\nToday is {weekday}, {today}.",
        room=agent.room,
        chat_ctx=agent.chat_ctx,
        userdata=agent.userdata,
        add_instruction=False,
        temperature=LLM_TEMPERATURE_WORKFLOW,
    )


def _create_schedule_agent(agent):
    """Create ScheduleCallAgent with date context."""
    today = date.today()
    weekday = today.strftime("%A")
    return ScheduleCallAgent(
        instructions=prompts.ScheduleCallPrompt + f"\nToday is {weekday}, {today}.",
        room=agent.room,
        chat_ctx=agent.chat_ctx,
        userdata=agent.userdata,
        add_instruction=False,
        temperature=LLM_TEMPERATURE_WORKFLOW,
    )
