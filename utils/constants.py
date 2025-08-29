"""
Constants for the 5v5 Scrims Bot
"""

from config import Config

# Match constants
MAX_MATCH_DURATION_HOURS = 2
PROOF_UPLOAD_TIMEOUT_MINUTES = 30
DRAFT_TIMEOUT_MINUTES = 10
LOBBY_CREATION_TIMEOUT_MINUTES = 15

# Pagination constants
LEADERBOARD_PER_PAGE = 10
HISTORY_PER_PAGE = 5

# Rate limiting
COMMAND_COOLDOWN_SECONDS = 3
ADMIN_COMMAND_COOLDOWN_SECONDS = 1

# Embed limits
MAX_EMBED_DESCRIPTION_LENGTH = 2048
MAX_EMBED_FIELD_LENGTH = 1024
MAX_EMBED_TITLE_LENGTH = 256

# Queue constants
MIN_QUEUE_SIZE = 4
MAX_QUEUE_SIZE = 20

# Points constants
MIN_POINTS = 0
MAX_POINTS = 10000

# Timeout constants
MIN_TIMEOUT_MINUTES = 1
MAX_TIMEOUT_MINUTES = 1440  # 24 hours

# Match ID generation
MATCH_ID_LENGTH = 3
MATCH_ID_PREFIX = "#"

# File upload limits
MAX_SCREENSHOT_SIZE_MB = 10
ALLOWED_IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.webp']

# Team constants
TEAM_SIZE = 5
NUM_TEAMS = 2

# Status messages
STATUS_MESSAGES = {
    "queue_join_success": "✅ You've joined the queue!",
    "queue_leave_success": "✅ You've left the queue!",
    "queue_already_in": "⚠️ You're already in the queue!",
    "queue_not_in": "⚠️ You're not in the queue!",
    "queue_full": "❌ The queue is full!",
    "queue_timeout": "⏰ You're currently timed out!",
    "match_not_found": "❌ Match not found!",
    "insufficient_permissions": "❌ You don't have permission to do that!",
    "invalid_team": "❌ Invalid team selection!",
    "invalid_player": "❌ Invalid player selection!",
    "match_already_completed": "❌ This match is already completed!",
    "screenshot_required": "📸 Screenshot proof is required!",
    "screenshot_uploaded": "✅ Screenshot uploaded successfully!",
    "match_cancelled": "❌ Match has been cancelled!",
    "match_completed": "✅ Match completed successfully!",
    "lobby_id_set": "✅ Lobby ID has been set!",
    "invalid_lobby_id": "❌ Invalid lobby ID format!",
    "mvp_voted": "🌟 MVP vote recorded!",
    "winner_voted": "🏆 Winner vote recorded!",
    "timeout_applied": "⏰ Timeout has been applied!",
    "timeout_removed": "✅ Timeout has been removed!",
    "config_updated": "⚙️ Configuration updated!",
    "points_updated": "💰 Points updated!",
    "database_error": "❌ Database error occurred!",
    "unknown_error": "❌ An unknown error occurred!",
    "cooldown_active": "⏰ Command is on cooldown!",
}

# Help text
HELP_TEXT = """
## 📘 5v5 Scrims Bot Commands

### Player Commands
• **Join Queue** - Click the 🟢 button to join the scrim queue
• **Leave Queue** - Click the 🔴 button to leave the queue
• `/stats` - View your personal statistics
• `/leaderboard` - View the points leaderboard
• `/history` - View recent match history

### Match Commands (Leaders Only)
• **Draft Players** - Click player buttons during drafting phase
• **Share Lobby ID** - Set the custom game lobby ID
• **Vote Winner** - Vote for the winning team after match
• **Select MVP** - Choose the MVP player
• **Upload Proof** - Upload screenshot proof of match results

### Admin Commands
• `/config` - View/modify bot configuration
• `/points` - Manage player points
• `/timeout` - Manage player timeouts  
• `/scrim` - Force match actions
• `/leaderboard reset` - Reset leaderboard
• `/history clear` - Clear match history

### Queue System
1. Players join the queue until it fills (default: 10 players)
2. Bot creates private scrim channel for those 10 players
3. Two leaders are randomly selected
4. Drafting phase begins with alternating picks
5. Leader B creates custom lobby and shares ID
6. Match is played externally
7. Leaders vote on winner and MVP
8. Winning leader uploads screenshot proof
9. Points are awarded and ranks updated

### Ranking System
🟤 **Bronze** - 0+ points
⚪ **Silver** - 600+ points  
🟡 **Gold** - 1000+ points
🟦 **Platinum** - 1200+ points
💎 **Diamond** - 1500+ points
🟢 **Ascendant** - 1800+ points
🔥 **Immortal** - 2200+ points
🌟 **Radiant** - Top 5 players

### Point System
• **Win**: +30 points
• **Loss**: -30 points  
• **MVP**: +10 points
• **AFK/Timeout**: 30 minute queue ban
• **No Proof**: -100 points to both leaders

Need help? Contact an administrator!
"""

# Error messages for logging
LOG_MESSAGES = {
    "database_connection_failed": "Failed to connect to database",
    "cog_load_failed": "Failed to load cog: {cog}",
    "command_error": "Command error in {command}: {error}",
    "match_creation_failed": "Failed to create match: {error}",
    "player_creation_failed": "Failed to create player: {error}",
    "queue_update_failed": "Failed to update queue: {error}",
    "config_update_failed": "Failed to update config: {error}",
    "webhook_error": "Webhook error: {error}",
    "permission_error": "Permission error: {error}",
    "rate_limit_error": "Rate limit error: {error}",
}

# Regex patterns  
LOBBY_ID_PATTERN = r'^[A-Z0-9]{4,10}$'  # Custom lobby ID format
DISCORD_MESSAGE_URL_PATTERN = r'https://discord(?:app)?\.com/channels/\d+/\d+/\d+'
DISCORD_IMAGE_URL_PATTERN = r'https://cdn\.discord(?:app)?\.com/attachments/\d+/\d+/.+\.(png|jpg|jpeg|gif|webp)'

# Time constants
SECONDS_IN_MINUTE = 60
MINUTES_IN_HOUR = 60
HOURS_IN_DAY = 24
SECONDS_IN_HOUR = SECONDS_IN_MINUTE * MINUTES_IN_HOUR
SECONDS_IN_DAY = SECONDS_IN_HOUR * HOURS_IN_DAY

# Bot permissions required
REQUIRED_PERMISSIONS = [
    'send_messages',
    'embed_links', 
    'attach_files',
    'read_message_history',
    'manage_messages',
    'create_private_threads',
    'manage_threads',
    'manage_roles',
    'manage_channels'
]

# Channel names
TEMP_CHANNEL_NAME_FORMAT = "scrim-{match_id}"
TEMP_CHANNEL_TOPIC_FORMAT = "🎮 5v5 Scrim Match {match_id} | Leaders: {leader1} vs {leader2}"
