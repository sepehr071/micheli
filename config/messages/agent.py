"""
Agent response strings — what Lena says in various conversation situations.
Multi-language support via config.translations module.

Used by: agents/contact_agents.py, agents/email_agents.py, agents/main_agent.py
"""

from config.translations import get_agent_messages


def get_agent_messages_config():
    """
    Get agent messages for the current language.

    Returns a dictionary of all agent message strings in the current language.
    """
    return get_agent_messages()


# For backward compatibility, also provide AGENT_MESSAGES as a property
class AgentMessagesDict(dict):
    """Dictionary that returns agent messages in the current language."""

    def __init__(self):
        super().__init__()
        self._update_from_current_language()

    def _update_from_current_language(self):
        messages = get_agent_messages_config()
        self.clear()
        self.update(messages)

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


AGENT_MESSAGES = AgentMessagesDict()
