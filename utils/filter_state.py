# filter_state.py
# Config-driven state tracking for filter preferences.
# All field definitions, allowed values, and aliases come from config/metadata.py.
# Reset triggers and string sets come from config/classification.py.

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Set, List, Tuple
import math
from config.metadata import (
    FIELD_DEFINITIONS,
    CATEGORICAL_VALUES,
    CATEGORICAL_FIELDS_SET,
    NUMERIC_RANGE_FIELDS,
    NUMERIC_VALIDATION,
)
from config.classification import (
    RESET_TRIGGERS,
    FULL_RESET_PHRASES,
    PRICE_RESET_PHRASES,
    PRICE_CONTEXT_WORDS,
    FEATURE_CONTEXT_WORDS,
    TRUTHY_STRINGS,
    FALSY_STRINGS,
)


# =============================================================================
# FILTER VALIDATION RESULT
# =============================================================================

@dataclass
class FilterValidationResult:
    """Result of filter validation with transparency about what was dropped."""
    valid_filters: Dict[str, Any]
    dropped_filters: Dict[str, str]  # field -> reason why dropped
    warnings: List[str]


# =============================================================================
# USER PREFERENCES STATE — Config-driven, domain-independent
# =============================================================================

@dataclass
class UserPreferences:
    """
    Config-driven filter state. Categorical and numeric fields stored in dicts,
    binary features and tags stored in sets. Fully domain-independent —
    field names come from config/metadata.py FIELD_DEFINITIONS.
    """
    # Dict-based storage: {field_name: value}
    categorical: Dict[str, str] = field(default_factory=dict)
    numeric: Dict[str, float] = field(default_factory=dict)

    # Set-based storage
    features: Set[str] = field(default_factory=set)
    negations: Set[str] = field(default_factory=set)
    usage_tags: Set[str] = field(default_factory=set)
    mode_tags: Set[str] = field(default_factory=set)

    def clear_all(self):
        """Full reset of all preferences."""
        self.categorical.clear()
        self.numeric.clear()
        self.features.clear()
        self.negations.clear()
        self.usage_tags.clear()
        self.mode_tags.clear()

    def clear_price(self):
        """Clear price-related filters."""
        self.numeric.pop("max_price", None)
        self.numeric.pop("min_price", None)

    def clear_features(self):
        """Clear all feature preferences."""
        self.features.clear()

    def update_from_extraction(self, extracted: Dict[str, Any]) -> None:
        """
        Update state from LLM extraction result.
        Latest values always override existing ones.
        Field group membership is resolved via config/metadata.py constants.
        """
        for key, val in extracted.items():
            if val is None or val == "":
                continue

            if key in CATEGORICAL_FIELDS_SET and val:
                self.categorical[key] = val
            elif key in NUMERIC_RANGE_FIELDS and val is not None:
                try:
                    self.numeric[key] = float(val)
                except (ValueError, TypeError):
                    pass
            # Binary features, usage tags, and mode tags are not used in Hansshow domain
            # but keeping negations and clears for future extensibility
            elif key.startswith("has_"):
                if val == 1:
                    self.features.add(key)
                elif val == 0:
                    self.features.discard(key)
            elif key.startswith("usage_"):
                if val == 1:
                    self.usage_tags.add(key)
                elif val == 0:
                    self.usage_tags.discard(key)
            elif key.startswith("mode_"):
                if val == 1:
                    self.mode_tags.add(key)
                elif val == 0:
                    self.mode_tags.discard(key)

        # Handle negations
        if extracted.get("negations"):
            for neg in extracted["negations"]:
                self.negations.add(neg)

        # Handle explicit clears
        if extracted.get("clear_price"):
            self.clear_price()
        if extracted.get("clear_features"):
            self.clear_features()
        if extracted.get("clear_all"):
            self.clear_all()

    def to_dict(self) -> Dict[str, Any]:
        """Convert current state to dictionary (for Pinecone queries / LLM context)."""
        result = {}
        result.update(self.categorical)
        result.update(self.numeric)
        for feat in self.features:
            result[feat] = 1
        for tag in self.usage_tags:
            result[tag] = 1
        for tag in self.mode_tags:
            result[tag] = 1
        return result


# =============================================================================
# FILTER VALIDATION — Config-driven (with transparency)
# =============================================================================

def _is_nan(val: Any) -> bool:
    """Check if value is NaN (handles both float and string)."""
    if val is None:
        return False
    if isinstance(val, float) and math.isnan(val):
        return True
    if isinstance(val, str) and val.lower() in ("nan", "none", "null", ""):
        return True
    return False


