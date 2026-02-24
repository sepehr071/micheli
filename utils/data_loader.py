"""
Data loader and classifier for Beauty Lounge treatment data.
Reads treatment information from local data files instead of RAG/Pinecone service.

Used by: agents/main_agent.py
"""

import json
import logging
import os
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Base URL for images
IMAGE_BASE_URL = ""  # Placeholder — update when Beauty Lounge provides treatment images


# =============================================================================
# DATA CATEGORY - Categories for data retrieval
# =============================================================================

class DataCategory:
    """Categories for data retrieval."""
    TREATMENTS = "treatments"
    PERMANENT_MAKEUP = "permanent_makeup"
    WELLNESS = "wellness"
    GENERAL = "general"
    FAQ = "faq"
    ALL = "all"

    # Backward compatibility aliases
    NEBULAR = TREATMENTS
    OTHER = PERMANENT_MAKEUP
    USE_CASES = WELLNESS


# =============================================================================
# IMAGE HELPER - Build image URLs
# =============================================================================

def build_image_url(image_path: str) -> str:
    """Build full image URL from relative path."""
    if not image_path:
        return ""
    # If already a full URL, return as is
    if image_path.startswith("http"):
        return image_path
    if not IMAGE_BASE_URL:
        return image_path
    return IMAGE_BASE_URL + image_path


def build_image_urls(image_paths: List[str]) -> List[str]:
    """Build full image URLs from list of relative paths."""
    return [build_image_url(path) for path in image_paths if path]


# =============================================================================
# DATA LOADER - Loads treatment data from local files
# =============================================================================

