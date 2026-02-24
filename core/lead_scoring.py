"""
Buying signal detection and lead degree scoring.
Pure functions — no side effects, no agent dependencies.

Used by: agents/main_agent.py, agents/email_agents.py
"""

import math
import logging
from typing import Optional
from config.signals import (
    HOT_SIGNALS, WARM_SIGNALS, COOL_SIGNALS,
    SIGNAL_SCORING, LEAD_SCORING,
)

logger = logging.getLogger(__name__)


def detect_buying_signals(user_message: str, search_count: int) -> dict:
    """
    Analyze user message for buying intent signals.
    Returns signal level (HOT/WARM/MILD/COOL) and confidence score.
    """
    message_lower = user_message.lower()
    s = SIGNAL_SCORING

    # Match keywords
    hot_matched = [kw for kw in HOT_SIGNALS if kw in message_lower]
    warm_matched = [kw for kw in WARM_SIGNALS if kw in message_lower]
    cool_matched = [kw for kw in COOL_SIGNALS if kw in message_lower]

    hot_count = len(hot_matched)
    warm_count = len(warm_matched)
    cool_count = len(cool_matched)

    # Determine level
    if hot_count > 0:
        level = "HOT"
        confidence = min(1.0, s["hot_base"] + (hot_count * s["hot_increment"]))
    elif warm_count > 0 or search_count >= 1:
        level = "WARM"
        confidence = min(1.0, s["warm_base"] + (warm_count * s["warm_increment"]) + (search_count * s["warm_search_increment"]))
    elif cool_count > 0:
        level = "COOL"
        confidence = s["cool_confidence"]
    else:
        level = "MILD"
        confidence = s["mild_base"] + (search_count * s["mild_search_increment"])

    logger.debug(f"Signal detection: {level} (conf={confidence:.1%}) hot={hot_matched} warm={warm_matched} cool={cool_matched}")

    return {
        "level": level,
        "confidence": confidence,
        "hot_signals": hot_count,
        "warm_signals": warm_count,
        "cool_signals": cool_count,
        "search_count": search_count,
        "hot_matched": hot_matched,
        "warm_matched": warm_matched,
        "cool_matched": cool_matched,
    }


def calculate_lead_degree(
    hot_count: int,
    warm_count: int,
    cool_count: int,
    search_count: int,
    products_shown: int,
    purchase_timing: Optional[str],
    next_step: Optional[str],
    reachability: Optional[str],
    message_length: int = 50,
) -> dict:
    """
    ML-style lead scoring (0-10).
    Returns dict with score, confidence, and breakdown.
    """
    ls = LEAD_SCORING

    # Factor 1: Intent Signal (0-3.0)
    hot_score = min(ls["hot_cap"], hot_count * ls["hot_weight"])
    warm_score = min(ls["warm_cap"], warm_count * ls["warm_weight"])
    cool_penalty = cool_count * ls["cool_penalty"]
    intent_raw = max(0, hot_score + warm_score + cool_penalty)
    intent_confidence = min(1.0, message_length / ls["intent_confidence_divisor"])
    intent_score = intent_raw * (0.7 + 0.3 * intent_confidence)

    # Factor 2: Engagement (0-2.5)
    search_score = min(ls["search_cap"], math.log(1 + search_count) * ls["search_log_weight"])
    products_score = min(ls["products_cap"], products_shown * ls["products_weight"])
    engagement_score = search_score + products_score

    # Factor 3: Qualification (0-3.5)
    timing_score = ls["timing_scores"].get(purchase_timing, ls["timing_default"])
    step_score = ls["step_scores"].get(next_step, ls["step_default"])

    synergy = 0.0
    for rule in ls["synergy_rules"]:
        if purchase_timing == rule["timing"] and next_step == rule["step"]:
            synergy = rule["bonus"]
            break

    qualification_score = timing_score + step_score + synergy

    # Factor 4: Accessibility (0-1.0)
    accessibility_score = ls["reach_scores"].get(reachability, ls["reach_default"])

    # Final calculation
    raw_score = intent_score + engagement_score + qualification_score + accessibility_score

    data_points = sum([
        1 if purchase_timing else 0,
        1 if next_step else 0,
        1 if reachability else 0,
        1 if search_count > 0 else 0,
    ])
    confidence = ls["base_confidence"] + (data_points * ls["per_data_point"])

    final_score = round(min(10.0, raw_score * confidence), 1)

    logger.debug(
        f"Lead degree: {final_score}/10 "
        f"(intent={intent_score:.2f} engagement={engagement_score:.2f} "
        f"qualification={qualification_score:.2f} accessibility={accessibility_score:.2f})"
    )

    return {
        "score": final_score,
        "confidence": round(confidence * 100),
        "breakdown": {
            "intent": round(intent_score, 2),
            "engagement": round(engagement_score, 2),
            "qualification": round(qualification_score, 2),
            "accessibility": round(accessibility_score, 2),
        },
    }
