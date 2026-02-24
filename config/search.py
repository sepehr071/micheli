"""
Search and product retrieval configuration.
Edit this file to customize search behavior, thresholds, and API settings.
"""
from dotenv import load_dotenv
import os
load_dotenv()
# =============================================================================
# SEARCH API — connection to the vector search service (Flask + Pinecone)
# =============================================================================

FLASK_PORT = os.getenv("PINECONE_PORT" , 5051)                                   # Port for the Flask search server
SEARCH_API_URL = f"http://localhost:{FLASK_PORT}/search"   # Flask search endpoint
SEARCH_TOP_K = 4                                  # Max products per search

# =============================================================================
# BEHAVIOR THRESHOLDS — control when features trigger
# =============================================================================

EXPERT_OFFER_SEARCH_GAP = 2     # Min searches between expert offers (prevent spam)
FILTER_RELAXATION_THRESHOLD = 2  # If fewer cars found, relax filters
BUDGET_ASK_BY_RESPONSE = 3      # Ask budget question at this response count

# =============================================================================
# HYBRID SEARCH TUNING — Pinecone dense/sparse weighting
# =============================================================================

HYBRID_SEARCH_ALPHA = 0.91      # Dense vs sparse weight (1.0 = pure dense, 0.0 = pure sparse)

# =============================================================================
# CONVERSATION LIMITS — control context window for search
# =============================================================================

BUDGET_SOFT_ASK_RESPONSE = 2    # Soft budget injection at this response count (before forced at BUDGET_ASK_BY_RESPONSE)
MAX_HISTORY_LOOKBACK = 20       # Max chat messages to consider for user message extraction
MAX_SEARCH_QUERY_MESSAGES = 5   # Max recent user messages joined as search query