class DataLoader:
    """Loads and parses treatment data from local text files."""

    _instance = None
    _treatments_data = None
    _permanent_makeup_data = None
    _wellness_data = None
    _general_info_data = None
    _faq_data = None
    _all_products_json = None
    # LLM context caches
    _treatments_llm_context = None
    _permanent_makeup_llm_context = None
    _wellness_llm_context = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_data_dir(self) -> str:
        """Get the path to the data directory."""
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

    def _parse_product_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a product line from the data file."""
        line = line.strip()
        if not line or not line.startswith("-"):
            return None

        # Remove the leading "-N " where N is a number
        match = re.match(r'-\d+\s+(.+)', line)
        if not match:
            return None

        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse product JSON: {e}")
            return None

    def _process_product_images(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Process product images and build full URLs."""
        if "image" not in product or not product["image"]:
            return product

        # Handle image array field
        if isinstance(product["image"], list):
            product["images"] = build_image_urls(product["image"])
            if product["images"]:
                product["image_url"] = product["images"][0]
        # Handle single image field
        elif isinstance(product["image"], str):
            product["image_url"] = build_image_url(product["image"])
            product["images"] = [product["image_url"]]

        return product

    def load_treatments(self) -> List[Dict[str, Any]]:
        """Load treatments from the data file."""
        if self._treatments_data is not None:
            return self._treatments_data

        file_path = os.path.join(self._get_data_dir(), "beauty-services", "treatments", "treatments.txt")
        products = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    product = self._parse_product_line(line)
                    if product:
                        product['category'] = 'treatments'
                        product = self._process_product_images(product)
                        products.append(product)
            logger.info(f"Loaded {len(products)} treatments from {file_path}")
        except FileNotFoundError:
            logger.warning(f"Treatments file not found: {file_path}")
        except Exception as e:
            logger.error(f"Error loading treatments: {e}")

        self._treatments_data = products
        return products

    def load_permanent_makeup(self) -> List[Dict[str, Any]]:
        """Load permanent makeup services from the data file."""
        if self._permanent_makeup_data is not None:
            return self._permanent_makeup_data

        file_path = os.path.join(self._get_data_dir(), "beauty-services", "permanent-makeup", "permanent-makeup.txt")
        products = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    product = self._parse_product_line(line)
                    if product:
                        product['category'] = 'permanent_makeup'
                        product = self._process_product_images(product)
                        products.append(product)
            logger.info(f"Loaded {len(products)} permanent makeup services from {file_path}")
        except FileNotFoundError:
            logger.warning(f"Permanent makeup file not found: {file_path}")
        except Exception as e:
            logger.error(f"Error loading permanent makeup services: {e}")

        self._permanent_makeup_data = products
        return products

    def load_wellness(self) -> List[Dict[str, Any]]:
        """Load wellness services from the data file."""
        if self._wellness_data is not None:
            return self._wellness_data

        file_path = os.path.join(self._get_data_dir(), "beauty-services", "wellness", "wellness.txt")
        wellness = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    item = self._parse_product_line(line)
                    if item:
                        item['category'] = 'wellness'
                        item = self._process_product_images(item)
                        wellness.append(item)
            logger.info(f"Loaded {len(wellness)} wellness services from {file_path}")
        except FileNotFoundError:
            logger.warning(f"Wellness file not found: {file_path}")
        except Exception as e:
            logger.error(f"Error loading wellness services: {e}")

        self._wellness_data = wellness
        return wellness

    # Backward compatibility aliases
    def load_nebular_products(self) -> List[Dict[str, Any]]:
        return self.load_treatments()

    def load_other_products(self) -> List[Dict[str, Any]]:
        return self.load_permanent_makeup()

    def load_use_cases(self) -> List[Dict[str, Any]]:
        return self.load_wellness()

    def load_general_info(self) -> str:
        """Load general company info from the data file."""
        if self._general_info_data is not None:
            return self._general_info_data

        file_path = os.path.join(self._get_data_dir(), "general_info", "general_info.txt")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Loaded general info from {file_path}")
            self._general_info_data = content
        except FileNotFoundError:
            logger.warning(f"General info file not found: {file_path}")
            self._general_info_data = ""
        except Exception as e:
            logger.error(f"Error loading general info: {e}")
            self._general_info_data = ""

        return self._general_info_data

    def load_faq(self) -> str:
        """Load FAQ from the data file."""
        if self._faq_data is not None:
            return self._faq_data

        file_path = os.path.join(self._get_data_dir(), "FAQ", "FAQ.txt")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Loaded FAQ from {file_path}")
            self._faq_data = content
        except FileNotFoundError:
            logger.warning(f"FAQ file not found: {file_path}")
            self._faq_data = ""
        except Exception as e:
            logger.error(f"Error loading FAQ: {e}")
            self._faq_data = ""

        return self._faq_data

    def _get_llm_context_dir(self) -> str:
        """Get the path to the LLM context directory."""
        return os.path.join(self._get_data_dir(), "llm-context")

    def _load_llm_context_file(self, filename: str, cache_attr: str) -> str:
        """Load and cache an LLM context file."""
        cached_value = getattr(self, cache_attr)
        if cached_value is not None:
            return cached_value

        file_path = os.path.join(self._get_llm_context_dir(), filename)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Loaded LLM context from {file_path}")
            setattr(self, cache_attr, content)
        except FileNotFoundError:
            logger.warning(f"LLM context file not found: {file_path}")
            setattr(self, cache_attr, "")
        except Exception as e:
            logger.error(f"Error loading LLM context: {e}")
            setattr(self, cache_attr, "")

        return getattr(self, cache_attr)

    def load_treatments_llm_context(self) -> str:
        """Load LLM-optimized treatment context."""
        return self._load_llm_context_file("treatments_llm.md", "_treatments_llm_context")

    def load_permanent_makeup_llm_context(self) -> str:
        """Load LLM-optimized permanent makeup context."""
        return self._load_llm_context_file("permanent_makeup_llm.md", "_permanent_makeup_llm_context")

    def load_wellness_llm_context(self) -> str:
        """Load LLM-optimized wellness context."""
        return self._load_llm_context_file("wellness_llm.md", "_wellness_llm_context")

    # Backward compatibility aliases for LLM context
    def load_nebular_llm_context(self) -> str:
        return self.load_treatments_llm_context()

    def load_other_llm_context(self) -> str:
        return self.load_permanent_makeup_llm_context()

    def load_use_cases_llm_context(self) -> str:
        return self.load_wellness_llm_context()

    def get_llm_context_by_category(self, category: str) -> str:
        """
        Get LLM-optimized context for a specific category.

        Args:
            category: 'treatments', 'permanent_makeup', or 'wellness'

        Returns:
            LLM-optimized markdown content for the category
        """
        if category in ("treatments", "nebular"):
            return self.load_treatments_llm_context()
        elif category in ("permanent_makeup", "other"):
            return self.load_permanent_makeup_llm_context()
        elif category in ("wellness", "use_cases"):
            return self.load_wellness_llm_context()
        else:
            logger.warning(f"Unknown LLM context category: {category}")
            return ""

    def get_all_products_json(self) -> Dict[str, Any]:
        """Get all treatments as a structured JSON object."""
        if self._all_products_json is not None:
            return self._all_products_json

        self._all_products_json = {
            "treatments": self.load_treatments(),
            "permanent_makeup": self.load_permanent_makeup(),
            "wellness": self.load_wellness(),
        }
        return self._all_products_json

    def search_products_by_name(self, query: str, min_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search treatments and services by name.

        - If user mentions a specific treatment: show matching first + random to fill
        - If no specific mention: return 5 random treatments
        """
        import random

        all_treatments = self.load_treatments() + self.load_permanent_makeup()
        all_wellness = self.load_wellness()
        all_items = all_treatments + all_wellness
        query_lower = query.lower()

        # Find matching items
        matching = []

        # Check treatments
        for product in all_treatments:
            name = product.get("name", "").lower()
            if query_lower in name or name in query_lower:
                matching.append(product)

        # Check wellness by name and title
        for item in all_wellness:
            name = item.get("name", "").lower()
            title = item.get("title", "").lower()
            if query_lower in name or name in query_lower or query_lower in title:
                matching.append(item)

        # Remove duplicates from matching
        matching = list({id(item): item for item in matching}.values())

        if matching:
            result = matching.copy()
            remaining = [item for item in all_items if item not in matching]
            random.shuffle(remaining)
            for item in remaining:
                if len(result) >= min_results:
                    break
                result.append(item)
        else:
            result = all_items.copy()
            random.shuffle(result)
            result = result[:min_results]

        return result

    def get_frontend_product(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a treatment or service to frontend format.
        Always returns images as a list.
        """
        category = item.get("category", "")

        if category == "wellness":
            return {
                "product_name": item.get("name", "Unknown"),
                "url": item.get("url", ""),
                "category": "wellness",
                "image": item.get("images", []),
            }
        elif category == "permanent_makeup":
            return {
                "product_name": item.get("name", "Unknown"),
                "url": item.get("url", ""),
                "category": "permanent_makeup",
                "image": item.get("images", []),
            }
        else:
            return {
                "product_name": item.get("name", "Unknown"),
                "url": item.get("url", ""),
                "category": category,
                "image": item.get("images", []),
            }

    def _fuzzy_match_product(self, mentioned: str, item_text: str, threshold: float = 0.7) -> bool:
        """
        Check if mentioned treatment matches item using fuzzy matching.
        Uses scoring: must match enough words to exceed threshold.

        Args:
            mentioned: The user-mentioned treatment name
            item_text: The treatment name from data
            threshold: Minimum match score (0.0-1.0) to consider a match

        Returns True if the match score exceeds threshold.
        """
        mentioned = mentioned.lower().strip()
        item_text = item_text.lower().strip()

        # Exact match - highest confidence
        if mentioned == item_text:
            return True

        # Substring match - high confidence
        if mentioned in item_text or item_text in mentioned:
            return True

        # Word-level scoring
        mentioned_words = mentioned.split()
        item_words = item_text.split()

        if not mentioned_words or not item_words:
            return False

        # Count how many significant words (3+ chars) from mentioned appear in item
        significant_words = [w for w in mentioned_words if len(w) >= 3]
        if not significant_words:
            significant_words = mentioned_words

        matched_words = 0
        for m_word in significant_words:
            for i_word in item_words:
                if m_word == i_word:
                    matched_words += 1
                    break
                if m_word in i_word or i_word in m_word:
                    matched_words += 1
                    break
                if len(m_word) >= 3 and i_word.startswith(m_word[:3]):
                    matched_words += 1
                    break

        match_score = matched_words / len(significant_words)

        return match_score >= threshold

    def get_products_by_category(self, category: str, query: str, mentioned_products: List[str], min_results: int = 5) -> List[Dict[str, Any]]:
        """
        Get treatments from a single category only.

        Args:
            category: 'treatments', 'permanent_makeup', or 'wellness'
            query: User's query
            mentioned_products: List of specifically mentioned treatments
            min_results: Minimum number of results to return

        Returns treatments only from the specified category.
        """
        import random

        # Get items from the specified category only
        if category in ("treatments", "nebular"):
            items = self.load_treatments()
        elif category in ("permanent_makeup", "other"):
            items = self.load_permanent_makeup()
        elif category in ("wellness", "use_cases"):
            items = self.load_wellness()
        else:
            items = self.load_treatments()

        if not items:
            items = self.load_treatments() or self.load_permanent_makeup() or self.load_wellness()

        query_lower = query.lower()
        mentioned_lower = [m.lower() for m in mentioned_products] if mentioned_products else []

        # Find matching items
        matching = []

        for item in items:
            name = item.get("name", "").lower()
            title = item.get("title", "").lower() if "title" in item else ""
            item_text = f"{name} {title}".strip()

            if any(self._fuzzy_match_product(m, item_text) for m in mentioned_lower):
                matching.append(item)
            elif query_lower in item_text or item_text in query_lower:
                matching.append(item)

        # Remove duplicates
        matching = list({id(item): item for item in matching}.values())

        if matching:
            result = matching.copy()
            remaining = [item for item in items if item not in matching]
            random.shuffle(remaining)
            for item in remaining:
                if len(result) >= min_results:
                    break
                result.append(item)
            return result[:min_results]
        else:
            result = items.copy()
            random.shuffle(result)
            return result[:min_results]


# =============================================================================
# DATA CLASSIFIER - Classifies messages to determine data categories
# =============================================================================

class DataClassifier:
    """Classifies user messages to determine which data categories are needed."""

    # Keywords for each category
    TREATMENTS_KEYWORDS = [
        "gesichtsbehandlung", "facial", "gesicht", "anti-aging", "reinigung",
        "hydration", "feuchtigkeit", "peeling", "körperbehandlung", "body",
        "fußpflege", "maniküre", "pediküre", "hautpflege", "körperpeeling",
        "body wrap", "wrapping", "behandlung", "kosmetik",
    ]

    PERMANENT_MAKEUP_KEYWORDS = [
        "permanent make-up", "permanent makeup", "pmu", "augenbrauen",
        "lippen", "eyeliner", "pigmentierung", "nachstechen",
        "microblading", "permanent",
    ]

    WELLNESS_KEYWORDS = [
        "massage", "entspannung", "wellness", "ganzkörper", "relaxen",
        "erholung", "körperpeeling", "ganzkörpermassage",
        "entspannungsmassage",
    ]

    # Backward compatibility
    NEBULAR_KEYWORDS = TREATMENTS_KEYWORDS
    OTHER_KEYWORDS = PERMANENT_MAKEUP_KEYWORDS
    USE_CASE_KEYWORDS = WELLNESS_KEYWORDS

    GENERAL_KEYWORDS = [
    ]

    FAQ_KEYWORDS = [
    ]

    def classify(self, message: str) -> List[str]:
        """
        Classify a message to determine which data categories are needed.

        Returns a list of category strings.
        """
        message_lower = message.lower()
        categories = []

        # Check for treatments
        if any(kw in message_lower for kw in self.TREATMENTS_KEYWORDS):
            categories.append(DataCategory.TREATMENTS)

        # Check for permanent makeup
        if any(kw in message_lower for kw in self.PERMANENT_MAKEUP_KEYWORDS):
            categories.append(DataCategory.PERMANENT_MAKEUP)

        # Check for wellness
        if any(kw in message_lower for kw in self.WELLNESS_KEYWORDS):
            categories.append(DataCategory.WELLNESS)

        # Check for general info
        if any(kw in message_lower for kw in self.GENERAL_KEYWORDS):
            categories.append(DataCategory.GENERAL)

        # Check for FAQ
        if any(kw in message_lower for kw in self.FAQ_KEYWORDS):
            categories.append(DataCategory.FAQ)

        # If no specific category found, return all for general search
        if not categories:
            categories.append(DataCategory.ALL)

        return categories


# =============================================================================
# GLOBAL INSTANCE - Singleton data loader
# =============================================================================

# Global data loader instance
data_loader = DataLoader()
