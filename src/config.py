"""
Configuration and constants for the music survey visualization app.
Centralizes hardcoded values to avoid duplication across modules.
"""

# ============================================================================
# SPREADSHEET CONFIGURATION
# ============================================================================

SPREADSHEET_CONFIG = {
    2024: "What was 2024 about - responses",
    2023: "What was 2023 about - responses",
    2019: "What was 2019 about - responses",
}

# Legacy data stored in a single multi-sheet spreadsheet
LEGACY_SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1ggWt0Pbpb47qR8XcdUEs7mYxifXh9jY67wEss7hbtsY"

SUPPORTED_YEARS = [2024, 2023, 2019]
DEFAULT_YEAR = 2024

# ============================================================================
# UI CONFIGURATION
# ============================================================================

RANKING_VIEW_MAPPING = {
    "Final score + your score (overlay)": "overlay",
    "Only final score": "average",
    "Only your scores": "user",
}

RANKING_VIEW_CHOICES = list(RANKING_VIEW_MAPPING.keys())
DEFAULT_RANKING_VIEW = "overlay"

# ============================================================================
# LLM MODEL CONFIGURATION
# ============================================================================

LLM_MODELS = {
    "blurb": {
        "name": "MODEL_BLURB",
        "default": "llama-3.1-8b-instant",
        "description": "Short summaries",
    },
    "analysis": {
        "name": "MODEL_ANALYSIS",
        "default": "openai/gpt-oss-120b",
        "description": "User voting patterns analysis",
    },
    "json": {
        "name": "MODEL_JSON",
        "default": "moonshotai/kimi-k2-instruct",
        "description": "Structured recommendations",
    },
}

# ============================================================================
# CONSTRAINTS & LIMITS
# ============================================================================

LLM_ANALYSIS_MIN_WORDS = 250
LLM_ANALYSIS_MAX_WORDS = 300
LLM_RECOMMENDATION_COUNT = 5

CACHE_MAX_SIZE = 10
CACHE_TTL_SECONDS = 3600  # 1 hour

# ============================================================================
# DATA PROCESSING
# ============================================================================

SONG_SCORE_MIN_THRESHOLD = 1
SONG_SCORE_MAX = 10
SONG_COLUMNS_START_INDEX = 2  # After Timestamp and Email columns

# ============================================================================
# FILE PATHS
# ============================================================================

from pathlib import Path  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = Path(__file__).resolve().parent
CREDENTIALS_PATH = BASE_DIR / "credentials.json"
FEEDBACK_LOG_PATH = BASE_DIR / "feedback_log.txt"
STATIC_DIR = BASE_DIR / "static"
HEADER_IMAGE = STATIC_DIR / "header.png"

# ============================================================================
# FEEDBACK CONFIGURATION
# ============================================================================

FEEDBACK_RECEIVER_EMAIL = "maravasku@gmail.com"
FEEDBACK_SUBMISSION_TIMEOUT = 10  # seconds

# ============================================================================
# CLUSTERING
# ============================================================================

CLUSTERING_METHOD = "kmeans"
CLUSTERING_N_CLUSTERS = 3
DIMENSIONALITY_REDUCTION_METHOD = "tsne"
STANDARDIZE_FEATURES = True
