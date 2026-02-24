"""
Product metadata — THE single source of truth for all treatment attributes,
filter definitions, display names, and validation rules for Beauty Lounge treatments.

PURE DATA — no logic, no functions. Only dicts, lists, and derived constants.

Since we use local data files instead of RAG/Pinecone, this metadata is simplified.
"""

from typing import Dict, Any, List
from config.products import PRODUCTS

# ═══════════════════════════════════════════════════════════════════════════════
# ZONE A — EDITABLE: Change these for a new product domain
# ═══════════════════════════════════════════════════════════════════════════════


# =============================================================================
# SECTION 1: FIELD DEFINITIONS
# Every filterable treatment attribute for Beauty Lounge services
# =============================================================================

FIELD_DEFINITIONS: Dict[str, Dict[str, Any]] = {

    # ── NUMERIC RANGE FILTERS ────────────────────────────────────────────────
    "duration_min": {
        "python_type": float,
        "group": "numeric_range",
        "display_name": "Min Dauer (Minuten)",          # Min Duration (minutes)
        "topic": "Behandlungsdauer",                     # Treatment Duration
    },
    "duration_max": {
        "python_type": float,
        "group": "numeric_range",
        "display_name": "Max Dauer (Minuten)",           # Max Duration (minutes)
        "topic": "Behandlungsdauer",                     # Treatment Duration
    },

    # ── CATEGORICAL / STRING FIELDS ──────────────────────────────────────────
    "treatment_category": {
        "python_type": str,
        "group": "categorical",
        "display_name": "Behandlungskategorie",          # Treatment Category
        "topic": "Kategorie",                            # Category
        "post_filter": True,
    },
    "skin_type": {
        "python_type": str,
        "group": "categorical",
        "display_name": "Hauttyp",                       # Skin Type
        "topic": "Hauttyp",                              # Skin Type
        "post_filter": True,
    },
    "first_time_suitable": {
        "python_type": str,
        "group": "categorical",
        "display_name": "Für Erstbesucher geeignet",     # Suitable for first-timers
        "topic": "Erstbehandlung",                       # First treatment
    },
    "method": {
        "python_type": str,
        "group": "categorical",
        "display_name": "Methode",                       # Method
        "topic": "Methode",                              # Method
        "post_filter": True,
    },
    "model_name": {
        "python_type": str,
        "group": "categorical",
        "display_name": "Behandlungsname",               # Treatment Name
    },
}


# =============================================================================
# SECTION 2: CATEGORICAL VALUES
# Allowed values and normalization aliases
# =============================================================================

CATEGORICAL_VALUES: Dict[str, Dict[str, Any]] = {
    "treatment_category": {
        "allowed": ["Gesicht", "Körper", "Hände & Füße", "Permanent Make-Up", "Wellness"],
        "aliases": {
            "gesicht": "Gesicht",
            "facial": "Gesicht",
            "gesichtsbehandlung": "Gesicht",
            "face": "Gesicht",
            "körper": "Körper",
            "body": "Körper",
            "körperbehandlung": "Körper",
            "hände": "Hände & Füße",
            "füße": "Hände & Füße",
            "fußpflege": "Hände & Füße",
            "maniküre": "Hände & Füße",
            "pediküre": "Hände & Füße",
            "hand": "Hände & Füße",
            "foot": "Hände & Füße",
            "permanent make-up": "Permanent Make-Up",
            "permanent makeup": "Permanent Make-Up",
            "pmu": "Permanent Make-Up",
            "permanent": "Permanent Make-Up",
            "massage": "Wellness",
            "entspannung": "Wellness",
            "wellness": "Wellness",
            "relaxation": "Wellness",
        },
    },
    "skin_type": {
        "allowed": ["Normal", "Trocken", "Fettig", "Mischhaut", "Empfindlich"],
        "aliases": {
            "normal": "Normal",
            "trocken": "Trocken",
            "dry": "Trocken",
            "fettig": "Fettig",
            "oily": "Fettig",
            "ölig": "Fettig",
            "mischhaut": "Mischhaut",
            "combination": "Mischhaut",
            "gemischt": "Mischhaut",
            "empfindlich": "Empfindlich",
            "sensitive": "Empfindlich",
            "sensibel": "Empfindlich",
        },
    },
    "first_time_suitable": {
        "allowed": ["Ja", "Nein"],
        "aliases": {
            "yes": "Ja",
            "no": "Nein",
            "ja": "Ja",
            "nein": "Nein",
        },
    },
    "method": {
        "allowed": ["Klassisch", "Apparativ", "Brigitte Kettner", "Permanent"],
        "aliases": {
            "klassisch": "Klassisch",
            "klassische kosmetik": "Klassisch",
            "traditional": "Klassisch",
            "apparativ": "Apparativ",
            "forma": "Apparativ",
            "radiofrequenz": "Apparativ",
            "rf": "Apparativ",
            "gerät": "Apparativ",
            "brigitte kettner": "Brigitte Kettner",
            "kettner": "Brigitte Kettner",
            "naturkosmetik": "Brigitte Kettner",
            "mbk": "Brigitte Kettner",
            "permanent": "Permanent",
            "permanent make-up": "Permanent",
            "pmu": "Permanent",
        },
    },
}


