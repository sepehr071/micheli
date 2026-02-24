# utils.py
# Utility functions for filter extraction, email validation, and helpers

import json
import os
import re
import time
import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from prompt.static_extraction import SINGLE_EXTRACTION_PROMPT
from config.company import COMPANY
from config.settings import LLM_MODEL, LLM_TEMPERATURE, OPENROUTER_BASE_URL
import pytz
from datetime import datetime 

logger = logging.getLogger(__name__)

load_dotenv()

llm = ChatOpenAI(
    model=LLM_MODEL,
    temperature=LLM_TEMPERATURE,
    openai_api_base=OPENROUTER_BASE_URL,
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
)


def is_valid_email_syntax(s: str) -> bool:
    EMAIL_RE = re.compile(
                r"^(?=.{1,254}$)(?=.{1,64}@)"
                r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
                r"@"
                r"(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}$"
            )
    return EMAIL_RE.match(s) is not None


def extract_filters_direct(current_message: str, current_preferences: Dict) -> Dict:
    """
    Single LLM call to extract filters from current message.

    Args:
        current_message: The user's latest message
        current_preferences: Current filter state as dict (can be empty)

    Returns:
        Dict with extracted filter changes (not full state)
    """
    import json as json_module

    # Format the prompt with current context
    prompt = SINGLE_EXTRACTION_PROMPT.replace(
        "{current_message}", current_message
    ).replace(
        "{current_preferences}", json_module.dumps(current_preferences, ensure_ascii=False)
    )

    # LLM call with retry
    content = None
    for attempt in range(3):
        try:
            response = llm.invoke(prompt)
            content = response.content.strip()
            break
        except Exception as e:
            logger.warning(f"[FILTER EXTRACTION] LLM attempt {attempt + 1}/3 failed: {e}")
            if attempt < 2:
                time.sleep(1 * (attempt + 1))

    if content is None:
        logger.error("[FILTER EXTRACTION] LLM call failed after 3 attempts")
        return {}

    # Clean up response (remove markdown if present)
    if content.startswith("```"):
        lines = content.split("\n")
        # Remove first and last line if they're code fences
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines)

    # Parse JSON
    try:
        extracted = json_module.loads(content)
    except json_module.JSONDecodeError as e:
        print(f"[FILTER EXTRACTION] JSON parse error: {e}")
        print(f"[FILTER EXTRACTION] Raw content: {content[:200]}")
        # Return empty dict on parse error (no changes)
        return {}

    return extracted


def get_greeting():
    """Return a time-of-day greeting based on company timezone and config."""
    tz = pytz.timezone(COMPANY['timezone'])
    hour = datetime.now(tz).hour
    greetings = COMPANY['greetings']

    if 5 <= hour < 12:
        return greetings['morning']
    elif 12 <= hour < 18:
        return greetings['afternoon']
    elif 18 <= hour < 22:
        return greetings['evening']
    else:
        return greetings['night']
