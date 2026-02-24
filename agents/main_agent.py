"""
Main conversational agent (BeautyLoungeAssistant) — handles treatment search, buying signals,
expert offers, and budget tracking. Uses local data files instead of RAG service.

Used by: agent.py (entrypoint), agents/email_agents.py (LastAgent restart)
"""

import json
import asyncio
import logging
from typing import AsyncIterable, Optional, List, Dict, Any
from livekit.agents import function_tool, ModelSettings , Agent
from livekit.rtc import DataPacket
from agents.base import safe_generate_reply, create_realtime_model

from core.session_state import UserData, RunContext_T
from core.lead_scoring import detect_buying_signals
from core.response_builder import (
    build_lead_instruction,
    build_expert_question_instruction,
    build_search_response,
    BudgetTracker,
)
from config.messages import AGENT_MESSAGES, UI_BUTTONS, CONVERSATION_RULES
from config.settings import LLM_TEMPERATURE_WORKFLOW
from config.language import handle_language_update, language_manager, get_language_instruction, get_language_prefix
from prompt.static_main_agent import BEAUTY_LOUNGE_PROMPT, BEAUTY_LOUNGE_GREETING
from utils.filter_extraction import get_greeting
from utils.history import normalize_messages
from utils.message_classifier import MessageClassifier, MessageCategory, ClassificationResult
from utils.data_loader import data_loader, DataClassifier, DataCategory
import prompt.static_workflow as prompts

logger = logging.getLogger(__name__)


# =============================================================================
# MAIN AGENT - BeautyLoungeAssistant
# =============================================================================

