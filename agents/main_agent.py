"""
ConversationAgent — the main brain of Beauty Lounge Warendorf.

Handles greeting, treatment search, natural lead qualification, contact collection,
scheduling, and expert connection offers. Replaces the previous 9-agent chain with
a single LLM-driven agent that uses function tools for all side effects.

Used by: agent.py (entrypoint), agents/email_agents.py (CompletionAgent restart)
"""

import json
import asyncio
import logging
from typing import AsyncIterable, List, Dict, Any

from livekit.agents import function_tool, ModelSettings, Agent
from livekit.rtc import DataPacket

from agents.base import safe_generate_reply, create_realtime_model, _NEW_CONV_KEYS
from core.session_state import UserData, RunContext_T
from config.messages import AGENT_MESSAGES, UI_BUTTONS, CONVERSATION_RULES
from config.language import (
    handle_language_update,
    language_manager,
    get_language_instruction,
    get_language_prefix,
    lang_hint,
)
from prompt.static_main_agent import CONVERSATION_AGENT_PROMPT, CONVERSATION_AGENT_GREETING
from datetime import datetime
from utils.helpers import get_greeting, is_valid_email_syntax
from utils.history import normalize_messages, save_conversation_to_file
from utils.webhook import send_session_webhook
from utils.search_pipeline import SearchPipeline

logger = logging.getLogger(__name__)


# =============================================================================
# CONVERSATION AGENT
# =============================================================================

