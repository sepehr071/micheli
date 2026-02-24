"""
UI button payloads — button labels and values shown to the customer.
Multi-language support via config.translations module.

Used by: agents/email_agents.py, agents/main_agent.py
"""

from config.translations import get_ui_buttons


def get_ui_buttons_config():
    """
    Get UI buttons configuration for the current language.

    Args:
        button_type: Type of buttons to retrieve (optional, returns all if not specified)

    Returns:
        If button_type specified: Dictionary of buttons for that type
        If not specified: Dictionary of all button types
    """
    # For backward compatibility, this function can return all button types
    # or a specific type based on how it's called
    return {
        "expert_offer": get_ui_buttons("expert_offer"),
        "appointment_confirm": get_ui_buttons("appointment_confirm"),
        "summary_offer": get_ui_buttons("summary_offer"),
        "new_conversation": get_ui_buttons("new_conversation"),
    }


# For backward compatibility, also provide UI_BUTTONS as a property
class UIButtonsDict(dict):
    """Dictionary that returns UI buttons in the current language."""

    def __init__(self):
        super().__init__()
        self._update_from_current_language()

    def _update_from_current_language(self):
        buttons = get_ui_buttons_config()
        self.clear()
        self.update(buttons)

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


UI_BUTTONS = UIButtonsDict()
