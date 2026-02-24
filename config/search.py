"""
Search and product retrieval configuration.
Edit this file to customize search behavior and thresholds.
Since we use local data files instead of RAG/Pinecone, Flask-related settings have been removed.
"""

# =============================================================================
# SEARCH SETTINGS — local data retrieval
# =============================================================================

SEARCH_TOP_K = 5                                   # Max products per search
MAX_PRODUCTS_TO_DISPLAY = 5                        # Max products to show in frontend

# =============================================================================
# BEHAVIOR THRESHOLDS — control when features trigger
# =============================================================================

EXPERT_OFFER_SEARCH_GAP = 2     # Min searches between expert offers (prevent spam)
FILTER_RELAXATION_THRESHOLD = 2  # If fewer products found, relax filters
BUDGET_ASK_BY_RESPONSE = 3      # Ask budget question at this response count

# =============================================================================
# CONVERSATION LIMITS — control context window for search
# =============================================================================

BUDGET_SOFT_ASK_RESPONSE = 2    # Soft budget injection at this response count (before forced at BUDGET_ASK_BY_RESPONSE)
MAX_HISTORY_LOOKBACK = 20       # Max chat messages to consider for user message extraction
MAX_SEARCH_QUERY_MESSAGES = 5   # Max recent user messages joined as search query

# =============================================================================
# DATA FILE PATHS — paths to local data files
# =============================================================================

DATA_DIR = "data"
TREATMENTS_FILE = f"{DATA_DIR}/beauty-services/treatments/treatments.txt"
PERMANENT_MAKEUP_FILE = f"{DATA_DIR}/beauty-services/permanent-makeup/permanent-makeup.txt"
WELLNESS_FILE = f"{DATA_DIR}/beauty-services/wellness/wellness.txt"
GENERAL_INFO_FILE = f"{DATA_DIR}/general_info/general_info.txt"
FAQ_FILE = f"{DATA_DIR}/FAQ/FAQ.txt"
