"""
Service configuration — what the company offers to customers.
Multi-language support via config.translations module.

This module provides dynamic translations for:
- Expert titles
- Service options
- Qualification choices

All content is automatically translated based on the current language setting.
"""

from config.translations import get_services
from config.language import language_manager

# =============================================================================
# SERVICES — dynamically loaded based on current language
# =============================================================================

def get_services_config():
    """
    Get services configuration for the current language.

    Returns a dictionary with:
    - expert_title: Sales expert title
    - expert_title_alt: Alternate specialist advisor title
    - primary_service: Main service (test drive)
    - off_topic_redirect: Redirect message for off-topic questions
    - service_options: Post-qualification next steps
    - purchase_timing: Purchase timing options
    - reachability: Contact preference options
    """
    return get_services()


# For backward compatibility, also provide SERVICES as a property that gets current language
class ServicesDict(dict):
    """Dictionary that returns services in the current language."""

    def __init__(self):
        super().__init__()
        self._update_from_current_language()

    def _update_from_current_language(self):
        services = get_services_config()
        self.clear()
        self.update(services)

    def __getitem__(self, key):
        # Refresh on each access to get current language
        self._update_from_current_language()
        return super().__getitem__(key)

    def get(self, key, default=None):
        self._update_from_current_language()
        return super().get(key, default)

    def items(self):
        self._update_from_current_language()
        return super().items()

    def values(self):
        self._update_from_current_language()
        return super().values()

    def keys(self):
        self._update_from_current_language()
        return super().keys()


SERVICES = ServicesDict()

# =============================================================================
# REACHABILITY HELPERS
# =============================================================================
# These map language-specific keys to internal categories
# The internal category names stay constant, but the display values change

# Internal categories (language-independent)
REACHABILITY_CATEGORY_PHONE = "phone"    # Phone-based contact
REACHABILITY_CATEGORY_WHATSAPP = "whatsapp"  # WhatsApp contact
REACHABILITY_CATEGORY_EMAIL = "email"    # Email contact

# Language-specific key mappings (for backward compatibility with existing code)
REACHABILITY_KEY_MAPS = {
    "en": {
        "phone_today": REACHABILITY_CATEGORY_PHONE,
        "whatsapp_today": REACHABILITY_CATEGORY_WHATSAPP,
        "email_week": REACHABILITY_CATEGORY_EMAIL,
    },
    "de": {
        "telefon_heute": REACHABILITY_CATEGORY_PHONE,
        "whatsapp_heute": REACHABILITY_CATEGORY_WHATSAPP,
        "email_woche": REACHABILITY_CATEGORY_EMAIL,
    },
    "tr": {
        "phone_today": REACHABILITY_CATEGORY_PHONE,
        "whatsapp_today": REACHABILITY_CATEGORY_WHATSAPP,
        "email_week": REACHABILITY_CATEGORY_EMAIL,
    },
    "es": {
        "phone_today": REACHABILITY_CATEGORY_PHONE,
        "whatsapp_today": REACHABILITY_CATEGORY_WHATSAPP,
        "email_week": REACHABILITY_CATEGORY_EMAIL,
    },
    "fr": {
        "phone_today": REACHABILITY_CATEGORY_PHONE,
        "whatsapp_today": REACHABILITY_CATEGORY_WHATSAPP,
        "email_week": REACHABILITY_CATEGORY_EMAIL,
    },
    "it": {
        "phone_today": REACHABILITY_CATEGORY_PHONE,
        "whatsapp_today": REACHABILITY_CATEGORY_WHATSAPP,
        "email_week": REACHABILITY_CATEGORY_EMAIL,
    },
    "pt": {
        "phone_today": REACHABILITY_CATEGORY_PHONE,
        "whatsapp_today": REACHABILITY_CATEGORY_WHATSAPP,
        "email_week": REACHABILITY_CATEGORY_EMAIL,
    },
    "nl": {
        "phone_today": REACHABILITY_CATEGORY_PHONE,
        "whatsapp_today": REACHABILITY_CATEGORY_WHATSAPP,
        "email_week": REACHABILITY_CATEGORY_EMAIL,
    },
    "pl": {
        "phone_today": REACHABILITY_CATEGORY_PHONE,
        "whatsapp_today": REACHABILITY_CATEGORY_WHATSAPP,
        "email_week": REACHABILITY_CATEGORY_EMAIL,
    },
    "ar": {
        "phone_today": REACHABILITY_CATEGORY_PHONE,
        "whatsapp_today": REACHABILITY_CATEGORY_WHATSAPP,
        "email_week": REACHABILITY_CATEGORY_EMAIL,
    },
}


# For backward compatibility: Derived reachability groups
# These are now computed based on current language
def get_reachability_phone_keys():
    """Get phone-related reachability keys for current language."""
    lang = language_manager.get_language()
    if lang == "de":
        return ["telefon_heute", "whatsapp_heute"]
    return ["phone_today", "whatsapp_today"]


def get_reachability_email_keys():
    """Get email-related reachability keys for current language."""
    lang = language_manager.get_language()
    if lang == "de":
        return ["email_woche"]
    return ["email_week"]
