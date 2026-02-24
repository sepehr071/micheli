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

from agents.base import safe_generate_reply, create_realtime_model
from core.session_state import UserData, RunContext_T
from config.messages import AGENT_MESSAGES, UI_BUTTONS, CONVERSATION_RULES
from config.language import (
    handle_language_update,
    language_manager,
    get_language_instruction,
    get_language_prefix,
)
from prompt.static_main_agent import CONVERSATION_AGENT_PROMPT, CONVERSATION_AGENT_GREETING
from utils.helpers import get_greeting, is_valid_email_syntax
from utils.history import normalize_messages
from utils.data_loader import data_loader

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
        self._original_instructions = CONVERSATION_AGENT_PROMPT

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

        except json.JSONDecodeError as e:
            logger.debug(f"Data received is not valid JSON: {e}")
        except Exception as e:
            logger.error(f"Error handling data received: {e}")

    async def _update_agent_instructions(self) -> None:
        """Update the agent's instructions with current language setting."""
        try:
            current_chat_ctx = self._chat_ctx

            instructions = self._original_instructions
            new_instructions = (
                get_language_prefix() + instructions + get_language_instruction()
            )

            self._instructions = new_instructions
            if hasattr(self, "_activity") and self._activity:
                await self._activity.update_instructions(new_instructions)

            if current_chat_ctx:
                self._chat_ctx = current_chat_ctx

            logger.info(
                f"Agent instructions updated for language: {language_manager.get_language()}"
            )
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
    # TREATMENT DATA RETRIEVAL — local data files
    # ══════════════════════════════════════════════════════════════════════════

    def _get_relevant_data(self, categories: List[str]) -> Dict[str, Any]:
        """
        Get relevant data based on classified categories.
        Returns a dictionary with data for each requested category.
        """
        result: Dict[str, Any] = {
            "products": [],
            "use_cases": [],
        }

        if "all" in categories:
            result["products"] = data_loader.load_treatments() + data_loader.load_permanent_makeup()
            result["use_cases"] = data_loader.load_wellness()
            return result

        if "treatments" in categories:
            result["products"].extend(data_loader.load_treatments())

        if "permanent_makeup" in categories:
            result["products"].extend(data_loader.load_permanent_makeup())

        if "wellness" in categories:
            result["use_cases"] = data_loader.load_wellness()

        # Fallback: return treatments if nothing matched
        if not result["products"] and not result["use_cases"]:
            result["products"] = data_loader.load_treatments()

        return result

    def _format_products_for_llm(
        self, products: List[Dict[str, Any]], max_products: int = 5
    ) -> str:
        """Format treatment data for LLM context — uses LLM context files."""
        if not products:
            return "Keine passenden Behandlungen gefunden."

        formatted = []
        for product in products[:max_products]:
            name = product.get("name", "Unbekannte Behandlung")
            url = product.get("url", "")

            desc_parts = [f"**{name}**"]

            if "Introduction" in product:
                desc_parts.append(f"Beschreibung: {product['Introduction']}")
            if "Features" in product:
                desc_parts.append(f"Details: {product['Features']}")
            if "Benefits to Clients" in product:
                desc_parts.append(f"Vorteile: {product['Benefits to Clients']}")
            if "duration_min" in product:
                desc_parts.append(f"Dauer: {product['duration_min']} Min.")
            if "treatment_category" in product:
                desc_parts.append(f"Kategorie: {product['treatment_category']}")
            if "skin_type" in product:
                desc_parts.append(f"Hauttyp: {product['skin_type']}")
            if "method" in product:
                desc_parts.append(f"Methode: {product['method']}")
            if url:
                desc_parts.append(f"URL: {url}")

            formatted.append("\n".join(desc_parts))

        return "\n\n---\n\n".join(formatted)

    def _format_use_cases_for_llm(
        self, use_cases: List[Dict[str, Any]], max_cases: int = 3
    ) -> str:
        """Format wellness data for LLM context."""
        if not use_cases:
            return ""

        formatted = []
        for case in use_cases[:max_cases]:
            title = case.get("title", case.get("name", "Unbekannt"))
            summary = case.get("summary", case.get("Introduction", ""))

            case_parts = [f"**{title}**"]
            if summary:
                case_parts.append(f"Beschreibung: {summary}")

            formatted.append("\n".join(case_parts))

        return "\n\n---\n\n".join(formatted)

    def _get_llm_context(self, category: str) -> str:
        """Get LLM-optimized context for a category from pre-built markdown files."""
        return data_loader.get_llm_context_by_category(category)

    # ══════════════════════════════════════════════════════════════════════════
    # FUNCTION TOOL 1 — SEARCH TREATMENTS
    # ══════════════════════════════════════════════════════════════════════════

    @function_tool()
    async def search_treatments(
        self,
        context: RunContext_T,
        query: str,
        category: str,
        mentioned_treatments: list[str] = None,
    ):
        """
        MUST be called for ANY treatment-related query before responding.
        Call this when user asks about: treatments, services, skincare, permanent makeup,
        massage, pricing, or refines a previous search.
        Even for vague queries like "Ich suche eine Behandlung" — call this first,
        then ask clarifying questions.

        Args:
            query: The user's search query
            category: Determines which category of treatments to display in the frontend.
                      Choose the MOST SUITABLE category based on what the user is asking about:

                      - "treatments": Use when user asks about facial treatments (Gesichtsbehandlung),
                        body treatments (Koerperbehandlung), pedicure (Fusspflege), manicure (Manikuere),
                        skincare, anti-aging, hydration, peeling, or mentions Brigitte Kettner.

                      - "permanent_makeup": Use when user asks about permanent makeup (Permanent Make-Up),
                        eyebrow pigmentation (Augenbrauen), lip pigmentation (Lippen), eyeliner,
                        or micropigmentation.

                      - "wellness": Use when user asks about massage (Massage, Ganzkoerpermassage,
                        Entspannungsmassage), relaxation, or Forma Radiofrequenz (RF technology,
                        skin tightening, collagen stimulation).

                      If unsure which category fits best, default to "treatments" as it is our main
                      service area.

            mentioned_treatments: IMPORTANT — Extract specific treatment names from the user's message.
                                  Examples: "Gesichtsbehandlung" -> ["Gesichtsbehandlung"],
                                  "Permanent Make-Up Lippen" -> ["Permanent Make-Up Lippen"],
                                  "Forma" -> ["Forma Radiofrequenz"].
                                  These treatments will be prioritized and shown first in the frontend.
        """
        if mentioned_treatments is None:
            mentioned_treatments = []
        try:
            logger.info(
                f"search_treatments: category={category}, "
                f"mentioned={mentioned_treatments}, query={query!r}"
            )
            return await self._search_treatments_inner(query, category, mentioned_treatments)
        except Exception as e:
            logger.error(f"search_treatments failed: {e}")
            return (
                AGENT_MESSAGES.get(
                    "search_unavailable",
                    "Es tut mir leid, ich kann gerade nicht auf die Behandlungsinformationen "
                    "zugreifen. Bitte versuchen Sie es erneut.",
                )
                + "\n"
                + CONVERSATION_RULES
            )

    async def _search_treatments_inner(
        self,
        query: str,
        category: str = "treatments",
        mentioned_treatments: list[str] = None,
    ) -> str:
        """Core search logic — loads data, sends to frontend, returns LLM context."""
        if mentioned_treatments is None:
            mentioned_treatments = []

        # Validate category
        valid_categories = ["treatments", "permanent_makeup", "wellness"]
        if category not in valid_categories:
            logger.warning(f"Invalid category '{category}', defaulting to 'treatments'")
            category = "treatments"

        # Get conversation history
        history = self._chat_ctx.items
        cleaned_history = normalize_messages(history)

        if cleaned_history and cleaned_history[-1]["role"] != "user":
            return AGENT_MESSAGES.get("wait_for_customer", "Warte auf Kundennachricht.")

        # Update search counter
        self.userdata.search_count += 1

        user_messages = [
            chat["message"] for chat in cleaned_history if chat["role"] == "user"
        ]
        last_user_msg = user_messages[-1] if user_messages else ""

        # Get treatments from the selected category (for frontend display)
        frontend_products = data_loader.get_products_by_category(
            category=category,
            query=last_user_msg,
            mentioned_products=mentioned_treatments,
            min_results=5,
        )

        # Get LLM-optimized context from pre-built markdown files
        if category == "wellness":
            products_text = ""
            use_cases_text = self._get_llm_context("wellness")
        else:
            products_text = self._get_llm_context(category)
            use_cases_text = ""

        # Send treatments to frontend via "products" topic
        try:
            frontend_payload = []
            for item in frontend_products[:5]:
                frontend_item = data_loader.get_frontend_product(item)
                if "duration_min" in item:
                    frontend_item["duration"] = item["duration_min"]
                frontend_payload.append(frontend_item)

            logger.info(
                f"Frontend treatments (category={category}): "
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
            logger.error(f"Failed to send treatments to frontend: {e}")

        # Build LLM context
        context_parts = [
            f"USER QUERY: {last_user_msg}",
            f"SEARCH NUMBER: {self.userdata.search_count}",
            "",
            "=== RELEVANT TREATMENT DATA ===",
            products_text,
            f"Also explain shortly about these treatments and their relation with user query: "
            f"{[p['product_name'] for p in frontend_payload]}",
        ]

        if use_cases_text:
            context_parts.extend([
                "",
                "=== RELEVANT WELLNESS DATA ===",
                use_cases_text,
            ])

        # Store results in userdata
        self.userdata.last_search_results = frontend_products[:5]

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
                "Kein Problem! Ich helfe Ihnen gerne weiter mit Ihren Fragen "
                "zu unseren Behandlungen."
            )

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
        if name:
            self.userdata.name = name.strip().title()
            logger.info(f"Saved name: {self.userdata.name}")
        if email:
            if is_valid_email_syntax(email.strip()):
                self.userdata.email = email.strip().lower()
                logger.info(f"Saved email: {self.userdata.email}")
            else:
                return "Die E-Mail-Adresse scheint nicht gueltig zu sein. Bitte fragen Sie erneut."
        if phone:
            self.userdata.phone = phone.strip()
            logger.info(f"Saved phone: {self.userdata.phone}")
        if preferred_contact and preferred_contact in ("phone", "whatsapp", "email"):
            self.userdata.preferred_contact = preferred_contact
            logger.info(f"Saved preferred contact: {preferred_contact}")

    # ══════════════════════════════════════════════════════════════════════════
    # FUNCTION TOOL 6 — RECORD CONSENT
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

    # ══════════════════════════════════════════════════════════════════════════
    # FUNCTION TOOL 9 — COMPLETE CONTACT COLLECTION
    # ══════════════════════════════════════════════════════════════════════════

    @function_tool
    async def complete_contact_collection(self, context: RunContext_T):
        """
        Call this when you have collected sufficient contact information and consent.
        This validates the data and hands off to the completion agent for email sending.

        Requirements: name + (email or phone) + consent_given = True
        """
        missing = []
        if not self.userdata.name:
            missing.append("Name")
        if not self.userdata.email and not self.userdata.phone:
            missing.append("E-Mail oder Telefon")
        if not self.userdata.consent_given:
            missing.append("Einwilligung zur Kontaktaufnahme")

        if missing:
            return f"Noch fehlend: {', '.join(missing)}. Bitte fragen Sie die Kundin danach."

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
