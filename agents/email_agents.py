"""
Email and summary agents — send appointment emails, offer summary, restart conversation.
Handles lead notifications, summary sending, and conversation lifecycle.

Used by: agents/contact_agents.py (ScheduleCallAgent → SendEmailAgent)
"""

import json
import logging
from livekit.agents import function_tool
from agents.base import BaseAgent
from core.session_state import UserData, RunContext_T
from core.lead_scoring import calculate_lead_degree
from config.company import COMPANY
from config.messages import AGENT_MESSAGES, UI_BUTTONS, FALLBACK_NOT_PROVIDED
from config.settings import LLM_TEMPERATURE_WORKFLOW
from utils.smtp import send_email, send_email_summary, send_lead_notification
from utils.history import save_conversation_to_file
from utils.webhook import send_session_webhook
import prompt.static_workflow as prompts
from datetime import datetime
from utils.filter_extraction import is_valid_email_syntax

logger = logging.getLogger(__name__)

COMPANY_LEAD_EMAILS = COMPANY["lead_emails"]


class SendEmailAgent(BaseAgent):
    async def on_enter(self):
        logger.info("SendEmailAgent on_enter called")
        try:
            await self.room.local_participant.send_text(
                json.dumps(UI_BUTTONS["appointment_confirm"]),
                topic="trigger",
            )
        except Exception as e:
            logger.error(f"SendEmailAgent buttons failed: {e}")

    @function_tool
    async def confirm_appointment(self, context: RunContext_T, confirm: bool):
        """
        Call this when the user confirms or declines the scheduled appointment.
        confirm (required): True if user confirms to send schedule appointment, False if user declines.
        """
        logger.info(f"User confirmation to send email: confirm={confirm}")

        if confirm:
            # Build products list from userdata
            products = self.userdata.ret_car if self.userdata.ret_car else []

            # 1. Customer email (nice-to-have — failure is OK)
            if self.userdata.email:
                try:
                    success = send_email(
                        self.userdata.email, self.userdata.schedule_date,
                        self.userdata.schedule_time, products=products,
                    )
                    if success:
                        logger.info("Customer email sent")
                    else:
                        logger.error("Customer email failed (SMTP returned False)")
                except Exception as e:
                    logger.error(f"Customer email crashed: {e}")
            else:
                logger.info("No customer email — skipping")

            # 2. Lead score (pure logic — cannot fail)
            lead_result = calculate_lead_degree(
                hot_count=self.userdata.last_hot_count,
                warm_count=self.userdata.last_warm_count,
                cool_count=self.userdata.last_cool_count,
                search_count=self.userdata.ret_count,
                products_shown=len(self.userdata.ret_car) if self.userdata.ret_car else 0,
                purchase_timing=self.userdata.purchase_timing,
                next_step=self.userdata.next_step,
                reachability=self.userdata.reachability,
            )

            # 3. Lead notification (critical — track success)
            all_leads_sent = True
            for company_email in COMPANY_LEAD_EMAILS:
                try:
                    lead_sent = send_lead_notification(
                        company_email=company_email,
                        customer_name=self.userdata.name or FALLBACK_NOT_PROVIDED,
                        customer_email=self.userdata.email,
                        customer_phone=self.userdata.phoneNumber,
                        schedule_date=self.userdata.schedule_date,
                        schedule_time=self.userdata.schedule_time,
                        reachability=self.userdata.reachability,
                        purchase_timing=self.userdata.purchase_timing,
                        next_step=self.userdata.next_step,
                        lead_degree=lead_result["score"],
                        confidence=lead_result["confidence"],
                        products=self.userdata.ret_car,
                    )
                    if lead_sent:
                        logger.info(f"Lead sent to {company_email}")
                    else:
                        all_leads_sent = False
                        logger.error(f"Lead to {company_email} failed")
                except Exception as e:
                    all_leads_sent = False
                    logger.error(f"Lead to {company_email} crashed: {e}")

            # 4. Voice response (choose message based on lead success)
            if all_leads_sent:
                await self._safe_reply(AGENT_MESSAGES["email_thanks"])
            else:
                await self._safe_reply(AGENT_MESSAGES["lead_email_failed"])

        else:
            await self._safe_reply(AGENT_MESSAGES["email_thanks"])

        # GUARANTEED: always advance to SummaryAgent
        return SummaryAgent(
            instructions=prompts.SummaryPrompt,
            room=self.room,
            chat_ctx=None,
            userdata=self.userdata,
            add_instruction=False,
            temperature=LLM_TEMPERATURE_WORKFLOW,
        )


