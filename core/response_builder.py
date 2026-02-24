"""
LLM response assembly — build signal-aware instructions and budget tracking.
Extracted from BertaAssistant to keep the main agent file focused on orchestration.

Used by: agents/main_agent.py
"""

import logging
from config.search import BUDGET_ASK_BY_RESPONSE, BUDGET_SOFT_ASK_RESPONSE
from config.messages import (
    SIGNAL_INSTRUCTIONS,
    EXPERT_QUESTION_INSTRUCTION,
    SEARCH_RESPONSE_TEMPLATE,
    CONVERSATION_RULES,
    BUDGET_INJECTIONS,
)

logger = logging.getLogger(__name__)


def build_lead_instruction(
    signal_level: str,
    can_offer_expert: bool,
    expert_phrase: str,
    expert_accepted: bool,
) -> str:
    """Build signal-aware lead instruction block for LLM."""
    if expert_accepted:
        return SIGNAL_INSTRUCTIONS["expert_accepted"]

    if signal_level == "HOT":
        if can_offer_expert:
            return SIGNAL_INSTRUCTIONS["hot_with_expert"].format(expert_phrase=expert_phrase)
        return SIGNAL_INSTRUCTIONS["hot_no_expert"]

    if signal_level == "WARM":
        if can_offer_expert:
            return SIGNAL_INSTRUCTIONS["warm_with_expert"].format(expert_phrase=expert_phrase)
        return SIGNAL_INSTRUCTIONS["warm_no_expert"]

    if signal_level == "COOL":
        return SIGNAL_INSTRUCTIONS["cool"]

    # MILD
    if can_offer_expert:
        return SIGNAL_INSTRUCTIONS["mild_with_expert"].format(expert_phrase=expert_phrase)
    return SIGNAL_INSTRUCTIONS["mild_no_expert"]


def build_expert_question_instruction(pending_expert_buttons: bool) -> str:
    """Build explicit instruction when Ja/Nein buttons will appear."""
    if not pending_expert_buttons:
        return ""

    return EXPERT_QUESTION_INSTRUCTION


def build_search_response(
    result: list,
    metadata_filters: dict,
    classification_info: str,
    skip_questions_hint: str,
    filter_explanation: str,
    signal_level: str,
    conversation_context: dict,
    match_analysis: dict,
    lead_instruction: str,
    expert_question_instruction: str,
    budget_question_instruction: str,
) -> str:
    """Assemble the full LLM instruction string for search results."""
    return SEARCH_RESPONSE_TEMPLATE.format(
        result=str(result),
        metadata_filters=str(metadata_filters),
        classification_info=classification_info,
        skip_questions_hint=skip_questions_hint,
        filter_explanation=filter_explanation,
        signal_level=signal_level,
        search_number=conversation_context['search_number'],
        cars_found=conversation_context['cars_found'],
        match_status=match_analysis['status'],
        lead_instruction=lead_instruction,
        expert_question_instruction=expert_question_instruction,
        budget_question_instruction=budget_question_instruction,
    ) + CONVERSATION_RULES


class BudgetTracker:
    """Tracks budget question state and injection logic."""

    def is_budget_known(self, userdata) -> bool:
        return bool(
            userdata.filter_preferences.numeric.get("max_price")
            or userdata.filter_preferences.numeric.get("min_price")
        )

    def should_ask_budget(self, userdata) -> bool:
        if self.is_budget_known(userdata):
            return False
        if userdata.budget_asked:
            return False
        return True

    def must_ask_budget_now(self, userdata) -> bool:
        return (
            userdata.response_count >= BUDGET_ASK_BY_RESPONSE
            and self.should_ask_budget(userdata)
        )

    def get_budget_injection(self, userdata, context: str, force: bool = False) -> str:
        if force:
            return BUDGET_INJECTIONS["forced"]

        return BUDGET_INJECTIONS.get(context, BUDGET_INJECTIONS["vague"])

    def get_search_budget_instruction(self, userdata) -> str:
        """Get budget injection for search context. Returns empty string if not needed."""
        if not self.should_ask_budget(userdata):
            return ""

        if self.must_ask_budget_now(userdata):
            userdata.budget_asked = True
            logger.debug(f"FORCED budget question at response #{userdata.response_count}")
            return self.get_budget_injection(userdata, "search_results", force=True)

        if userdata.response_count == BUDGET_SOFT_ASK_RESPONSE:
            userdata.budget_asked = True
            logger.debug(f"Injecting budget question at response #{userdata.response_count}")
            return self.get_budget_injection(userdata, "search_results")

        return ""
