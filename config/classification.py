"""
Message classification patterns and behavioral thresholds.
Edit THIS file for new language or domain.

Used by: utils/message_classifier.py, utils/filter_state.py, utils/suggestion_engine.py
"""

# =============================================================================
# SECTION 1: MESSAGE CLASSIFICATION PATTERNS (regex)
# Used by: utils/message_classifier.py
# =============================================================================

CLASSIFIER_PATTERNS = {
    "greeting": [
        r"^(hello|hi|hey|good\s*(morning|afternoon|evening)|greetings|hallo|guten\s*(morgen|tag|abend))\.?$",
        r"^how\s+are\s+you\.?$",
        r"^(what'?s\s+up|wie\s+geht'?s)\.?$",
    ],
    "buying": [
        r"(buchen|buchung|termin|vereinbaren|book|appointment)",        # Booking
        r"(preis|kosten|preisliste|angebot|price|cost|quote)",          # Price
        r"(gutschein|geschenkgutschein|gift)",                          # Gift certificates
        r"(sofort|nächste\s+woche|morgen|heute|immediately|urgent)",    # Urgency
        r"(kaufen|bestellen|buy|purchase|order)",                       # Purchase
        r"(beratungstermin|beratung|consultation)",                     # Consultation
    ],
    "vague": [
        r"^ich\s+(suche|brauche|möchte)\s+(eine?\s+)?(behandlung|pflege|beratung|massage)\.?$",
        r"^was\s+(bietet\s+ihr\s+an|habt\s+ihr|gibt\s+es)\.?$",
        r"^(zeig|zeigen\s+sie)\s+mir\s+(etwas|behandlungen|alles)\.?$",
        r"^ich\s+brauche\s+hilfe\.?$",
        r"^i\s+(need|want|looking\s+for)\s+(a|an|some)\s+(treatment|service|facial|massage)\.?$",
        r"^(tell|erzählen)\s+(me|sie\s+mir)\s+(about|more|über|mehr)\.?$",
    ],
    "gratitude": [
        r"(thank|thanks|appreciate|danke|vielen\s+dank)",
        r"(bye|goodbye|see\s+you|take\s+care|tschüss|auf\s+wiedersehen)",
        r"(that'?s\s+(all|great|helpful)|das\s+(war'?s|reicht|ist\s+alles))",
    ],
    "off_topic": [
        r"(weather|rain|sun|cold|hot|wetter|regen|sonne)",
        r"(auto|fahrzeug|werkstatt|car|vehicle)",                       # Cars (off-topic for beauty)
        r"(insurance|tax|legal|versicherung|steuer)",
        r"(football|sport|music|movie|politics|fußball|film|politik)",
        r"(food|restaurant|hotel|vacation|essen|urlaub)",
    ],
    "price": [
        r"(wie\s*viel|how\s+much|was\s+kostet)",
        r"(preis|price)\s*(von|für|of|for)?",
        r"(kosten|cost)\s*(von|für|of|for)?",
        r"(preisliste|pricing)\s*(für|for|information)?",
        r"budget",
        r"(angebot|quote|offer)",
    ],
    "comparison": [
        r"(unterschied|difference|compare)\s+(zwischen|between)",
        r"(besser|better|worse)\s+(als|than)",
        r"oder\s+.+\s+oder",
        r"was\s+(empfehlen\s+sie|do\s+you\s+recommend)",
        r"(welche|which)\s+(behandlung|one|treatment)\s+(ist|is)\s+(besser|better|best)",
    ],
    "specific": [
        r"\d+",                                                         # Numbers (duration, price)
        r"(gesichtsbehandlung|fußpflege|massage|peeling|permanent.?make.?up|maniküre|forma)",
        r"(kosmetik|behandlung|hautpflege|beauty|wellness)",
        r"(radiofrequenz|kollagen|hyaluron|anti.?aging|brigitte.?kettner)",
        r"(dauer|minuten|stunde|hauttyp|empfindlich|trocken|fettig)",
        r"(studio|salon|termin|sitzung|erstbehandlung)",
    ],
}

# =============================================================================
# SECTION 2: CONFIDENCE THRESHOLDS
# Used by: utils/message_classifier.py
# =============================================================================

CONFIDENCE_SCORES = {
    "greeting": 0.95,
    "buying_signal": 0.9,
    "gratitude": 0.9,
    "price_inquiry": 0.9,
    "clarification": 0.85,
    "typo_query": 0.8,
    "off_topic": 0.8,
    "vague_pattern": 0.75,
    "vague_short": 0.7,
    "default": 0.7,
}

# =============================================================================
# SECTION 3: SINGLE-ATTRIBUTE WORDS (clarification detection)
# Used by: utils/message_classifier.py
# =============================================================================

SINGLE_ATTRS = [
    "gesichtsbehandlung", "fußpflege", "massage", "peeling", "permanent",
    "maniküre", "forma", "wellness", "anti-aging", "brigitte kettner",
    "kurz", "lang", "gesicht", "körper",
    "yes", "no", "ok", "okay", "sure", "right", "correct",
    "ja", "nein", "gut", "richtig",
]

# =============================================================================
# SECTION 4: TECHNICAL PRODUCT WORDS (beyond domain_keywords from products.py)
# Used by: utils/message_classifier.py
# =============================================================================

TECHNICAL_PRODUCT_WORDS = [
    "radiofrequenz", "kollagen", "hyaluron", "hyaluronsäure",
    "microneedling", "dermapen", "mikrodermabrasion",
    "rf", "led", "ultraschall", "hochfrequenz",
    "peptide", "retinol", "vitamin", "serum",
    "elastin", "ceramide", "antioxidantien",
]

# =============================================================================
# SECTION 5: RESET TRIGGERS AND PHRASES
# Used by: utils/filter_state.py
# =============================================================================

RESET_TRIGGERS = {
    "forget", "never mind", "actually not", "reset",
    "no preference", "doesn't matter",
    "open to anything", "just show me",
    "start over", "begin again",
    "vergiss", "egal", "von vorne", "ganz anders",             # German
    "keine präferenz", "zeig mir alles",                        # German
}

FULL_RESET_PHRASES = [
    "forget everything", "start over", "reset search",
    "from the beginning", "completely different", "something else",
    "just show me", "all products",
    "vergiss alles", "nochmal von vorne", "ganz anders",        # German
    "alles neu", "zeig mir alles",                              # German
]

PRICE_RESET_PHRASES = [
    "no budget", "without price limit", "any price",
    "price doesn't matter", "no limit", "open budget",
    "kein budget", "ohne preislimit", "egal was es kostet",     # German
]

PRICE_CONTEXT_WORDS = ["price", "budget", "cost", "dollar", "euro", "€", "$", "preis", "kosten"]
FEATURE_CONTEXT_WORDS = ["feature", "specification", "specs", "capability", "eigenschaft", "merkmal"]

# =============================================================================
# SECTION 6: TRUTHY/FALSY STRING SETS
# Used by: utils/filter_state.py → validate_filters()
# =============================================================================

TRUTHY_STRINGS = {"yes", "yeah", "true", "1", "important", "must", "need", "required", "ja", "wichtig"}
FALSY_STRINGS = {"no", "nope", "false", "0", "not important", "optional", "skip", "nein", "unwichtig"}

# =============================================================================
# SECTION 7: RELAXATION THRESHOLDS
# Used by: utils/suggestion_engine.py
# =============================================================================

RELAXATION_THRESHOLDS = {
    "min_results_ok": 2,              # >= this many results = no relaxation needed
    "max_features_before_relax": 3,   # If >= this many features and 0 results, suggest dropping
}
