# settings.py
# Application settings — LLM, embedding, infrastructure, debug flags.
# Product metadata (filters, fields, mappings) lives in config/metadata.py.
# User-facing messages live in config/messages/.

import os
from dotenv import load_dotenv
load_dotenv()

# =============================================================================
# 1. LLM & EMBEDDING SETTINGS
# =============================================================================
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = 0.6
LLM_TEMPERATURE_WORKFLOW = 0.1  # Lower temperature for deterministic sub-agents
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")

# Realtime voice model (used by agents/base.py, agents/main_agent.py)
RT_MODEL = "gpt-realtime-mini-2025-10-06"

# =============================================================================
# 2. SMTP SETTINGS
# =============================================================================
SMTP_CONFIG = {
    "host": "smtp.gmail.com",
    "port": 587,
    "timeout": 10,
}

# =============================================================================
# 3. IMAGE CDN
# =============================================================================
IMAGE_CDN_BASE_URL = ""  # Placeholder — update when Beauty Lounge provides product images
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
IMAGE_COVER_PREFIX = "cover"

# =============================================================================
# 4. DEBUG & LOGGING
# =============================================================================
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
SAVE_CONVERSATION_HISTORY = True

# =============================================================================
# 5. DIRECTORIES
# =============================================================================
LOGS_DIR = "docs"                          # Directory for log files

# =============================================================================
# 6. WEBHOOK (session ingest)
# =============================================================================
WEBHOOK_URL = "https://ayand-log.vercel.app/api/webhooks/ingest"
WEBHOOK_API_KEY = os.getenv("INGEST_API_KEY")
WEBHOOK_TIMEOUT = 5                        # Seconds per attempt
WEBHOOK_RETRIES = 3                        # Number of retry attempts

# =============================================================================
# 7. FLASK STARTUP
# =============================================================================
FLASK_STARTUP_RETRIES = 20                 # Number of port-check attempts before warning
FLASK_STARTUP_INTERVAL = 0.5              # Seconds between port-check attempts