class SummaryAgent(BaseAgent):
    async def on_enter(self):
        logger.info("SummaryAgent on_enter called")
        await self._safe_reply(AGENT_MESSAGES["offer_summary"])
        try:
            await self.room.local_participant.send_text(
                json.dumps(UI_BUTTONS["summary_offer"]),
                topic="trigger",
            )
        except Exception as e:
            logger.error(f"SummaryAgent buttons failed: {e}")

    @function_tool
    async def provide_summary(self, context: RunContext_T, confirm: bool):
        """
        Call this when the user requests a summary of the conversation. or not.
        confirm (required): Boolean indicating if the user wants the summary. return True if user say yes or confirm to provide summery, return False if user say no or doesnt confirm to provide summery.
        """
        logger.info(f"User confirmation to provide summary: confirm={confirm}")

        if confirm:
            if not self.userdata.email:
                return SummarySenderAgent(
                    instructions=prompts.SummarySenderPrompt,
                    room=self.room,
                    chat_ctx=None,
                    userdata=self.userdata,
                    add_instruction=False,
                    temperature=LLM_TEMPERATURE_WORKFLOW,
                )

            try:
                success = send_email_summary(
                    self.userdata.email,
                    summary_context=self.userdata.summary_context or "No conversation summary available.",
                )
            except Exception as e:
                logger.error(f"Summary email crashed: {e}")
                success = False

            if success:
                await self._safe_reply(AGENT_MESSAGES["summary_sent"])
            else:
                await self._safe_reply(AGENT_MESSAGES["email_error"])

        else:
            await self._safe_reply(AGENT_MESSAGES["no_summary_thanks"])

        # GUARANTEED: always advance to LastAgent
        return LastAgent(
            instructions="", room=self.room, chat_ctx=None,
            userdata=self.userdata, add_instruction=False,
            temperature=LLM_TEMPERATURE_WORKFLOW,
        )


class SummarySenderAgent(BaseAgent):
    """Collects email address for summary when user chose phone contact."""

    async def on_enter(self):
        logger.info("SummarySenderAgent on_enter called")
        await self._safe_reply(AGENT_MESSAGES["ask_email_for_summary"])

    @function_tool
    async def collect_summary_email(self, context: RunContext_T, email: str):
        """
        Call this when the user provides their email address for the summary.
        email (required): The email address provided by the user.
        """
        logger.info(f"Collecting email for summary: {email}")

        if is_valid_email_syntax(email):
            self.userdata.email = email.lower().strip()

            try:
                success = send_email_summary(
                    self.userdata.email,
                    summary_context=self.userdata.summary_context or "No conversation summary available.",
                )
            except Exception as e:
                logger.error(f"Summary email crashed: {e}")
                success = False

            if success:
                await self._safe_reply(AGENT_MESSAGES["summary_sent"])
            else:
                await self._safe_reply(AGENT_MESSAGES["email_error"])

            return LastAgent(
                instructions="", room=self.room, chat_ctx=None,
                userdata=self.userdata, add_instruction=False,
                temperature=LLM_TEMPERATURE_WORKFLOW,
            )
        else:
            logger.info("Invalid email address")
            await self._safe_reply(AGENT_MESSAGES["invalid_email"])


class LastAgent(BaseAgent):
    async def on_enter(self) -> None:
        logger.info("LastAgent on_enter called")
        try:
            await self.room.local_participant.send_text(
                json.dumps(UI_BUTTONS["new_conversation"]),
                topic="trigger",
            )
        except Exception as e:
            logger.error(f"LastAgent buttons failed: {e}")

    @function_tool
    async def start_new_conversation(self, context: RunContext_T):
        """
        If the user wants to start a new conversation. run this function.
        """
        try:
            await self.room.local_participant.send_text(
                json.dumps({"clean": True}), topic="clean"
            )
        except Exception as e:
            logger.error(f"Clean message failed: {e}")

        logger.info("Starting new conversation - saving history and resetting userdata")
        try:
            chat_history = list(self.session.history.items)

            # Save local history file
            save_conversation_to_file(chat_history, self.userdata)

            # Send webhook
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            await send_session_webhook(session_id, chat_history, self.userdata)

            self.userdata._history_saved = True
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")

        from agents.main_agent import BertaAssistant
        return BertaAssistant(room=self.room, userdata=UserData(), first_message=True)
