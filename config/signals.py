"""
Signal detection and lead scoring configuration.
Edit this file to tune buying signal sensitivity and lead scoring weights per deployment.
Optimized for B2C beauty and cosmetics studio.
"""

# =============================================================================
# BUYING SIGNAL KEYWORDS — detected in user messages to classify intent level
# =============================================================================

# HOT signals — ready to act, clear booking/buying intent
HOT_SIGNALS = [
    "termin", "buchen", "buchung", "vereinbaren",             # Booking intent (appointment, book)
    "preis", "kosten", "was kostet", "preisliste",            # Price inquiries
    "angebot", "gutschein", "geschenkgutschein",              # Offers, gift certificates
    "sofort", "nächste woche", "morgen", "heute",             # Urgency signals
    "beratungstermin", "permanent make-up termin",            # Specific booking
    "möchte buchen", "termin vereinbaren",                    # Direct booking intent
    "kaufen", "bestellen", "online shop",                     # Purchase intent
    "price", "cost", "how much", "book", "appointment",       # English equivalents
]

# WARM signals — interested, engaged
WARM_SIGNALS = [
    "gesichtsbehandlung", "körperbehandlung", "massage",      # Treatment mentions
    "peeling", "fußpflege", "maniküre", "pediküre",          # Specific services
    "forma", "radiofrequenz", "brigitte kettner",             # Method mentions
    "permanent make-up", "augenbrauen", "lippen", "eyeliner", # PMU mentions
    "anti-aging", "falten", "unreinheiten", "trockene haut",  # Skin concerns
    "empfindliche haut", "augenringe", "cellulite",           # More skin concerns
    "empfehlung", "beratung", "hauttyp", "welche behandlung", # Seeking advice
    "naturkosmetik", "nachhaltig", "natürlich",               # Philosophy match
    "entspannung", "wellness", "erholung",                    # Wellness interest
    "vergleich", "unterschied", "besser",                     # Comparison
    "interessant", "klingt gut", "gefällt mir",               # Positive sentiment
    "mehr details", "erzähl mir mehr",                        # Info seeking
    "budget", "euro", "€",                                    # Budget mentions
]

# COOL signals — just browsing, no urgency
COOL_SIGNALS = [
    "mal schauen", "informieren", "nur gucken",               # Casual browsing
    "was bietet ihr an", "welche behandlungen",               # General inquiry
    "vielleicht", "irgendwann", "später",                     # Low urgency
    "bin nicht sicher", "überlege noch",                      # Undecided
    "einfach mal", "aus neugier",                             # Curiosity
    "just looking", "browsing", "curious",                    # English equivalents
]

# =============================================================================
# SIGNAL SCORING — weights for confidence calculation
# =============================================================================

SIGNAL_SCORING = {
    "hot_base": 0.7,            # Base confidence when HOT keywords found
    "hot_increment": 0.1,       # Per additional HOT keyword
    "warm_base": 0.5,           # Base confidence for WARM
    "warm_increment": 0.1,      # Per additional WARM keyword
    "warm_search_increment": 0.1,  # Per search count (for WARM by search activity)
    "cool_confidence": 0.3,     # Fixed confidence for COOL
    "mild_base": 0.4,           # Base confidence for MILD (no signals)
    "mild_search_increment": 0.1,  # Per search count (for MILD)
}

# =============================================================================
# LEAD SCORING — weights for ML-style lead degree (0-10) calculation
# =============================================================================

LEAD_SCORING = {
    # Factor 1: Intent Signal (0-3.0)
    "hot_weight": 0.3,          # Per HOT keyword (max 1.5)
    "hot_cap": 1.5,             # Max HOT contribution
    "warm_weight": 0.15,        # Per WARM keyword (max 0.75)
    "warm_cap": 0.75,           # Max WARM contribution
    "cool_penalty": -0.2,       # Per COOL keyword
    "intent_confidence_divisor": 100,  # Message length for confidence calc

    # Factor 2: Engagement (0-2.5)
    "search_log_weight": 0.8,   # log(1 + search_count) multiplier
    "search_cap": 1.5,          # Max search contribution
    "products_weight": 0.15,    # Per product shown
    "products_cap": 1.0,        # Max products contribution

    # Factor 3: Qualification timing/step scores
    "timing_scores": {
        "immediately": 1.5,     # "Sofort" — highest urgency
        "2_4_weeks": 1.0,       # "In 2-4 Wochen"
        "later": 0.3,           # "Später"
    },
    "timing_default": 0.5,      # When no timing selected yet

    "step_scores": {
        "demo": 1.2,            # "Beratungstermin" — highest intent
        "price_details": 0.8,   # "Preise und Details"
        "keep_browsing": 0.2,   # "Weiter umschauen"
    },
    "step_default": 0.4,        # When no step selected yet

    # Synergy bonus: timing + step combinations
    "synergy_rules": [
        {"timing": "immediately", "step": "demo", "bonus": 0.8},
        {"timing": "immediately", "step": "price_details", "bonus": 0.5},
        {"timing": "2_4_weeks", "step": "demo", "bonus": 0.4},
    ],

    # Factor 4: Accessibility (0-1.0)
    "reach_scores": {
        "phone_today": 1.0,     # "Telefon heute" — easiest to reach
        "whatsapp_today": 0.8,  # "WhatsApp heute"
        "email_week": 0.4,      # "E-Mail diese Woche"
    },
    "reach_default": 0.3,       # When no reachability selected yet

    # Confidence
    "base_confidence": 0.6,     # Minimum confidence
    "per_data_point": 0.1,      # Bonus per known data point (max 4)
}
