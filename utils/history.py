"""
Conversation history — save transcripts to local text files.

Webhook sending has moved to utils/webhook.py.
"""

import json
import os
import logging
from datetime import datetime
from config.settings import SAVE_CONVERSATION_HISTORY
from config.messages import HISTORY_FORMAT

logger = logging.getLogger(__name__)

HISTORY_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "history"
)


def normalize_messages(chat_messages):
    """
    Converts ChatMessage objects into a standardized dictionary format:
    { role: "...", message: "..." }

    - User messages containing JSON strings will be parsed.
    - Assistant messages are flattened into a single string.
    - Skips non-ChatMessage items like FunctionCall.
    """
    normalized = []

    for msg in chat_messages:
        # Skip if not a ChatMessage (e.g., FunctionCall)
        if not hasattr(msg, 'role'):
            continue

        role = msg.role

        # Extract raw content (list of strings)
        if isinstance(msg.content, list) and msg.content:
            raw = " ".join(msg.content)
        else:
            raw = str(msg.content)

        # If user message contains a JSON string, parse it
        if role == "user":
            try:
                parsed = json.loads(raw)
                message_text = parsed.get("message", raw)
            except Exception:
                message_text = raw
        else:
            message_text = raw

        normalized.append({
            "role": role,
            "message": message_text
        })

    return normalized


def save_conversation_to_file(chat_messages, userdata, start_time=None):
    """
    Save a complete conversation to a .txt file in the history/ folder.

    Args:
        chat_messages: Raw chat message objects from session.history.items
        userdata: UserData instance with products, contact info, and qualification data
        start_time: datetime when the conversation started (unused, kept for compat)
    """
    if not SAVE_CONVERSATION_HISTORY:
        return

    conversation = normalize_messages(chat_messages)

    # Guard: don't save empty conversations
    if not conversation:
        logger.info("No conversation to save (empty session)")
        return

    os.makedirs(HISTORY_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    txt_filename = f"conversation_{timestamp}.txt"
    txt_filepath = os.path.join(HISTORY_DIR, txt_filename)

    try:
        lines = []
        lines.append("=" * 50)
        lines.append(HISTORY_FORMAT["header"])
        lines.append(f"Date: {datetime.now().strftime(HISTORY_FORMAT['date_format'])}")
        lines.append("=" * 50)
        lines.append("")
        lines.append(HISTORY_FORMAT["transcript_header"])
        lines.append("")

        # Build a map: user_msg_count -> list of search results to insert after that user message
        product_map = {}  # {after_user_msg: [(search_number, products), ...]}
        all_products = getattr(userdata, 'all_retrieved_products', []) or []
        for search_idx, entry in enumerate(all_products):
            msg_count = entry.get("after_user_msg", 0)
            products = entry.get("products", [])
            if products:
                product_map.setdefault(msg_count, []).append((search_idx + 1, products))

        # Write transcript with products inserted inline at the correct position
        user_msg_count = 0
        for msg in conversation:
            role = msg["role"]
            text = msg["message"].strip()
            if not text:
                continue

            if role == "user":
                user_msg_count += 1
                lines.append(f"{HISTORY_FORMAT['user_label']} {text}")
                # Insert products that were retrieved after this user message
                if user_msg_count in product_map:
                    for search_num, products in product_map[user_msg_count]:
                        lines.append("")
                        lines.append(f"  [{HISTORY_FORMAT['search_line'].format(search_num=search_num, count=len(products))}]")
                        for i, car in enumerate(products, 1):
                            name = car.get("product_name", "Unknown")
                            price = car.get("price", "N/A")
                            mileage = car.get("mileage", "N/A")
                            lines.append(f"  {HISTORY_FORMAT['product_line'].format(i=i, name=name, price=price, mileage=mileage)}")
                        lines.append("")
            else:
                lines.append(f"{HISTORY_FORMAT['agent_label']} {text}")

        # Contact info section
        has_contact = any([
            userdata.name, userdata.email, userdata.phone,
            userdata.schedule_date, userdata.schedule_time,
        ])

        if has_contact:
            cl = HISTORY_FORMAT["contact_labels"]
            ev = HISTORY_FORMAT["empty_value"]
            lines.append("")
            lines.append(HISTORY_FORMAT["contact_header"])
            lines.append("")
            lines.append(f"{cl['name']} {userdata.name or ev}")
            lines.append(f"{cl['email']} {userdata.email or ev}")
            lines.append(f"{cl['phone']} {userdata.phone or ev}")
            lines.append(
                f"{cl['schedule']} {userdata.schedule_date or ev}"
                f"{cl['schedule_time_sep'] + userdata.schedule_time if userdata.schedule_time else ''}"
            )
            lines.append(f"Preferred Contact: {userdata.preferred_contact or ev}")
            lines.append(f"Lead Score: {userdata.lead_score}/10 ({userdata.lead_level})")
            lines.append(f"Consent: {'Yes' if userdata.consent_given else 'No'}")

        # AI summary section (if agent generated one)
        if userdata.conversation_summary:
            lines.append("")
            lines.append("-" * 50)
            lines.append("AI Summary:")
            lines.append(userdata.conversation_summary)

        lines.append("")
        lines.append("=" * 50)

        with open(txt_filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"Conversation saved to {txt_filepath}")

    except Exception as e:
        logger.error(f"Failed to save conversation history (txt): {e}")
