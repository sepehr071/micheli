"""
Filter extraction prompt — JSON schema spec for LLM-based filter parsing.

STATIC: JSON schema structure, critical rules, examples format.
CONFIGURABLE: Field names, allowed values, implicit mappings all from config/metadata.py.

Used by: utils/utils.py
"""

from datetime import datetime
from config.company import COMPANY
from config.products import PRODUCTS
from config.metadata import (
    FIELD_DEFINITIONS, CATEGORICAL_VALUES, EXTRACTION_PROMPT_FIELDS,
    IMPLICIT_MAPPINGS,
)

current_year = datetime.now().year


# ═══════════════════════════════════════════════════════════════════════════════
# Auto-generated prompt sections from config/metadata.py
# ═══════════════════════════════════════════════════════════════════════════════

def _build_categorical_spec() -> str:
    lines = []
    for name in EXTRACTION_PROMPT_FIELDS["categorical"]:
        cat = CATEGORICAL_VALUES.get(name, {})
        allowed = cat.get("allowed")
        if allowed is None:
            lines.append(f"- {name}: any value (free text)")
        else:
            vals = " | ".join(f'"{v}"' for v in allowed)
            lines.append(f"- {name}: {vals}")
    return "\n".join(lines)


def _build_numeric_spec() -> str:
    col_groups: dict[str, list[str]] = {}
    for name in EXTRACTION_PROMPT_FIELDS["numeric_range"]:
        col = FIELD_DEFINITIONS[name].get("db_column", name)
        col_groups.setdefault(col, []).append(name)
    lines = []
    for names in col_groups.values():
        lines.append("- " + ", ".join(sorted(names)))
    return "\n".join(lines)


def _build_implicit_spec() -> str:
    lines = []
    for m in IMPLICIT_MAPPINGS:
        phrases = ", ".join(f'"{p}"' for p in m["phrases"])
        resolved = {}
        for k, v in m["filters"].items():
            resolved[k] = current_year - 2 if v == "CURRENT_YEAR_MINUS_2" else v
        filt = ", ".join(f"{k}: {v}" for k, v in resolved.items())
        lines.append(f"   - {phrases} \u2192 {filt}")
    return "\n".join(lines)


# Pre-compute at import time
_categorical_spec = _build_categorical_spec()
_numeric_spec = _build_numeric_spec()
_binary_spec = ""  # Not used in Beauty Lounge domain
_usage_spec = ""   # Not used in Beauty Lounge domain
_mode_spec = ""    # Not used in Beauty Lounge domain
_implicit_spec = _build_implicit_spec()
_never_use = ""    # Not used in Beauty Lounge domain


# ═══════════════════════════════════════════════════════════════════════════════
# Prompt template — rules, examples, and task section are hand-tuned per domain
# ═══════════════════════════════════════════════════════════════════════════════

SINGLE_EXTRACTION_PROMPT = f"""
You are a precise filter extractor for a {COMPANY['language']} {PRODUCTS['domain']} Kosmetikstudio.
Your task: Extract search filters from the user's CURRENT message, considering their existing preferences.

INPUT FORMAT:
- Current message: The user's latest request
- Current preferences: Their existing filter state (may be empty)

OUTPUT FORMAT:
Return a JSON object with ONLY the filters that should change based on the CURRENT message.
Do NOT repeat unchanged preferences from current state.

\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
ALLOWED FILTER KEYS (use EXACTLY these names):
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501

CATEGORICAL (exact values required):
{_categorical_spec}

NUMERIC RANGES (clean numbers only):
{_numeric_spec}

BINARY FEATURES (use 1 for wanted, omit if not mentioned):
{_binary_spec}

USAGE TAGS (use 1 if mentioned):
{_usage_spec}

MODE TAGS (use 1 if mentioned):
{_mode_spec}

SPECIAL CONTROL FIELDS:
- clear_all: true (when user wants to start completely fresh)
- clear_duration: true (when user removes duration constraint)

\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
CRITICAL RULES:
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501

1. LATEST MESSAGE WINS: If user changes a preference, output the NEW value only.
   - "Ich m\u00f6chte eine Gesichtsbehandlung" then "doch lieber eine Massage" \u2192 output: {{"treatment_category": "Wellness"}}

2. RESET TRIGGERS: These phrases mean clear preferences:
   - "vergiss", "forget", "egal", "doesn't matter", "von vorne"
   - Full reset: "vergiss alles", "start over", "ganz anders"
   \u2192 Output: {{"clear_all": true}} or {{"clear_duration": true}} etc.

3. IMPLICIT MAPPINGS (apply ONLY if exact terms appear):
{_implicit_spec}

4. OFF-TOPIC MESSAGES: If message is completely unrelated to {PRODUCTS['domain']} (weather, jokes, greetings):
   \u2192 Output: {{}}

5. DO NOT INFER what's not explicitly mentioned:
   - "entspannung" does NOT imply method (could be Massage or Gesichtsbehandlung)
   - "haut" does NOT add all skin types
   - Only extract what the user explicitly requests

6. NEVER use these field names (they break the system):
{_never_use}

\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
EXAMPLES:
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501

Example 1 - New search:
Current message: "Ich suche eine Gesichtsbehandlung f\u00fcr trockene Haut, nicht l\u00e4nger als 60 Minuten"
Current preferences: {{}}
Output: {{"treatment_category": "Gesicht", "skin_type": "Trocken", "duration_max": 60}}

Example 2 - Preference change:
Current message: "Doch lieber eine K\u00f6rperbehandlung"
Current preferences: {{"treatment_category": "Gesicht", "skin_type": "Trocken", "duration_max": 60}}
Output: {{"treatment_category": "K\u00f6rper"}}

Example 3 - Remove constraint:
Current message: "Die Dauer ist mir egal, zeigen Sie mir alles"
Current preferences: {{"treatment_category": "Gesicht", "duration_max": 60}}
Output: {{"clear_duration": true}}

Example 4 - Complete reset:
Current message: "Vergessen Sie alles, ich m\u00f6chte etwas ganz anderes"
Current preferences: {{"treatment_category": "Gesicht", "skin_type": "Trocken", "duration_max": 60}}
Output: {{"clear_all": true}}

Example 5 - Specific method:
Current message: "Haben Sie Behandlungen mit der Brigitte Kettner Methode?"
Current preferences: {{}}
Output: {{"method": "Brigitte Kettner"}}

Example 6 - Off-topic (return empty):
Current message: "Wie wird das Wetter morgen?"
Current preferences: {{"treatment_category": "Gesicht"}}
Output: {{}}

Example 7 - Add filter to existing:
Current message: "Und das sollte auch f\u00fcr Erstkundinnen geeignet sein"
Current preferences: {{"treatment_category": "Wellness", "method": "Klassisch"}}
Output: {{"first_time_suitable": "Ja"}}

\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
YOUR TASK:
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501

Current message: {{current_message}}
Current preferences: {{current_preferences}}

Output ONLY valid JSON. No markdown, no explanation.
"""
