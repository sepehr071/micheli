"""
Base agent — shared init and transcription for all sub-agents.
Configures the LLM, injects base prompt, and streams text to frontend.

Used by: all agent subclasses in agents/
"""

import json
import asyncio
import time
import logging
from typing import AsyncIterable
from livekit.agents import Agent, ModelSettings, function_tool
from livekit.rtc import DataPacket
from livekit.plugins import openai
from core.session_state import UserData, RunContext_T
from config.settings import RT_MODEL, LLM_TEMPERATURE
from config.messages import AGENT_MESSAGES
from config.language import get_language_instruction, get_language_prefix, handle_language_update, language_manager
import prompt.static_workflow as prompts

logger = logging.getLogger(__name__)

REPLY_MAX_RETRIES = 3
REPLY_BACKOFF = 1.0
MODEL_MAX_RETRIES = 3
MODEL_BACKOFF = 2.0


async def safe_generate_reply(session, room, instructions: str, retries: int = REPLY_MAX_RETRIES) -> bool:
    """Retry session.generate_reply up to `retries` times with backoff.
    On total failure, sends a polite 'patience' text to the frontend so the user
    never experiences silence or an error — just a brief 'one moment please'.
    Returns True on success, False on total failure.
    """
    for attempt in range(retries):
        try:
            await session.generate_reply(instructions=instructions)
            return True
        except Exception as e:
            logger.warning(f"generate_reply attempt {attempt + 1}/{retries} failed: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(REPLY_BACKOFF * (attempt + 1))

    # All retries exhausted — send text fallback so user sees something
    logger.error(f"generate_reply failed after {retries} attempts")
    try:
        await room.local_participant.send_text(
            json.dumps({"agent_response": AGENT_MESSAGES["patience_fallback"]}),
            topic="message",
        )
    except Exception:
        pass
    return False


def create_realtime_model(model=None, retries: int = MODEL_MAX_RETRIES, temperature=None):
    """Create OpenAI RealtimeModel with retry. Re-raises on total failure."""
    for attempt in range(retries):
        try:
            return openai.realtime.RealtimeModel(
                model=model or RT_MODEL,
                temperature=temperature if temperature is not None else LLM_TEMPERATURE,
            )
        except Exception as e:
            logger.warning(f"RealtimeModel init attempt {attempt + 1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(MODEL_BACKOFF * (attempt + 1))
            else:
                logger.critical(f"RealtimeModel init failed after {retries} attempts")
                raise


class BaseAgent(Agent):
    def __init__(
        self,
        instructions: str,
        room,
        userdata: UserData | None = None,
        chat_ctx=None,
        add_instruction: bool = True,
        model=None,
        temperature: float | None = None,
    ) -> None:
        logger.info("Initializing BaseAgent")
        if userdata:
            self.userdata = userdata
        self.room = room
        self._add_instruction = add_instruction
        self._original_instructions = instructions  # Store for language updates

        # Set up data listener for language updates
        self._setup_data_listener()

        if add_instruction:
            instructions = prompts.BaseAgentPrompt.format(user_info=str(self.userdata)) + "\n" + instructions

        # Add language prefix and suffix for maximum emphasis
        instructions = get_language_prefix() + instructions + get_language_instruction()

        llm_model = create_realtime_model(model, temperature=temperature)

        super().__init__(
            llm=llm_model,
            instructions=instructions,
            chat_ctx=chat_ctx,
        )
        logger.info("BaseAgent initialized successfully")

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
            if self._add_instruction:
                instructions = prompts.BaseAgentPrompt.format(user_info=str(self.userdata)) + "\n" + instructions
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

    async def _safe_reply(self, instructions: str) -> bool:
        """Convenience wrapper — calls safe_generate_reply with language injection."""
        # Inject current language instruction
        instructions = get_language_prefix() + instructions + get_language_instruction()
        return await safe_generate_reply(self.session, self.room, instructions)

    @function_tool
    async def save_conversation_summary(self, context: RunContext_T, summary: str):
        """
        Call this to save a brief summary of the conversation before ending or handing off.
        summary (required): A 1-2 sentence summary of what the customer discussed and their interest level.
        """
        logger.info(f"Conversation summary (BaseAgent): {summary}")
        self.userdata.conversation_summary = summary.strip()

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
            logger.error(f"Failed to send transcription to frontend: {e}")

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