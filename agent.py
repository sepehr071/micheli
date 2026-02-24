"""
Entry point for the LiveKit voice agent.
Connects the agent framework and session management.

All business logic lives in agents/, core/, config/, prompt/, and utils/.
This file only handles startup and shutdown.
"""

from livekit import agents
from livekit.agents import AgentSession, RoomInputOptions
from core.session_state import UserData
from agents.main_agent import BeautyLoungeAssistant
from utils.history import save_conversation_to_file, normalize_messages
from utils.webhook import send_session_webhook
import logging
import os
import re
from datetime import datetime
from config.settings import LOGS_DIR
from utils.translate_online import translate_transcribed_text

# ══════════════════════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════════════════════

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(LOGS_DIR, f"app_{timestamp}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

for noisy in ["httpx", "httpcore", "openai", "livekit.agents", "urllib3", "asyncio", "livekit"]:
    logging.getLogger(noisy).setLevel(logging.WARNING)


# ══════════════════════════════════════════════════════════════════════════════
# TRANSCRIPT EMAIL EXTRACTION (safety net for sudden session close)
# ══════════════════════════════════════════════════════════════════════════════

_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')


def _extract_contact_from_transcript(chat_messages, userdata) -> None:
    """Extract email from transcript if not already stored in userdata.

    Safety net for sudden session close — the visitor may have said their
    email but the LLM hadn't yet called the contact collection tool.
    """
    if userdata.email:
        return

    for msg in normalize_messages(chat_messages):
        if msg["role"] != "user":
            continue
        match = _EMAIL_RE.search(msg["message"])
        if match:
            userdata.email = match.group(0).lower()
            logger.info(f"Extracted email from transcript on shutdown: {userdata.email}")
            break


# ══════════════════════════════════════════════════════════════════════════════
# ENTRYPOINT
# ══════════════════════════════════════════════════════════════════════════════


async def entrypoint(ctx: agents.JobContext):
    userData = UserData()
    session = AgentSession[UserData](userdata=userData)
    start_time = datetime.now()

    async def on_shutdown():
        try:
            ud = session.userdata
            if ud and not ud._history_saved:
                # Get complete conversation across all agents
                chat_history = list(session.history.items)

                # Safety net: extract email from transcript if not yet stored
                _extract_contact_from_transcript(chat_history, ud)

                # Save local history file
                save_conversation_to_file(chat_history, ud, start_time)

                # Send webhook (async, non-blocking)
                session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                await send_session_webhook(session_id, chat_history, ud, start_time)

                ud._history_saved = True
                logger.info("Conversation saved and webhook sent on session shutdown")
        except Exception as e:
            logger.error(f"Failed to save conversation on shutdown: {e}")

    ctx.add_shutdown_callback(on_shutdown)

    session.on("user_input_transcribed", translate_transcribed_text)

    try:
        await session.start(
            room=ctx.room,
            agent=BeautyLoungeAssistant(room=ctx.room, userdata=userData, first_message=True),
            room_input_options=RoomInputOptions(),
        )
    except Exception as e:
        logger.critical(f"Session start failed: {e}")
        try:
            await ctx.room.local_participant.send_text(
                '{"agent_response": "Sorry, there was a technical problem. Please try again."}',
                topic="message",
            )
        except Exception:
            pass
        return

    try:
        await ctx.connect()
    except Exception as e:
        logger.critical(f"Room connect failed: {e}")


if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint),
    )
