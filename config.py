"""
Configuration settings for the 5v5 Scrims Bot
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for bot settings"""

    # Discord Bot Settings
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    BOT_PREFIX = os.getenv("BOT_PREFIX", "!")
    GUILD_ID = int(os.getenv("GUILD_ID")) if os.getenv("GUILD_ID") else None

    # Database Settings
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_NAME = os.getenv("DB_NAME", "scrims_bot")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    # Channel IDs
    SCRIMS_QUEUE_CHANNEL = int(os.getenv("SCRIMS_QUEUE_CHANNEL")) if os.getenv("SCRIMS_QUEUE_CHANNEL") else None
    SCRIM_HISTORY_CHANNEL = int(os.getenv("SCRIM_HISTORY_CHANNEL")) if os.getenv("SCRIM_HISTORY_CHANNEL") else None
    SCRIM_CATEGORY = int(os.getenv("SCRIM_CATEGORY")) if os.getenv("SCRIM_CATEGORY") else None

    # Game Settings
    QUEUE_SIZE = int(os.getenv("QUEUE_SIZE", 10))
    POINTS_WIN = int(os.getenv("POINTS_WIN", 30))
    POINTS_LOSS = int(os.getenv("POINTS_LOSS", -30))
    POINTS_MVP = int(os.getenv("POINTS_MVP", 10))
    STARTING_POINTS = int(os.getenv("STARTING_POINTS", 1000))

    # Timeout Settings
    TIMEOUT_MINUTES = int(os.getenv("TIMEOUT_MINUTES", 30))
    NO_PROOF_PENALTY = int(os.getenv("NO_PROOF_PENALTY", 100))
    PROOF_TIMEOUT_MINUTES = int(os.getenv("PROOF_TIMEOUT_MINUTES", 30))

    # Rank Settings
    RANK_ROLES_ENABLED = os.getenv("RANK_ROLES_ENABLED", "true").lower() == "true"

    # Rank thresholds and role names
    RANK_THRESHOLDS = {
        "BRONZE": 0,
        "SILVER": 600,
        "GOLD": 1000,
        "PLATINUM": 1200,
        "DIAMOND": 1500,
        "ASCENDANT": 1800,
        "IMMORTAL": 2200,
        "RADIANT": float('inf')  # Top 5 players
    }

    RANK_ROLE_NAMES = {
        "BRONZE": "🟤 Bronze",
        "SILVER": "⚪ Silver", 
        "GOLD": "🟡 Gold",
        "PLATINUM": "🟦 Platinum",
        "DIAMOND": "💎 Diamond",
        "ASCENDANT": "🟢 Ascendant",
        "IMMORTAL": "🔥 Immortal",
        "RADIANT": "🌟 Radiant"
    }

    RANK_COLORS = {
        "BRONZE": 0x8B4513,
        "SILVER": 0xC0C0C0,
        "GOLD": 0xFFD700,
        "PLATINUM": 0x4169E1,
        "DIAMOND": 0x00CED1,
        "ASCENDANT": 0x00FF00,
        "IMMORTAL": 0xFF4500,
        "RADIANT": 0xFF1493
    }

    # Embed Colors
    COLOR_SUCCESS = 0x00FF00
    COLOR_ERROR = 0xFF0000
    COLOR_WARNING = 0xFFFF00
    COLOR_INFO = 0x0099FF
    COLOR_QUEUE = 0x7289DA
    COLOR_MATCH = 0xF1C40F

    # Emojis
    EMOJI_JOIN = "🟢"
    EMOJI_LEAVE = "🔴"
    EMOJI_DRAFT = "🎯"
    EMOJI_LOBBY = "📌"
    EMOJI_CANCEL = "❌"
    EMOJI_VOTE_WIN = "✅"
    EMOJI_MVP = "🌟"
    EMOJI_PROOF = "📸"

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_vars = [
            "DISCORD_TOKEN",
            "DB_PASSWORD"
        ]

        missing = []
        for var in required_vars:
            if not getattr(cls, var):
                missing.append(var)

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        return True

    @classmethod
    def get_database_url(cls):
        """Get PostgreSQL database URL"""
        return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
