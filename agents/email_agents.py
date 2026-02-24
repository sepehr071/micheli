"""
Completion agent — send appointment emails, offer summary, restart conversation.

Replaces the old SendEmailAgent, SummaryAgent, SummarySenderAgent, and LastAgent
with a single agent that uses 3 function tools.

Used by: agents/main_agent.py (ConversationAgent -> CompletionAgent)
"""

import json
import logging
from datetime import datetime

from livekit.agents import function_tool

from agents.base import BaseAgent
from core.session_state import UserData, RunContext_T
from config.company import COMPANY
from config.messages import AGENT_MESSAGES, UI_BUTTONS, FALLBACK_NOT_PROVIDED
from utils.smtp import send_email, send_email_summary, send_lead_notification
from utils.history import save_conversation_to_file
from utils.webhook import send_session_webhook
from utils.helpers import is_valid_email_syntax

logger = logging.getLogger(__name__)

COMPANY_LEAD_EMAILS = COMPANY["lead_emails"]


class CompletionAgent(BaseAgent):
    """Handles appointment confirmation, summary delivery, and conversation restart.

    Function tools:
        send_appointment_emails  — confirm/decline appointment, send lead notifications
        send_summary_email       — send conversation summary to customer's email
        start_new_conversation   — reset UI, save history, webhook, restart
    """

    def __init__(self, room, userdata, chat_ctx=None):
        from config.settings import LLM_TEMPERATURE_WORKFLOW
        import prompt.static_workflow as prompts

        super().__init__(
            instructions=prompts.COMPLETION_AGENT_PROMPT,
            room=room,
            userdata=userdata,
            chat_ctx=chat_ctx,
            add_instruction=False,
            temperature=LLM_TEMPERATURE_WORKFLOW,
        )

    async def on_enter(self):
        """Show appointment confirmation buttons when entering this agent."""
        logger.info("CompletionAgent on_enter")
        try:
            await self.room.local_participant.send_text(
                json.dumps(UI_BUTTONS["appointment_confirm"]),
                topic="trigger",
            )
        except Exception as e:
            logger.error(f"CompletionAgent buttons failed: {e}")

    # -----------------------------------------------------------------
    # Tool 1: Appointment emails
    # -----------------------------------------------------------------

    @function_tool
    async def send_appointment_emails(self, context: RunContext_T, confirm: bool):
        """
        Call this when the user confirms or declines the scheduled appointment.
        confirm (required): True if user confirms to send the appointment, False if user declines.
        """
        logger.info(f"Appointment confirmation: confirm={confirm}")

        if confirm:
            products = self.userdata.last_search_results or []

            # 1. Customer confirmation email (nice-to-have — failure is OK)
            if self.userdata.email:
                try:
                    success = send_email(
                        self.userdata.email,
                        self.userdata.schedule_date,
                        self.userdata.schedule_time,
                        products=products,
                    )
                    if success:
                        logger.info("Customer confirmation email sent")
                    else:
                        logger.error("Customer confirmation email failed (SMTP returned False)")
                except Exception as e:
                    logger.error(f"Customer confirmation email crashed: {e}")
            else:
                logger.info("No customer email on file — skipping confirmation email")

            # 2. Lead notification to company (critical — log all failures)
            lead_score = self.userdata.lead_score
            confidence = self.userdata.lead_score * 10  # convert 0-10 to 0-100 scale

            all_leads_sent = True
            for company_email in COMPANY_LEAD_EMAILS:
                try:
                    lead_sent = send_lead_notification(
                        company_email=company_email,
                        customer_name=self.userdata.name or FALLBACK_NOT_PROVIDED,
                        customer_email=self.userdata.email,
                        customer_phone=self.userdata.phone,
                        schedule_date=self.userdata.schedule_date,
                        schedule_time=self.userdata.schedule_time,
                        reachability=self.userdata.preferred_contact or FALLBACK_NOT_PROVIDED,
                        purchase_timing=FALLBACK_NOT_PROVIDED,
                        next_step=FALLBACK_NOT_PROVIDED,
                        lead_degree=lead_score,
                        confidence=confidence,
                        products=products,
                    )
                    if lead_sent:
                        logger.info(f"Lead notification sent to {company_email}")
                    else:
                        all_leads_sent = False
                        logger.error(f"Lead notification to {company_email} failed")
                except Exception as e:
                    all_leads_sent = False
                    logger.error(f"Lead notification to {company_email} crashed: {e}")

            # 3. Voice response based on lead email success
            if all_leads_sent:
                await self._safe_reply(AGENT_MESSAGES["email_thanks"])
            else:
                await self._safe_reply(AGENT_MESSAGES["lead_email_failed"])

        else:
            # User declined — acknowledge politely
            await self._safe_reply(AGENT_MESSAGES["email_thanks"])

        # Always offer summary after appointment handling
        await self._safe_reply(AGENT_MESSAGES["offer_summary"])
        try:
            await self.room.local_participant.send_text(
                json.dumps(UI_BUTTONS["summary_offer"]),
                topic="trigger",
            )
        except Exception as e:
            logger.error(f"Summary offer buttons failed: {e}")

    # -----------------------------------------------------------------
    # Tool 2: Summary email
    # -----------------------------------------------------------------

    @function_tool
    async def send_summary_email(self, context: RunContext_T, email: str = None):
        """
        Call this when the user wants a conversation summary emailed, or declines.
        email (optional): Email address provided by user. If empty/null, uses stored email.
        Pass the string "decline" if the user does not want a summary.
        """
        # Handle decline
        if email and email.strip().lower() == "decline":
            await self._safe_reply(AGENT_MESSAGES["no_summary_thanks"])
            # Show new conversation buttons
            try:
                await self.room.local_participant.send_text(
                    json.dumps(UI_BUTTONS["new_conversation"]),
                    topic="trigger",
                )
            except Exception as e:
                logger.error(f"New conversation buttons failed: {e}")
            return

        # Determine recipient email
        recipient = None
        if email and email.strip():
            clean_email = email.strip().lower()
            if is_valid_email_syntax(clean_email):
                self.userdata.email = clean_email
                recipient = clean_email
            else:
                logger.info(f"Invalid email syntax: {email}")
                await self._safe_reply(AGENT_MESSAGES["invalid_email"])
                return
        elif self.userdata.email:
            recipient = self.userdata.email
        else:
            # No email available — ask for it
            await self._safe_reply(AGENT_MESSAGES["ask_email_for_summary"])
            return

        # Send the summary
        summary_context = self.userdata.conversation_summary
        if not summary_context:
            # Fall back to session history if no agent-written summary
            try:
                from utils.history import normalize_messages
                chat_history = list(self.session.history.items)
                messages = normalize_messages(chat_history)
                summary_context = "\n".join(
                    f"{m['role']}: {m['message']}" for m in messages[-20:]
                )
            except Exception as e:
                logger.error(f"Failed to build summary from history: {e}")
                summary_context = "No conversation summary available."

        try:
            success = send_email_summary(recipient, summary_context=summary_context)
        except Exception as e:
            logger.error(f"Summary email crashed: {e}")
            success = False

        if success:
            await self._safe_reply(AGENT_MESSAGES["summary_sent"])
        else:
            await self._safe_reply(AGENT_MESSAGES["email_error"])

        # Show new conversation buttons
        try:
            await self.room.local_participant.send_text(
                json.dumps(UI_BUTTONS["new_conversation"]),
                topic="trigger",
            )
        except Exception as e:
            logger.error(f"New conversation buttons failed: {e}")

    # -----------------------------------------------------------------
    # Tool 3: New conversation
    # -----------------------------------------------------------------

    @function_tool
    async def start_new_conversation(self, context: RunContext_T):
        """
        Call this when the user wants to start a new conversation.
        """
        # 1. Clean the frontend
        try:
            await self.room.local_participant.send_text(
                json.dumps({"clean": True}), topic="clean"
            )
        except Exception as e:
            logger.error(f"Clean message failed: {e}")

        # 2. Save conversation history + send webhook
        logger.info("Starting new conversation — saving history and sending webhook")
        try:
            chat_history = list(self.session.history.items)

            save_conversation_to_file(chat_history, self.userdata)

            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            await send_session_webhook(session_id, chat_history, self.userdata)

            self.userdata._history_saved = True
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")

        # 3. Return a fresh ConversationAgent
        from agents.main_agent import ConversationAgent
        return ConversationAgent(room=self.room, userdata=UserData())