class BeautyLoungeAssistant(Agent):
    def __init__(self, room, userdata: UserData | None = None, first_message: bool = False) -> None:
        if userdata:
            self.userdata = userdata
        self.first_message = first_message
        self.room = room
        self.classifier = MessageClassifier()
        self.data_classifier = DataClassifier()
        self.pending_classification: ClassificationResult | None = None
        self.budget_tracker = BudgetTracker()
        self._original_instructions = BEAUTY_LOUNGE_PROMPT

        # Register data received callback for language updates
        self._setup_data_listener()

        llm_model = create_realtime_model()

        # Include language prefix and suffix for maximum emphasis
        instructions_with_language = get_language_prefix() + BEAUTY_LOUNGE_PROMPT + get_language_instruction()

        super().__init__(
            llm=llm_model,
            instructions=instructions_with_language,
        )

    def _setup_data_listener(self) -> None:
        """Set up listener for incoming data from frontend (e.g., language changes)."""
        @self.room.on("data_received")
        def on_data_received(data: DataPacket):
            asyncio.create_task(self._handle_data_received(data))

    async def _handle_data_received(self, data: DataPacket) -> None:
        """Handle incoming data packets from frontend."""
        try:
            # Decode the data payload
            payload = data.data.decode("utf-8") if isinstance(data.data, bytes) else data.data
            parsed = json.loads(payload)

            # Check if this is a language update (topic: "language")
            if data.topic == "language":
                logger.info(f"Received language update: {parsed}")
                if handle_language_update(parsed):
                    new_lang = language_manager.get_language()
                    logger.info(f"Language successfully changed to: {new_lang}")
                    # Update agent instructions with new language
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
            # Preserve the current chat context before updating
            current_chat_ctx = self._chat_ctx

            instructions = self._original_instructions
            # Update with fresh language instruction
            new_instructions = get_language_prefix() + instructions + get_language_instruction()

            # Update instructions while preserving chat context
            self._instructions = new_instructions
            if hasattr(self, '_activity') and self._activity:
                await self._activity.update_instructions(new_instructions)

            # Ensure chat context is restored
            if current_chat_ctx:
                self._chat_ctx = current_chat_ctx

            logger.info(f"Agent instructions updated for language: {language_manager.get_language()}")
        except Exception as e:
            logger.error(f"Failed to update agent instructions: {e}")

    async def on_enter(self):
        logger.info(f"BeautyLoungeAssistant on_enter (first_message={self.first_message}, searches={self.userdata.ret_count})")

        if self.first_message:
            try:
                greeting_prefix = get_greeting()
                await self._generate_reply_tracked(
                    BEAUTY_LOUNGE_GREETING.format(greeting_prefix=greeting_prefix),
                    context="greeting",
                )
            except Exception as e:
                logger.error(f"BeautyLoungeAssistant greeting failed: {e}")
        else:
            try:
                return await super().on_enter()
            except Exception as e:
                logger.error(f"BeautyLoungeAssistant on_enter failed: {e}")

    # ══════════════════════════════════════════════════════════════════════════════
    # BUDGET TRACKING — delegates to BudgetTracker
    # ══════════════════════════════════════════════════════════════════════════════

    async def _safe_reply(self, instructions: str) -> bool:
        """Convenience wrapper — calls safe_generate_reply with language injection."""
        # Inject current language instruction
        instructions = get_language_prefix() + instructions + get_language_instruction()
        return await safe_generate_reply(self.session, self.room, instructions)

    async def _generate_reply_tracked(self, instructions: str, context: str = None):
        """Generate reply with response tracking and smart budget injection."""
        self.userdata.response_count += 1
        bt = self.budget_tracker

        # Reply without budget tracking (B2C context)
        await self._safe_reply(instructions)

    # ══════════════════════════════════════════════════════════════════════════════
    # TREATMENT DATA RETRIEVAL — Uses local data files
    # ══════════════════════════════════════════════════════════════════════════════

    def _get_relevant_data(self, categories: List[str]) -> Dict[str, Any]:
        """
        Get relevant data based on classified categories.

        Returns a dictionary with data for each requested category.
        Note: FAQ and general_info are now in the static prompt, not retrieved dynamically.
        """
        result = {
            "products": [],
            "use_cases": [],
        }

        # If ALL category is requested, get everything
        if DataCategory.ALL in categories:
            result["products"] = data_loader.load_treatments() + data_loader.load_permanent_makeup()
            result["use_cases"] = data_loader.load_wellness()
            return result

        # Get specific categories
        if DataCategory.TREATMENTS in categories:
            result["products"].extend(data_loader.load_treatments())

        if DataCategory.PERMANENT_MAKEUP in categories:
            result["products"].extend(data_loader.load_permanent_makeup())

        if DataCategory.WELLNESS in categories:
            result["use_cases"] = data_loader.load_wellness()

        # If no products but general search, return treatments as default
        if not result["products"] and not result["use_cases"]:
            result["products"] = data_loader.load_treatments()

        return result

    def _format_products_for_llm(self, products: List[Dict[str, Any]], max_products: int = 5) -> str:
        """Format treatment data for LLM context - uses LLM context files."""
        if not products:
            return "Keine passenden Behandlungen gefunden."

        formatted = []
        for i, product in enumerate(products[:max_products]):
            name = product.get("name", "Unbekannte Behandlung")
            url = product.get("url", "")

            # Build treatment description
            desc_parts = [f"**{name}**"]

            if "Introduction" in product:
                desc_parts.append(f"Beschreibung: {product['Introduction']}")

            if "Features" in product:
                desc_parts.append(f"Details: {product['Features']}")

            if "Benefits to Clients" in product:
                desc_parts.append(f"Vorteile: {product['Benefits to Clients']}")

            # Treatment-specific fields
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

    def _format_use_cases_for_llm(self, use_cases: List[Dict[str, Any]], max_cases: int = 3) -> str:
        """Format wellness data for LLM context."""
        if not use_cases:
            return ""

        formatted = []
        for i, case in enumerate(use_cases[:max_cases]):
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

    @function_tool()
    async def _retrieve_products(self, context: RunContext_T, query: str, category: str, mentioned_products: list[str] = None):
        """
        MUST be called for ANY treatment-related query before responding.
        Call this when user asks about: treatments, services, skincare, permanent makeup, massage, pricing, or refines a previous search.
        Even for vague queries like "Ich suche eine Behandlung" - call this first, then ask clarifying questions.

        Args:
            query: The user's search query
            category: Determines which category of treatments to display in the frontend.
                      Choose the MOST SUITABLE category based on what the user is asking about:

                      - "treatments": Use when user asks about facial treatments (Gesichtsbehandlung),
                        body treatments (Körperbehandlung), pedicure (Fußpflege), manicure (Maniküre),
                        skincare, anti-aging, hydration, peeling, or mentions Brigitte Kettner.

                      - "permanent_makeup": Use when user asks about permanent makeup (Permanent Make-Up),
                        eyebrow pigmentation (Augenbrauen), lip pigmentation (Lippen), eyeliner,
                        or micropigmentation.

                      - "wellness": Use when user asks about massage (Massage, Ganzkörpermassage,
                        Entspannungsmassage), relaxation, or Forma Radiofrequenz (RF technology,
                        skin tightening, collagen stimulation).

                      If unsure which category fits best, default to "treatments" as it's our main service area.

            mentioned_products: IMPORTANT - Extract specific treatment names from the user's message.
                                Examples: "Gesichtsbehandlung" → ["Gesichtsbehandlung"],
                                "Permanent Make-Up Lippen" → ["Permanent Make-Up Lippen"],
                                "Forma" → ["Forma Radiofrequenz"].
                                These treatments will be prioritized and shown first in the frontend.
        """
        if mentioned_products is None:
            mentioned_products = []
        try:
            logger.info(f"\n\nCategory: {category} , Mentioned Treatments: {mentioned_products}\n\n")
            return await self._retrieve_products_inner(query, category, mentioned_products)
        except Exception as e:
            logger.error(f"_retrieve_products total failure: {e}")
            return AGENT_MESSAGES.get("search_unavailable", "Es tut mir leid, ich kann gerade nicht auf die Behandlungsinformationen zugreifen. Bitte versuchen Sie es erneut.") + "\n" + CONVERSATION_RULES

    async def _retrieve_products_inner(self, query: str, category: str = "treatments", mentioned_products: list[str] = None):
        """Inner search logic — called by the guarded _retrieve_products."""
        if mentioned_products is None:
            mentioned_products = []

        # Validate category, default to treatments if invalid
        valid_categories = ["treatments", "permanent_makeup", "wellness"]
        if category not in valid_categories:
            logger.warning(f"Invalid category '{category}', defaulting to 'treatments'")
            category = "treatments"

        # 1. Get conversation history
        history = self._chat_ctx.items
        cleaned_history = normalize_messages(history)

        if cleaned_history and cleaned_history[-1]["role"] != "user":
            return AGENT_MESSAGES.get("wait_for_customer", "Warte auf Kundennachricht.")

        # 2. Update counters
        self.userdata.ret_count += 1
        self.userdata.response_count += 1

        user_messages = [
            chat["message"]
            for chat in cleaned_history
            if chat["role"] == "user"
        ]
        last_user_msg = user_messages[-1] if user_messages else ""

        # 3. Classify message for data categories
        data_categories = self.data_classifier.classify(last_user_msg)
        logger.info(f"Data categories for query: {data_categories}")

        # 4. Classify message type
        if not self.pending_classification:
            self.pending_classification = self.classifier.classify(last_user_msg, cleaned_history)
        classification = self.pending_classification

        # Handle typo correction
        if classification.category == MessageCategory.TYPO_QUERY and classification.corrected_query:
            current_message = classification.corrected_query
        else:
            current_message = last_user_msg

        # 5. Detect buying signals
        buying_signals = detect_buying_signals(last_user_msg, self.userdata.ret_count)
        self.userdata.current_signal_level = buying_signals["level"]
        self.userdata.last_hot_count = buying_signals["hot_signals"]
        self.userdata.last_warm_count = buying_signals["warm_signals"]
        self.userdata.last_cool_count = buying_signals["cool_signals"]
        self.userdata.last_confidence = buying_signals["confidence"]

        # 6. Get treatments from the selected category (for both LLM and frontend)
        frontend_products = data_loader.get_products_by_category(
            category=category,
            query=last_user_msg,
            mentioned_products=mentioned_products,
            min_results=5
        )

        # 7. Format data for LLM based on selected category only - use LLM context files
        if category == "wellness":
            products_text = ""
            use_cases_text = self._get_llm_context("wellness")
        else:
            products_text = self._get_llm_context(category)
            use_cases_text = ""

        # 8. Send treatments to frontend (only from selected category)
        try:
            frontend_payload = []
            for item in frontend_products[:5]:
                frontend_item = data_loader.get_frontend_product(item)
                # Add duration for treatments that have it
                if "duration_min" in item:
                    frontend_item["duration"] = item["duration_min"]
                frontend_payload.append(frontend_item)

            logger.info(f"Frontend treatments (category={category}): {[p['product_name'] for p in frontend_payload]}")

            if frontend_payload:
                asyncio.create_task(
                    self.room.local_participant.send_text(
                        json.dumps(frontend_payload),
                        topic="products",
                    )
                )
        except Exception as e:
            logger.error(f"Failed to send treatments to frontend: {e}")

        # 9. Build LLM instructions
        signal_level = buying_signals.get("level", "MILD")

        # Determine if we should offer expert consultation
        offer_expert = (
            self.userdata.ret_count >= 2
            and signal_level in ["HOT", "WARM"]
            and not self.userdata.expert_accepted
        )

        if offer_expert:
            self.userdata.pending_expert_buttons = True
            self.userdata.expert_offer_count += 1
            logger.info(f"Expert offer flagged (signal={signal_level}, search=#{self.userdata.ret_count})")

        # Build context for LLM
        context_parts = [
            f"USER QUERY: {last_user_msg}",
            f"SEARCH NUMBER: {self.userdata.ret_count}",
            f"SIGNAL LEVEL: {signal_level}",
            "",
            "=== RELEVANT TREATMENT DATA ===",
            products_text,
            f"Also explain shortly about these treatments and their relation with user query: {[p['product_name'] for p in frontend_payload]}"
        ]

        if use_cases_text:
            context_parts.extend([
                "",
                "=== RELEVANT WELLNESS DATA ===",
                use_cases_text,
            ])

        # Add lead instruction
        expert_phrase = ""
        if offer_expert:
            expert_phrase = "Basierend auf dem Interesse der Kundin, bieten Sie an, sie mit unserer Kosmetikerin zu verbinden, die detailliertere Informationen und Preise geben kann."

        lead_instruction = build_lead_instruction(
            signal_level=signal_level,
            can_offer_expert=offer_expert,
            expert_phrase=expert_phrase,
            expert_accepted=self.userdata.expert_accepted,
        )
        context_parts.extend(["", "=== INSTRUCTIONS ===", lead_instruction])

        # Add classification info
        classification_info = f"Message Category: {classification.category.value}"
        if classification.corrected_query:
            classification_info += f" (typo corrected: {classification.corrected_query})"
        context_parts.extend(["", classification_info])

        # Clear pending classification
        self.pending_classification = None

        # Update userdata with frontend treatments
        self.userdata.ret_car = frontend_products[:5]  # Legacy field name, holds treatment results
        self.userdata.summary_context = cleaned_history

        return get_language_prefix() + "\n".join(context_parts) + get_language_instruction()

    # ══════════════════════════════════════════════════════════════════════════════
    # CONVERSATION SUMMARY
    # ══════════════════════════════════════════════════════════════════════════════

    @function_tool
    async def save_conversation_summary(self, context: RunContext_T, summary: str):
        """
        Call this to save a brief summary of the conversation before offering expert connection or ending.
        summary (required): A 1-2 sentence summary of what the customer discussed and their interest level.
        """
        logger.info(f"Conversation summary: {summary}")
        self.userdata.conversation_summary = summary.strip()

    # ══════════════════════════════════════════════════════════════════════════════
    # EXPERT CONNECTION
    # ══════════════════════════════════════════════════════════════════════════════

    @function_tool
    async def connect_to_expert(self, context: RunContext_T, confirm: bool):
        """
        IMPORTANT: Call this function when the user responds to Yes/No buttons!

        When Yes/No buttons are displayed and the user responds:
        - "Yes", "yes", "yeah", "sure", "ok", "Ja", "ja" → confirm = True
        - "No", "no", "nope", "not interested", "Nein", "nein" → confirm = False

        confirm = True → User clicked "Yes" (wants consultation contact)
        confirm = False → User clicked "No" (declines)

        This function MUST be called when the user responds to the expert offer!
        """
        logger.info(f"connect_to_expert: confirm={confirm}, signal={self.userdata.current_signal_level}")

        if confirm:
            self.userdata.expert_accepted = True
            # No need to save history to userdata - session.history already tracks everything
            from agents.qualification_agents import PurchaseTimingAgent
            return PurchaseTimingAgent(
                instructions=prompts.PurchaseTimingPrompt,
                room=self.room,
                chat_ctx=None,
                userdata=self.userdata,
                add_instruction=False,
                temperature=LLM_TEMPERATURE_WORKFLOW,
            )
        else:
            self.userdata.expert_accepted = False
            await self._safe_reply(AGENT_MESSAGES.get("expert_decline", "Kein Problem! Lassen Sie mich wissen, wenn Sie weitere Fragen haben."))

    # ══════════════════════════════════════════════════════════════════════════════
    # TRANSCRIPTION — streams text + sends expert buttons after LLM speaks
    # ══════════════════════════════════════════════════════════════════════════════

    async def transcription_node(self, text: AsyncIterable[str], model_settings: ModelSettings) -> AsyncIterable[str]:
        agent_response = ""
        async for delta in text:
            agent_response += delta
            yield delta

        # Send message to frontend
        try:
            await self.room.local_participant.send_text(
                json.dumps({"agent_response": agent_response}),
                topic="message",
            )
        except Exception as e:
            logger.error(f"Failed to send transcription: {e}")

        # Send expert Yes/No buttons AFTER message if flagged
        if self.userdata.pending_expert_buttons:
            try:
                await self.room.local_participant.send_text(
                    json.dumps(UI_BUTTONS.get("expert_offer", {"Yes": "Yes", "No": "No"})),
                    topic="trigger",
                )
            except Exception as e:
                logger.error(f"Failed to send expert buttons: {e}")
            self.userdata.pending_expert_buttons = False


    async def update_instructions(self, instructions: str) -> None:
        """
        Updates the agent's instructions.

        If the agent is running in realtime mode, this method also updates
        the instructions for the ongoing realtime session.

        Args:
            instructions (str):
                The new instructions to set for the agent.

        Raises:
            llm.RealtimeError: If updating the realtime session instructions fails.
        """
        # Preserve the current chat context before updating
        current_chat_ctx = self._chat_ctx

        self._instructions = instructions

        if hasattr(self, '_activity') and self._activity:
            await self._activity.update_instructions(instructions)

        # Ensure chat context is restored
        if current_chat_ctx:
            self._chat_ctx = current_chat_ctx


# Backward compatibility aliases
HanshowAssistant = BeautyLoungeAssistant
BertaAssistant = BeautyLoungeAssistant
