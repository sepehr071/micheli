"""
Small utility functions — email validation, time-based greeting.

Extracted from filter_extraction.py (which is being deleted).
"""

import re
import pytz
from datetime import datetime
from config.company import COMPANY


def is_valid_email_syntax(s: str) -> bool:
    EMAIL_RE = re.compile(
        r"^(?=.{1,254}$)(?=.{1,64}@)"
        r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@"
        r"(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}$"
    )
    return EMAIL_RE.match(s) is not None


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
