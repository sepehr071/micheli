"""
Configurable prompt settings — word limits, expert phrases, signal triggers.
Edit this file to customize response lengths and expert offer wording per deployment.
All German text has English translations in comments.
"""

from config.services import SERVICES

# --- Derived constants from services config ---

_expert = SERVICES["expert_title"]          # e.g., "Kosmetikerin" ("Beautician")
_expert_alt = SERVICES["expert_title_alt"]  # e.g., "Beauty-Beraterin" ("Beauty consultant")
_primary_service = SERVICES["primary_service"]  # e.g., "Beratungstermin" ("Consultation appointment")

# =============================================================================
# WORD LIMITS — max words per dynamic template category
# =============================================================================

TEMPLATE_WORD_LIMITS = {
    "greeting": 30,          # Initial greeting
    "typo_clarify": 30,      # Typo confirmation question
    "typo_corrected": 40,    # Typo auto-corrected + results
    "vague_clarify": 30,     # Vague request clarification
    "specific_search": 70,   # Search results presentation
    "price_inquiry": 40,     # Price-related response
    "buying_hot": 35,        # Strong purchase signal
    "clarification": 35,     # Confirmation response
    "comparison": 50,        # Comparison request
    "off_topic": 15,         # Off-topic redirect
    "gratitude": 15,         # Thank you / goodbye
    "objection": 35,         # Customer objection handling
    "no_results": 40,        # No matching results
    "default": 40,           # Generic fallback
}

# =============================================================================
# EXPERT OFFER PHRASES — context-aware phrases for expert contact offers
# Organized by signal context. Lists rotate via offer_count % len(phrases).
# All phrases end with "möchten Sie, dass sie Sie kontaktiert?" ("would you like her to contact you?")
# =============================================================================

EXPERT_PHRASES = {
    # Mismatch context — user wanted something we couldn't provide
    # "The desired treatment is currently not available. Our {expert} knows more options..."
    "mismatch_color": f"Die gewünschte Behandlung ist gerade nicht verfügbar. Unsere {_expert} kennt weitere Optionen – möchten Sie, dass sie Sie kontaktiert?",
    # "Not all criteria could be met. Our {expert} knows more possibilities..."
    "mismatch_generic": f"Nicht alle Kriterien konnten erfüllt werden. Unsere {_expert} kennt weitere Möglichkeiten – möchten Sie, dass sie Sie kontaktiert?",

    # HOT signal — price-related triggers
    "hot_price": [
        # "Our {expert} can explain all price details and treatment packages..."
        f"Unsere {_expert} kann Ihnen alle Preisdetails und Behandlungspakete erklären – möchten Sie, dass sie Sie kontaktiert?",
        # "For exact prices and individual offers, our {expert} is the right person..."
        f"Für genaue Preise und individuelle Angebote ist unsere {_expert} die Richtige – möchten Sie, dass sie Sie kontaktiert?",
    ],

    # HOT signal — availability-related triggers
    "hot_availability": [
        # "Our {expert} can check available appointments immediately..."
        f"Unsere {_expert} kann die freien Termine sofort prüfen – möchten Sie, dass sie Sie kontaktiert?",
        # "Our {expert} knows all current availability..."
        f"Unsere {_expert} kennt alle aktuellen Verfügbarkeiten – möchten Sie, dass sie Sie kontaktiert?",
    ],

    # HOT signal — consultation / appointment triggers
    "hot_testdrive": [
        # "Our {expert} can organize a {consultation} for you..."
        f"Unsere {_expert} kann einen {_primary_service} für Sie organisieren – möchten Sie, dass sie Sie kontaktiert?",
        # "For a personal consultation, our {expert} is the best contact..."
        f"Für eine persönliche Beratung ist unsere {_expert} die beste Ansprechpartnerin – möchten Sie, dass sie Sie kontaktiert?",
    ],

    # HOT signal — generic booking intent
    # "Our {expert} can clarify all details for you..."
    "hot_generic": f"Unsere {_expert} kann Ihnen alle Details klären – möchten Sie, dass sie Sie kontaktiert?",

    # WARM/MILD signals — varied phrases for moderate interest
    "warm": [
        # "Our {expert} can show you all details..."
        f"Unsere {_expert} kann Ihnen alle Details zeigen – möchten Sie, dass sie Sie kontaktiert?",
        # "Our {beauty consultant} can help you personally..."
        f"Unsere {_expert_alt} kann Ihnen persönlich weiterhelfen – möchten Sie, dass sie Sie kontaktiert?",
        # "For questions, our {expert} is the right person..."
        f"Bei Fragen ist unsere {_expert} die Richtige – möchten Sie, dass sie Sie kontaktiert?",
        # "Our {expert} knows everything about this..."
        f"Unsere {_expert} kennt sich bestens aus – möchten Sie, dass sie Sie kontaktiert?",
    ],
}

# =============================================================================
# SIGNAL TRIGGERS — keywords that determine which expert phrase to use
# =============================================================================

SIGNAL_TRIGGERS = {
    # Price-related keywords
    "price": [
        "preis", "kosten", "was kostet", "euro", "€",     # "price", "costs", "how much", "euro"
        "gutschein", "geschenkgutschein", "angebot",        # "voucher", "gift voucher", "offer"
        "rabatt", "nachlass",                               # "discount", "reduction"
    ],
    # Availability-related keywords
    "availability": [
        "termin", "verfügbar", "freie termine",             # "appointment", "available", "free slots"
        "wann kann ich", "nächste woche",                   # "when can I", "next week"
        "sofort", "heute noch",                             # "immediately", "today still"
    ],
    # Consultation / appointment keywords
    "testdrive": [
        "beratungstermin", "beratung",                      # "consultation appointment", "consultation"
        "ausprobieren", "erstbehandlung",                   # "try out", "first treatment"
        "termin buchen", "termin vereinbaren",              # "book appointment", "schedule appointment"
    ],
}