# =============================================================================
# SECTION 3: PRODUCT PROJECTIONS
# How raw data is transformed for different consumers
# =============================================================================

PRODUCT_PROJECTIONS: Dict[str, Dict[str, Dict[str, Any]]] = {
    # Sent to frontend via WebSocket
    "frontend": {
        "url":          {"db_field": "url"},
        "image":        {"db_field": "image"},
        "name":         {"db_field": "name"},
        "description":  {"db_field": "Introduction"},
        "category":     {"db_field": "category"},
    },
    # Sent to LLM as result context
    "llm_context": {
        "name":         {"db_field": "name"},
        "url":          {"db_field": "url"},
        "description":  {"db_field": "Introduction"},
        "features":     {"db_field": "Features"},
        "benefits":     {"db_field": "Benefits to Clients"},
    },
    # Stored in userdata for email summary
    "stored": {
        "name":         {"db_field": "name"},
        "url":          {"db_field": "url"},
        "category":     {"db_field": "category"},
    },
}


# =============================================================================
# SECTION 4: MATCH SCORING FIELDS
# Fields used in analyze_match_quality()
# =============================================================================

MATCH_SCORING_FIELDS: List[Dict[str, str]] = [
    {"filter_key": "treatment_category", "db_field": "category", "compare": "contains_ci"},
    {"filter_key": "method", "db_field": "method", "compare": "contains_ci"},
]


# =============================================================================
# SECTION 5: IMPLICIT MAPPINGS
# Shortcut phrases that translate into filters
# =============================================================================

IMPLICIT_MAPPINGS: List[Dict[str, Any]] = [
    {"phrases": ["kurz", "schnell", "short", "quick"], "filters": {"duration_max": 30}},
    {"phrases": ["lang", "ausführlich", "long", "extended"], "filters": {"duration_min": 60}},
    {"phrases": ["gesicht", "facial", "face"], "filters": {"treatment_category": "Gesicht"}},
    {"phrases": ["entspannung", "relaxen", "relax"], "filters": {"treatment_category": "Wellness"}},
    {"phrases": ["naturkosmetik", "natürlich", "natural"], "filters": {"method": "Brigitte Kettner"}},
]


# =============================================================================
# SECTION 6: NUMERIC VALIDATION
# Sanity-check bounds for numeric fields
# =============================================================================

NUMERIC_VALIDATION: Dict[str, Dict[str, Any]] = {
    "duration_min": {"min": 15, "max": 180},
    "duration_max": {"min": 15, "max": 180},
}


# ═══════════════════════════════════════════════════════════════════════════════
# ZONE B — AUTO-DERIVED: Do not edit below this line
# Everything below is computed from Zone A at import time.
# ═══════════════════════════════════════════════════════════════════════════════


# ── Field group sets ──────────────────────────────────
NUMERIC_RANGE_FIELDS: set = {
    n for n, d in FIELD_DEFINITIONS.items() if d["group"] == "numeric_range"
}
CATEGORICAL_FIELDS_SET: set = {
    n for n, d in FIELD_DEFINITIONS.items() if d["group"] == "categorical"
}

# ── EXTRACTION_PROMPT_FIELDS (for prompt/static_extraction.py) ───────────────
EXTRACTION_PROMPT_FIELDS: Dict[str, list] = {
    "categorical": sorted(CATEGORICAL_FIELDS_SET),
    "numeric_range": sorted(NUMERIC_RANGE_FIELDS),
}
