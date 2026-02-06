# Constants for EON Diceroller Bot
import os

# AI Model - override via .env: CLAUDE_MODEL=claude-sonnet-4-5-20250929
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

# User IDs
UMNATAK_ID = "680064176227352610"

# Dice limits
MAX_DICE = 100
MAX_SIDES = 1000
MAX_UNLIMITED_ROLLS = 1000

# Message limits
MAX_MESSAGE_LENGTH = 2000

# AI model limits
MAX_TOKENS = 1000
DEFAULT_SIMULATION_TRIALS = 10000

# Knowledge base settings
DEFAULT_TOP_K = 5

# Umnatak comments (will be loaded at runtime)
UMNATAK_SUCCESS_COMMENTS = []