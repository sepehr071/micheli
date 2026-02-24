"""
Qualification agent questions and fallback values.
Multi-language support via config.translations module.

Used by: agents/qualification_agents.py, agents/email_agents.py, utils/smtp.py
"""

from config.translations import get_qualification_questions, get_fallback_not_provided


def get_qualification_questions_config():
    """
    Get qualification questions for the current language.

    Returns a dictionary of question strings in the current language.
    """
    return get_qualification_questions()


# For backward compatibility, also provide QUALIFICATION_QUESTIONS as a property
class QualificationQuestionsDict(dict):
    """Dictionary that returns qualification questions in the current language."""

    def __init__(self):
        super().__init__()
        self._update_from_current_language()

    def _update_from_current_language(self):
        questions = get_qualification_questions_config()
        self.clear()
        self.update(questions)

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


QUALIFICATION_QUESTIONS = QualificationQuestionsDict()


# =============================================================================
# FALLBACK / DEFAULT VALUES
# =============================================================================

def get_fallback_not_provided_config():
    """
    Get fallback "not provided" text for the current language.

    Returns a string to use when data is not provided.
    """
    return get_fallback_not_provided()


class FallbackNotProvidedWrapper:
    """
    Wrapper that provides language-specific fallback text.

    This class wraps the dynamic fallback text and provides:
    - String conversion (__str__) that returns current language's text
    - Truthiness evaluation (__bool__) that's always False
    - Compatibility with `or` operator in expressions like: `value or FALLBACK_NOT_PROVIDED`

    When used in string formatting (e.g., .format(), f-strings), __str__ is called
    automatically, returning the correct language-specific text.
    """

    def __str__(self) -> str:
        """Return the fallback text when converted to string."""
        return get_fallback_not_provided_config()

    def __repr__(self) -> str:
        """Return representation."""
        return f"'{self.__str__()}'"

    def __eq__(self, other) -> bool:
        """Check equality with string value."""
        return str(self) == other

    def __bool__(self) -> bool:
        """Make it falsy so `or` operators work correctly."""
        return False

    def __len__(self) -> int:
        """Return 0 to make it falsy in more contexts."""
        return 0

    # Make it behave like a string in as many contexts as possible
    def __add__(self, other):
        """Support string concatenation."""
        return str(self) + other

    def __radd__(self, other):
        """Support string concatenation (reversed)."""
        return other + str(self)

    def __format__(self, format_spec):
        """Support format() calls."""
        return str(self).__format__(format_spec)


FALLBACK_NOT_PROVIDED = FallbackNotProvidedWrapper()