def _clean_numeric(val: Any) -> Tuple[Optional[float], Optional[str]]:
    """
    Clean and validate numeric value.
    Returns (cleaned_value, error_message).
    """
    if val is None:
        return None, None

    if _is_nan(val):
        return None, "Invalid value (NaN)"

    if isinstance(val, (int, float)):
        return float(val), None

    if isinstance(val, str):
        # Handle German/US formats: "30.000", "30,000", "30k"
        cleaned = (
            val.lower()
            .replace("k", "000")
            .replace(".", "")
            .replace(",", "")
            .replace("€", "")
            .replace("euro", "")
            .replace("km", "")
            .strip()
        )
        # Extract first number-like word
        for word in cleaned.split():
            if word.isdigit():
                return float(word), None
        # Try parsing the whole cleaned string
        try:
            return float(cleaned), None
        except ValueError:
            return None, f"Could not parse '{val}' as number"

    return None, f"Unexpected type: {type(val)}"


def validate_filters(raw: Dict[str, Any]) -> FilterValidationResult:
    """
    Validate extracted filters against config/metadata.py definitions.

    This function:
    1. Validates each field against its group (categorical, numeric, binary/tag)
    2. Resolves aliases for categorical fields
    3. Cleans numeric values and applies sanity checks
    4. Returns what was kept AND what was dropped with reasons
    """
    valid = {}
    dropped = {}
    warnings = []

    for field_name, val in raw.items():
        # Skip None/empty/don't-care values
        if val in (None, "", "all", "any", "unknown", "egal", "doesn't matter"):
            continue

        # NaN protection
        if _is_nan(val):
            dropped[field_name] = "Invalid value (NaN/null)"
            continue

        # Look up field definition
        defn = FIELD_DEFINITIONS.get(field_name)
        if defn is None:
            warnings.append(f"Unknown field '{field_name}' ignored")
            continue

        group = defn["group"]

        # === CATEGORICAL FIELDS ===
        if group == "categorical":
            cat_config = CATEGORICAL_VALUES.get(field_name, {})
            allowed = cat_config.get("allowed")

            if allowed is None:
                # Free-text field (manufacturer, model)
                if isinstance(val, str) and val.strip():
                    valid[field_name] = val.strip()
                else:
                    dropped[field_name] = "Empty value"
            elif val in allowed:
                valid[field_name] = val
            else:
                # Try aliases
                aliases = cat_config.get("aliases", {})
                mapped = aliases.get(val.lower() if isinstance(val, str) else val)
                if mapped:
                    valid[field_name] = mapped
                else:
                    options = ", ".join(allowed)
                    dropped[field_name] = f"'{val}' not available. Options: {options}"
            continue

        # === NUMERIC RANGE FIELDS ===
        if group == "numeric_range":
            cleaned, error = _clean_numeric(val)
            if error:
                dropped[field_name] = error
            elif cleaned is not None:
                # Apply sanity checks from NUMERIC_VALIDATION
                rules = NUMERIC_VALIDATION.get(field_name, {})
                # Apply prefix rule for min_ fields
                if field_name.startswith("min_"):
                    prefix_rules = NUMERIC_VALIDATION.get("_min_prefix_rule", {})
                    rules = {**prefix_rules, **rules}

                if rules.get("min") is not None and cleaned < rules["min"]:
                    dropped[field_name] = f"Value too low: {cleaned}"
                elif rules.get("max") is not None and cleaned > rules["max"]:
                    dropped[field_name] = f"Value too high: {cleaned}"
                else:
                    valid[field_name] = cleaned
            continue

        # === BINARY FEATURES / USAGE TAGS / MODE TAGS ===
        if group in ("binary_feature", "usage_tag", "mode_tag"):
            if isinstance(val, str):
                lowered = val.lower().strip()
                if lowered in TRUTHY_STRINGS:
                    valid[field_name] = 1
                elif lowered in FALSY_STRINGS:
                    # Don't add filter for "don't care"
                    continue
                else:
                    # Assume direct feature mention = wanted
                    valid[field_name] = 1
            elif isinstance(val, (int, float)):
                if int(val) == 1:
                    valid[field_name] = 1
                # val == 0 or 2 means "don't filter for this"
            continue

        # === UNKNOWN GROUP (shouldn't happen with valid config) ===
        warnings.append(f"Unknown group '{group}' for field '{field_name}'")

    return FilterValidationResult(valid, dropped, warnings)


def check_for_reset_triggers(message: str) -> Tuple[bool, str]:
    """
    Check if message contains reset triggers.
    Returns (should_reset, reset_type).

    Reset types:
    - "all": Full reset of all preferences
    - "price": Clear only price preferences
    - "features": Clear only feature preferences
    - "none": No reset
    """
    message_lower = message.lower()

    # Full reset triggers
    for phrase in FULL_RESET_PHRASES:
        if phrase in message_lower:
            return True, "all"

    # Price reset triggers
    for phrase in PRICE_RESET_PHRASES:
        if phrase in message_lower:
            return True, "price"

    # Check for generic reset words (but need context)
    for trigger in RESET_TRIGGERS:
        if trigger in message_lower:
            # Found a trigger word - but which category?
            if any(word in message_lower for word in PRICE_CONTEXT_WORDS):
                return True, "price"
            if any(word in message_lower for word in FEATURE_CONTEXT_WORDS):
                return True, "features"
            # Generic reset
            return True, "all"

    return False, "none"