class ConversationAgent(Agent):
    """
    Single conversational agent that drives the entire Beauty Lounge experience.

    Responsibilities:
      - Greet the customer
      - Search and present treatments (facial, permanent makeup, wellness)
      - Assess lead interest (LLM-driven scoring, no keyword matching)
      - Offer expert connection with Patrizia (Yes/No buttons)
      - Collect contact info incrementally (name, email, phone, preferred contact)
      - Record GDPR consent
      - Schedule appointments
      - Save conversation summary
      - Hand off to CompletionAgent when contact collection is complete
    """

    def __init__(
        self,
        room,
        userdata: UserData | None = None,
        first_message: bool = False,
    ) -> None:
        if userdata:
            self.userdata = userdata
        self.first_message = first_message
        self.room = room
        self.search_pipeline = SearchPipeline()
        self._original_instructions = CONVERSATION_AGENT_PROMPT
        self._lang_listener_active = True

        # Register data received callback for language updates
        self._setup_data_listener()

        llm_model = create_realtime_model()

        # Include language prefix and suffix for maximum emphasis
        instructions_with_language = (
            get_language_prefix() + CONVERSATION_AGENT_PROMPT + get_language_instruction()
        )

        super().__init__(
            llm=llm_model,
            instructions=instructions_with_language,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # LANGUAGE HANDLING — listen for frontend language changes
    # ══════════════════════════════════════════════════════════════════════════

    def _setup_data_listener(self) -> None:
        """Set up listener for incoming data from frontend (e.g., language changes)."""
        @self.room.on("data_received")
        def on_data_received(data: DataPacket):
            asyncio.create_task(self._handle_data_received(data))

    async def _handle_data_received(self, data: DataPacket) -> None:
        """Handle incoming data packets from frontend."""
        if not self._lang_listener_active:
            return
        try:
            payload = (
                data.data.decode("utf-8") if isinstance(data.data, bytes) else data.data
            )
            parsed = json.loads(payload)

            if data.topic == "language":
                logger.info(f"Received language update: {parsed}")
                if handle_language_update(parsed):
                    new_lang = language_manager.get_language()
                    logger.info(f"Language successfully changed to: {new_lang}")
                    await self._update_agent_instructions()
                else:
                    logger.warning(f"Failed to update language: {parsed}")

            elif data.topic == "trigger":
                if isinstance(parsed, dict):
                    # Check for new conversation button first
                    for key in parsed.keys():
                        if str(key).lower() in _NEW_CONV_KEYS:
                            logger.info("New conversation button clicked in ConversationAgent")
                            if hasattr(self, "session") and self.session:
                                await self.session.generate_reply(
                                    user_input="I want to start a new conversation"
                                )
                            return
                    # Normal button — inject value as user input
                    value = next(iter(parsed.values()), None)
                    if value and hasattr(self, "session") and self.session:
                        logger.info(f"Button clicked — injecting as user input: {value}")
                        await self.session.generate_reply(user_input=str(value))

        except json.JSONDecodeError as e:
            logger.debug(f"Data received is not valid JSON: {e}")
        except Exception as e:
            logger.error(f"Error handling data received: {e}")

    async def _update_agent_instructions(self) -> None:
        """Update the agent's instructions with current language setting."""
        try:
            # Capture language immediately before any await to prevent stale reads
            new_lang = language_manager.get_language()
            instructions = self._original_instructions
            new_instructions = (
                get_language_prefix() + instructions + get_language_instruction()
            )

            self._instructions = new_instructions
            if hasattr(self, "_activity") and self._activity:
                await self._activity.update_instructions(new_instructions)

            # Update transcription language hint (uses captured new_lang)
            if hasattr(self, "session") and self.session and self.session.llm:
                try:
                    from livekit.plugins.openai import AudioTranscription
                    self.session.llm.update_options(
                        input_audio_transcription=AudioTranscription(
                            model="gpt-4o-mini-transcribe",
                            language=new_lang,
                        ),
                    )
                except Exception as e:
                    logger.warning(f"Could not update transcription language to {new_lang}: {e}")

            logger.info(f"Agent instructions updated for language: {new_lang}")
        except Exception as e:
            logger.error(f"Failed to update agent instructions: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # LIFECYCLE
    # ══════════════════════════════════════════════════════════════════════════

    async def on_enter(self):
        logger.info(
            f"ConversationAgent on_enter (first_message={self.first_message}, "
            f"searches={self.userdata.search_count})"
        )

        if self.first_message:
            try:
                greeting_prefix = get_greeting()
                await self._safe_reply(
                    CONVERSATION_AGENT_GREETING.format(greeting_prefix=greeting_prefix)
                )
            except Exception as e:
                logger.error(f"ConversationAgent greeting failed: {e}")
        else:
            try:
                return await super().on_enter()
            except Exception as e:
                logger.error(f"ConversationAgent on_enter failed: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    async def _safe_reply(self, instructions: str) -> bool:
        """Convenience wrapper — calls safe_generate_reply with language injection."""
        instructions = get_language_prefix() + instructions + get_language_instruction()
        return await safe_generate_reply(self.session, self.room, instructions)

    # ══════════════════════════════════════════════════════════════════════════
    # TREATMENT DATA RETRIEVAL — Pinecone vector search
    # ══════════════════════════════════════════════════════════════════════════

    def _format_pinecone_results_for_llm(self, results: List[Dict[str, Any]], max_results: int = 5) -> str:
        """Format Pinecone search results for LLM context."""
        if not results:
            return f"No matching treatments found. {lang_hint()}"

        formatted = []
        for item in results[:max_results]:
            name = item.get("name", "Unknown treatment")
            desc_parts = [f"**{name}**"]

            if "Introduction" in item:
                desc_parts.append(f"Description: {item['Introduction']}")
            if "Features" in item:
                desc_parts.append(f"Details: {item['Features']}")
            if "Benefits to Clients" in item:
                desc_parts.append(f"Benefits: {item['Benefits to Clients']}")
            if "url" in item:
                desc_parts.append(f"URL: {item['url']}")

            formatted.append("\n".join(desc_parts))

        return "\n\n---\n\n".join(formatted)

    # ══════════════════════════════════════════════════════════════════════════
    # FUNCTION TOOL 1 — SEARCH (Services & Products)
    # ══════════════════════════════════════════════════════════════════════════

    @function_tool()
    async def search(
        self,
        context: RunContext_T,
        query: str,
        category: str,
    ):
        """
        Search for services or products offered by the company.

        Args:
            query: The user's search query
            category: MUST be one of:
                      - "service": For beauty SERVICES (treatments, facials, massages,
                        permanent makeup, wellness, skincare treatments)
                      - "product": For retail PRODUCTS users can BUY (skincare products,
                        gift sets, items for purchase)
        """
        try:
            logger.info(f"search: category={category}, query={query!r}")
            return await self._search_inner(query, category)
        except Exception as e:
            logger.error(f"search failed: {e}")
            return f"Search temporarily unavailable. Ask customer to try again. {lang_hint()}"

    async def _search_inner(
        self,
        query: str,
        category: str,
    ) -> str:
        """Core search logic — queries Pinecone index, sends to frontend, returns LLM context."""
        # Validate category
        valid_categories = ["service", "product"]
        if category not in valid_categories:
            logger.warning(f"Invalid category '{category}', defaulting to 'service'")
            category = "service"

        # Get conversation history
        history = self._chat_ctx.items
        cleaned_history = normalize_messages(history)

        if cleaned_history and cleaned_history[-1]["role"] != "user":
            return f"Waiting for customer message. {lang_hint()}"

        # Update search counter
        self.userdata.search_count += 1

        user_messages = [
            chat["message"] for chat in cleaned_history if chat["role"] == "user"
        ]
        last_user_msg = user_messages[-1] if user_messages else ""

        # Query Pinecone index based on category
        try:
            if category == "product":
                search_results = await asyncio.to_thread(
                    self.search_pipeline.search_products,
                    query=last_user_msg,
                    top_k=5,
                )
            else:
                search_results = await asyncio.to_thread(
                    self.search_pipeline.search_services,
                    query=last_user_msg,
                    top_k=5,
                )
        except Exception as e:
            logger.error(f"Pinecone search failed: {e}")
            search_results = []

        # Format for LLM context
        results_text = self._format_pinecone_results_for_llm(search_results)

        # Send results to frontend via "products" topic
        try:
            frontend_payload = []
            for item in search_results[:5]:
                frontend_payload.append({
                    "product_name": item.get("name", "Unknown"),
                    "url": item.get("url", ""),
                    "category": category,
                    "image": [item.get("image_link", "")] if item.get("image_link") else ["https://image.ayand.cloud/BL_logo.png"],
                })

            logger.info(
                f"Frontend results (category={category}): "
                f"{[p['product_name'] for p in frontend_payload]}"
            )

            if frontend_payload:
                asyncio.create_task(
                    self.room.local_participant.send_text(
                        json.dumps(frontend_payload),
                        topic="products",
                    )
                )
        except Exception as e:
            logger.error(f"Failed to send results to frontend: {e}")

        # Store results in userdata
        self.userdata.last_search_results = search_results[:5]

        # Build LLM context
        category_label = "PRODUCT" if category == "product" else "SERVICE"
        context_parts = [
            f"USER QUERY: {last_user_msg}",
            f"SEARCH NUMBER: {self.userdata.search_count}",
            "",
            f"=== RELEVANT {category_label} DATA ===",
            results_text,
            f"Also explain shortly about these {category}s and their relation with user query: "
            f"{[p['product_name'] for p in frontend_payload]}",
        ]

        # Append conversation rules
        context_parts.extend(["", "=== CONVERSATION RULES ===", CONVERSATION_RULES])

        return get_language_prefix() + "\n".join(context_parts) + get_language_instruction()

    # ══════════════════════════════════════════════════════════════════════════
    # FUNCTION TOOL 2 — ASSESS LEAD INTEREST
    # ══════════════════════════════════════════════════════════════════════════

    @function_tool
    async def assess_lead_interest(
        self,
        context: RunContext_T,
        score: int,
        level: str,
        reasoning: str,
    ):
        """
        Call this to record your assessment of the customer's interest level.
        Call whenever you notice a meaningful change in engagement.

        Args:
            score: Interest score 0-10 (0=browsing, 5=warm, 8=hot, 10=ready to book)
            level: One of HOT, WARM, COOL, MILD
            reasoning: Brief explanation (e.g., "Asked about prices for 2 treatments and mentioned wanting to book soon")
        """
        self.userdata.lead_score = max(0, min(10, score))
        self.userdata.lead_level = (
            level.upper() if level.upper() in ("HOT", "WARM", "COOL", "MILD") else "MILD"
        )
        self.userdata.lead_reasoning = reasoning.strip()
        logger.info(f"Lead assessed: score={score}, level={level}, reason={reasoning}")
        return f"Lead assessment saved. Continue naturally. {lang_hint()}"

    # ══════════════════════════════════════════════════════════════════════════
    # FUNCTION TOOL 3 — OFFER EXPERT CONNECTION
    # ══════════════════════════════════════════════════════════════════════════

    @function_tool
    async def offer_expert_connection(self, context: RunContext_T):
        """
        Call this when you want to offer connecting the customer with our beautician Patrizia.
        This sends Yes/No buttons to the frontend. Wait for the customer's response,
        then call handle_expert_response.
        """
        if self.userdata.expert_offered:
            return f"Expert connection already offered. Do not offer again. {lang_hint()}"
        self.userdata.expert_offered = True
        try:
            await self.room.local_participant.send_text(
                json.dumps(
                    UI_BUTTONS.get("expert_offer", {"Ja": "Ja", "Nein": "Nein"})
                ),
                topic="trigger",
            )
        except Exception as e:
            logger.error(f"Failed to send expert buttons: {e}")
        logger.info("Expert connection offered to customer")
        return f"Buttons sent. Wait for customer response. {lang_hint()}"

    # ══════════════════════════════════════════════════════════════════════════
    # FUNCTION TOOL 4 — HANDLE EXPERT RESPONSE
    # ══════════════════════════════════════════════════════════════════════════

    @function_tool
    async def handle_expert_response(self, context: RunContext_T, accepted: bool):
        """
        Call this when the customer responds to the expert connection offer (Yes/No buttons).
        accepted=True when user says yes/ja/sure, accepted=False when they decline.

        If accepted, continue the conversation naturally — collect their contact info.
        """
        self.userdata.expert_accepted = accepted
        logger.info(f"Expert response: accepted={accepted}")
        if not accepted:
            await self._safe_reply(
                "No problem! I'm happy to help with any other questions about our treatments."
            )
            return f"Customer declined. Reply generated. {lang_hint()}"
        return f"Customer accepted. Collect contact info now. {lang_hint()}"

    # ══════════════════════════════════════════════════════════════════════════
    # FUNCTION TOOL 5 — SAVE CONTACT INFO
    # ══════════════════════════════════════════════════════════════════════════

    @function_tool
    async def save_contact_info(
        self,
        context: RunContext_T,
        name: str = None,
        email: str = None,
        phone: str = None,
        preferred_contact: str = None,
    ):
        """
        Save customer contact information. Call this incrementally as the customer
        provides each piece of info. All parameters are optional — save whatever is provided.

        Args:
            name: Customer's name
            email: Customer's email address
            phone: Customer's phone number
            preferred_contact: How they prefer to be reached: "phone", "whatsapp", or "email"
        """
        # Save all non-email fields first
        if name:
            self.userdata.name = name.strip().title()
            logger.info(f"Saved name: {self.userdata.name}")
        if phone:
            self.userdata.phone = phone.strip()
            logger.info(f"Saved phone: {self.userdata.phone}")
        if preferred_contact and preferred_contact in ("phone", "whatsapp", "email"):
            self.userdata.preferred_contact = preferred_contact
            logger.info(f"Saved preferred contact: {preferred_contact}")

        # Validate and save email last (so other fields are not lost on invalid email)
        if email:
            if is_valid_email_syntax(email.strip()):
                self.userdata.email = email.strip().lower()
                logger.info(f"Saved email: {self.userdata.email}")
            else:
                return f"Email seems invalid. Other info saved. Ask for email again. {lang_hint()}"

        # Check if enough contact info is now available for consent step
        has_name = bool(self.userdata.name)
        has_contact = bool(self.userdata.email) or bool(self.userdata.phone)
        needs_phone = self.userdata.preferred_contact == "phone" and not self.userdata.phone

        if has_name and has_contact and not needs_phone and not self.userdata.consent_given:
            if not self.userdata.consent_buttons_shown:
                # Auto-send consent buttons
                buttons_sent = False
                try:
                    await self.room.local_participant.send_text(
                        json.dumps(UI_BUTTONS.get("consent", {"Yes": "Yes", "No": "No"})),
                        topic="trigger",
                    )
                    self.userdata.consent_buttons_shown = True
                    buttons_sent = True
                    logger.info("Consent buttons auto-sent after contact info complete")
                except Exception as e:
                    logger.error(f"Failed to auto-send consent buttons: {e}")
                if buttons_sent:
                    return (
                        f"Contact info saved. Consent buttons are now displayed. "
                        f"You MUST now ask for GDPR consent: "
                        f"'May we use your contact information to reach out to you?' "
                        f"Wait for response, then call record_consent(). {lang_hint()}"
                    )
                else:
                    return (
                        f"Contact info saved. Buttons failed to send. "
                        f"Ask for GDPR consent verbally and call record_consent(). {lang_hint()}"
                    )
            else:
                return (
                    f"Contact info saved. Consent buttons already shown. "
                    f"Ask for consent if not yet given, then call record_consent(). {lang_hint()}"
                )
        elif has_name and has_contact and not needs_phone and self.userdata.consent_given:
            return (
                f"Contact info saved. All requirements met. "
                f"Call save_conversation_summary() then complete_contact_collection(). {lang_hint()}"
            )
        elif has_name and not has_contact:
            return f"Name saved. Now ask for email or phone number. {lang_hint()}"
        elif not has_name and has_contact:
            return f"Contact saved. Now ask for the customer's name. {lang_hint()}"
        else:
            return f"Saved. Still need: name + (email or phone). {lang_hint()}"

    # ══════════════════════════════════════════════════════════════════════════
    # FUNCTION TOOL 6a — SHOW CONSENT BUTTONS
    # ══════════════════════════════════════════════════════════════════════════

    @function_tool
    async def show_consent_buttons(self, context: RunContext_T):
        """
        Call this BEFORE asking the customer for GDPR consent.
        This sends Yes/No buttons to the frontend. Then ask verbally and wait
        for the customer's response, then call record_consent.
        """
        if self.userdata.consent_buttons_shown:
            return f"Consent buttons already shown. Do not show again. {lang_hint()}"
        try:
            await self.room.local_participant.send_text(
                json.dumps(
                    UI_BUTTONS.get("consent", {"Yes": "Yes", "No": "No"})
                ),
                topic="trigger",
            )
            self.userdata.consent_buttons_shown = True
        except Exception as e:
            logger.error(f"Failed to send consent buttons: {e}")
        logger.info("Consent buttons sent to customer")
        return f"Consent buttons sent. Now ask for consent verbally and wait for response. {lang_hint()}"

    # ══════════════════════════════════════════════════════════════════════════
    # FUNCTION TOOL 6b — RECORD CONSENT
    # ══════════════════════════════════════════════════════════════════════════

    @function_tool
    async def record_consent(self, context: RunContext_T, consent: bool):
        """
        Record the customer's explicit consent to be contacted using their provided information.
        You MUST ask for consent after collecting contact info and BEFORE handing off.

        Args:
            consent: True if customer agrees to be contacted, False if they decline.
        """
        self.userdata.consent_given = consent
        logger.info(f"Consent recorded: {consent}")
        return f"Consent recorded. Continue. {lang_hint()}"

    # ══════════════════════════════════════════════════════════════════════════
    # FUNCTION TOOL 7 — SCHEDULE APPOINTMENT
    # ══════════════════════════════════════════════════════════════════════════

    @function_tool
    async def schedule_appointment(
        self, context: RunContext_T, date: str, time: str
    ):
        """
        Save the customer's preferred appointment date and time.

        Args:
            date: Preferred date (e.g., "20.02.2026", "next Monday", "morgen")
            time: Preferred time (e.g., "14:00", "nachmittags", "morning")
        """
        self.userdata.schedule_date = date.strip()
        self.userdata.schedule_time = time.strip()
        logger.info(f"Appointment scheduled: {date} at {time}")
        return f"Appointment saved. Confirm with customer. {lang_hint()}"

    # ══════════════════════════════════════════════════════════════════════════
    # FUNCTION TOOL 8 — SAVE CONVERSATION SUMMARY
    # ══════════════════════════════════════════════════════════════════════════

    @function_tool
    async def save_conversation_summary(self, context: RunContext_T, summary: str):
        """
        Call this to save a brief summary of the conversation before offering expert
        connection or ending.
        summary (required): A 1-2 sentence summary of what the customer discussed
        and their interest level.
        """
        logger.info(f"Conversation summary: {summary}")
        self.userdata.conversation_summary = summary.strip()
        return f"Summary saved. {lang_hint()}"

    # ══════════════════════════════════════════════════════════════════════════
    # FUNCTION TOOL 9 — COMPLETE CONTACT COLLECTION
    # ══════════════════════════════════════════════════════════════════════════

    @function_tool
    async def complete_contact_collection(self, context: RunContext_T):
        """
        Call this when you have collected sufficient contact information and consent.
        This validates the data and hands off to the completion agent for email sending.

        Requirements: name + (email or phone) + consent_given = True (+ phone if callback requested)
        """
        missing = []
        if not self.userdata.name:
            missing.append("Name")
        if not self.userdata.email and not self.userdata.phone:
            missing.append("Email or Phone")
        if self.userdata.preferred_contact == "phone" and not self.userdata.phone:
            missing.append("Phone number (callback requested)")
        if not self.userdata.consent_given:
            missing.append("Consent to be contacted")

        if missing:
            missing_str = ", ".join(missing)
            return f"Still missing: {missing_str}. Ask customer. {lang_hint()}"

        # Deactivate language listener before handoff to avoid duplicate updates
        self._lang_listener_active = False

        # Send clean signal to frontend
        try:
            await self.room.local_participant.send_text(
                json.dumps({"clean": True}), topic="clean"
            )
        except Exception as e:
            logger.error(f"Clean message failed: {e}")

        from agents.email_agents import CompletionAgent

        return CompletionAgent(
            room=self.room,
            userdata=self.userdata,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # FUNCTION TOOL 10 — SHOW FEATURED SERVICES
    # ══════════════════════════════════════════════════════════════════════════

    @function_tool
    async def show_featured_services(self, context: RunContext_T):
        """
        Show a selection of featured beauty SERVICES to the customer.
        Call this ONCE in your first response after the greeting to give the customer
        a visual overview. Do NOT call this again — it only works once.
        """
        if self.userdata.featured_shown:
            return f"Already shown. Do not call again. {lang_hint()}"

        self.userdata.featured_shown = True

        try:
            # Query Pinecone for featured services
            featured_results = await asyncio.to_thread(
                self.search_pipeline.get_featured_services,
                treatments_count=3,
                pmu_count=2,
                wellness_count=2,
            )

            showcase = []
            for item in featured_results:
                category = item.get("category", "treatments")
                showcase.append({
                    "product_name": item.get("name", "Unknown"),
                    "url": item.get("url", ""),
                    "category": category,
                    "image": [item.get("image_link", "")] if item.get("image_link") else ["https://image.ayand.cloud/BL_logo.png"],
                })

            if showcase:
                asyncio.create_task(
                    self.room.local_participant.send_text(
                        json.dumps(showcase), topic="products"
                    )
                )
                logger.info(f"Featured services sent: {[p['product_name'] for p in showcase]}")
        except Exception as e:
            logger.error(f"Failed to send featured services: {e}")

        return f"Services displayed. Continue naturally. {lang_hint()}"

    # ══════════════════════════════════════════════════════════════════════════
    # FUNCTION TOOL 11 — SHOW NEW CONVERSATION BUTTON
    # ══════════════════════════════════════════════════════════════════════════

    @function_tool
    async def show_new_conversation_button(self, context: RunContext_T):
        """
        Show a 'New Conversation' button. Call this ONLY when the customer
        insists on leaving and you have already tried to help them further.
        You MUST call save_conversation_summary() BEFORE calling this.
        """
        try:
            await self.room.local_participant.send_text(
                json.dumps(UI_BUTTONS["new_conversation"]),
                topic="trigger",
            )
        except Exception as e:
            logger.error(f"New conversation button failed: {e}")
        return f"New conversation button shown. Say a brief warm goodbye. {lang_hint()}"

    # ══════════════════════════════════════════════════════════════════════════
    # FUNCTION TOOL 12 — START NEW CONVERSATION
    # ══════════════════════════════════════════════════════════════════════════

    @function_tool
    async def start_new_conversation(self, context: RunContext_T):
        """Call when the customer wants to start a new conversation."""
        self._lang_listener_active = False
        try:
            await self.room.local_participant.send_text(
                json.dumps({"clean": True}), topic="clean"
            )
        except Exception as e:
            logger.error(f"Clean message failed: {e}")

        logger.info("Starting new conversation from ConversationAgent")
        try:
            chat_history = list(self.session.history.items)
            save_conversation_to_file(chat_history, self.userdata)
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            await send_session_webhook(session_id, chat_history, self.userdata)
            self.userdata._history_saved = True
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")

        return ConversationAgent(room=self.room, userdata=UserData())

    # ══════════════════════════════════════════════════════════════════════════
    # TRANSCRIPTION — streams text to frontend via "message" topic
    # ══════════════════════════════════════════════════════════════════════════

    async def transcription_node(
        self, text: AsyncIterable[str], model_settings: ModelSettings
    ) -> AsyncIterable[str]:
        agent_response = ""
        async for delta in text:
            agent_response += delta
            yield delta

        # Send complete message to frontend
        try:
            await self.room.local_participant.send_text(
                json.dumps({"agent_response": agent_response}),
                topic="message",
            )
        except Exception as e:
            logger.error(f"Failed to send transcription: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # INSTRUCTION UPDATE — preserves chat context across language changes
    # ══════════════════════════════════════════════════════════════════════════

    async def update_instructions(self, instructions: str) -> None:
        """
        Updates the agent's instructions.

        If the agent is running in realtime mode, this method also updates
        the instructions for the ongoing realtime session.

        Args:
            instructions: The new instructions to set for the agent.
        """
        current_chat_ctx = self._chat_ctx

        self._instructions = instructions

        if hasattr(self, "_activity") and self._activity:
            await self._activity.update_instructions(instructions)

        if current_chat_ctx:
            self._chat_ctx = current_chat_ctx
