# message_classifier.py
# Smart message classification for the voice agent

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
import re
from config.products import PRODUCTS
from config.classification import (
    CLASSIFIER_PATTERNS,
    CONFIDENCE_SCORES,
    SINGLE_ATTRS,
    TECHNICAL_PRODUCT_WORDS,
)


class MessageCategory(Enum):
    """Categories for user messages."""
    GREETING = "greeting"
    TYPO_QUERY = "typo_query"
    VAGUE_QUERY = "vague_query"
    SPECIFIC_QUERY = "specific_query"
    PRICE_INQUIRY = "price_inquiry"
    BUYING_SIGNAL = "buying_signal"
    CLARIFICATION = "clarification"
    OFF_TOPIC = "off_topic"
    GRATITUDE = "gratitude"


@dataclass
class ClassificationResult:
    """Result of message classification."""
    category: MessageCategory
    confidence: float
    corrected_query: Optional[str] = None
    requires_search: bool = False
    prompt_key: str = "default"
    typos_found: Optional[List[dict]] = None


class MessageClassifier:
    """
    Classifies user messages to determine the appropriate response strategy.

    This classifier runs BEFORE any tool invocation to route messages:
    - Non-search categories get short, direct responses
    - Search categories go through _retrieve_products
    """

    def __init__(self):
        # Typo corrections from product config
        self.typo_map = dict(PRODUCTS["typo_corrections"])

        # Pattern definitions from classification config
        self.greeting_patterns = CLASSIFIER_PATTERNS["greeting"]
        self.buying_patterns = CLASSIFIER_PATTERNS["buying"]
        self.vague_patterns = CLASSIFIER_PATTERNS["vague"]
        self.gratitude_patterns = CLASSIFIER_PATTERNS["gratitude"]
        self.off_topic_patterns = CLASSIFIER_PATTERNS["off_topic"]
        self.price_patterns = CLASSIFIER_PATTERNS["price"]
        self.comparison_patterns = CLASSIFIER_PATTERNS["comparison"]

        # Product-related words for validation (from product config + technical terms)
        self.product_words = (
            list(PRODUCTS["domain_keywords"])
            + list(PRODUCTS.get("product_keywords", []))
            + TECHNICAL_PRODUCT_WORDS
        )

        # Single attribute words (for clarification detection)
        self.single_attrs = SINGLE_ATTRS

    def classify(self, message: str, history: List[dict] = None) -> ClassificationResult:
        """
        Classify a user message and determine response strategy.

        Args:
            message: The user's message
            history: Optional conversation history for context

        Returns:
            ClassificationResult with category, confidence, and routing info
        """
        msg = message.lower().strip()
        word_count = len(msg.split())

        print(f"\n{'='*50}")
        print(f"[CLASSIFIER] Analyzing: '{msg}'")
        print(f"[CLASSIFIER] Word count: {word_count}")

        # 1. Check for greetings (highest priority for short messages)
        if self._matches(msg, self.greeting_patterns):
            print(f"[CLASSIFIER] -> GREETING detected")
            return ClassificationResult(
                category=MessageCategory.GREETING,
                confidence=CONFIDENCE_SCORES["greeting"],
                requires_search=False,
                prompt_key="greeting"
            )

        # 2. Check for buying signals (high priority - HOT leads)
        if self._matches(msg, self.buying_patterns):
            print(f"[CLASSIFIER] -> BUYING_SIGNAL detected")
            return ClassificationResult(
                category=MessageCategory.BUYING_SIGNAL,
                confidence=CONFIDENCE_SCORES["buying_signal"],
                requires_search=True,
                prompt_key="buying_hot"
            )

        # 3. Check for gratitude/goodbye
        if self._matches(msg, self.gratitude_patterns):
            print(f"[CLASSIFIER] -> GRATITUDE detected")
            return ClassificationResult(
                category=MessageCategory.GRATITUDE,
                confidence=CONFIDENCE_SCORES["gratitude"],
                requires_search=False,
                prompt_key="gratitude"
            )

        # 4. Check for price inquiry
        if self._matches(msg, self.price_patterns):
            print(f"[CLASSIFIER] -> PRICE_INQUIRY detected")
            return ClassificationResult(
                category=MessageCategory.PRICE_INQUIRY,
                confidence=CONFIDENCE_SCORES["price_inquiry"],
                requires_search=True,
                prompt_key="price_inquiry"
            )

        # 5. Check for clarification (short context-dependent responses)
        if word_count <= 3:
            if msg in ["yes", "no", "ok", "okay", "sure", "ja", "nein"] or self._is_single_attribute(msg):
                print(f"[CLASSIFIER] -> CLARIFICATION detected")
                return ClassificationResult(
                    category=MessageCategory.CLARIFICATION,
                    confidence=CONFIDENCE_SCORES["clarification"],
                    requires_search=True,
                    prompt_key="clarification"
                )

        # 6. Check for typos
        corrected, has_typo, typos_found = self._correct_typos(msg)
        if has_typo:
            is_product_related = self._is_product_related(corrected)
            print(f"[CLASSIFIER] -> TYPO_QUERY detected")
            print(f"[CLASSIFIER]    Typos: {typos_found}")
            print(f"[CLASSIFIER]    Corrected: '{corrected}'")
            print(f"[CLASSIFIER]    Product-related after correction: {is_product_related}")

            return ClassificationResult(
                category=MessageCategory.TYPO_QUERY,
                confidence=CONFIDENCE_SCORES["typo_query"],
                corrected_query=corrected,
                requires_search=is_product_related,
                prompt_key="typo_corrected" if is_product_related else "typo_clarify",
                typos_found=typos_found
            )

        # 7. Check for vague queries
        if self._matches(msg, self.vague_patterns):
            print(f"[CLASSIFIER] -> VAGUE_QUERY detected (pattern match)")
            return ClassificationResult(
                category=MessageCategory.VAGUE_QUERY,
                confidence=CONFIDENCE_SCORES["vague_pattern"],
                requires_search=False,
                prompt_key="vague_clarify"
            )

        # Also check for short messages without specifics
        if word_count <= 5 and not self._has_specifics(msg):
            # Check if it's product-related at all
            if not self._is_product_related(msg):
                print(f"[CLASSIFIER] -> VAGUE_QUERY detected (short, no specifics)")
                return ClassificationResult(
                    category=MessageCategory.VAGUE_QUERY,
                    confidence=CONFIDENCE_SCORES["vague_short"],
                    requires_search=False,
                    prompt_key="vague_clarify"
                )

        # 8. Check for off-topic
        if self._matches(msg, self.off_topic_patterns) and not self._is_product_related(msg):
            print(f"[CLASSIFIER] -> OFF_TOPIC detected")
            return ClassificationResult(
                category=MessageCategory.OFF_TOPIC,
                confidence=CONFIDENCE_SCORES["off_topic"],
                requires_search=False,
                prompt_key="off_topic"
            )

        # 9. Default: Specific query (has enough detail for search)
        print(f"[CLASSIFIER] -> SPECIFIC_QUERY (default)")
        return ClassificationResult(
            category=MessageCategory.SPECIFIC_QUERY,
            confidence=CONFIDENCE_SCORES["default"],
            requires_search=True,
            prompt_key="specific_search"
        )

    def _matches(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the given regex patterns."""
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    def _correct_typos(self, text: str) -> tuple:
        """
        Correct common typos in the text.

        Returns:
            tuple: (corrected_text, has_corrections, list_of_corrections)
        """
        corrected = text
        corrections = []

        for typo, fix in self.typo_map.items():
            # Use word boundary matching to avoid partial replacements
            pattern = r'\b' + re.escape(typo) + r'\b'
            if re.search(pattern, corrected, re.IGNORECASE):
                corrected = re.sub(pattern, fix, corrected, flags=re.IGNORECASE)
                corrections.append({"typo": typo, "correction": fix})

        return corrected, len(corrections) > 0, corrections

    def _has_specifics(self, text: str) -> bool:
        """Check if the message contains specific product criteria."""
        return any(re.search(p, text, re.IGNORECASE) for p in CLASSIFIER_PATTERNS["specific"])

    def _is_single_attribute(self, text: str) -> bool:
        """Check if the text is a single attribute (like 'gesichtsbehandlung' or 'massage')."""
        text_clean = text.strip().lower()
        return text_clean in self.single_attrs

    def _is_product_related(self, text: str) -> bool:
        """Check if the text contains product-related words."""
        text_lower = text.lower()
        return any(word in text_lower for word in self.product_words)
