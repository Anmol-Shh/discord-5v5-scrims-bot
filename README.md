# 📘 5v5 Scrims Discord Bot

A comprehensive Discord bot for managing competitive 5v5 scrimmage matches with queue management, team drafting, match tracking, and ranking systems.

## 🎯 Features

### Core Functionality
- **Queue Management** - Dynamic queue system with join/leave buttons
- **Team Drafting** - Snake draft system showing player scores  
- **Random Leader Assignment** - One creates lobby, other gets first pick
- **Private Match Channels** - Temporary channels for each match
- **Post-Game Voting** - Winner and MVP selection by leaders
- **Screenshot Proof System** - Required match verification
- **Points & Ranking System** - Competitive progression tracking
- **Match History Logging** - Complete game records
- **Leaderboards** - Paginated player rankings
- **AFK/Timeout System** - Automatic penalties for no-shows
- **Automatic Rank Roles** - Bronze → Radiant progression
- **Admin Configuration** - Extensive customization via slash commands

### Advanced Features
- **PostgreSQL Database** - Robust data storage with connection pooling
- **Docker Deployment** - Container-ready with docker-compose
- **Comprehensive Statistics** - Player analytics and match tracking
- **Permission Management** - Role-based command access
- **Error Handling** - Graceful error recovery and logging
- **Rate Limiting** - Prevents spam and abuse
- **Modular Architecture** - Clean cog-based organization

## 🚀 Quick Start

### Prerequisites
- **Python 3.12+**
- **PostgreSQL 15+** (or use Docker)
- **Discord Bot Token** with required permissions
- **Docker & Docker Compose** (for containerized deployment)

### Discord Bot Setup

1. **Create Discord Application**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create new application → Bot section
   - Copy bot token and save securely
   - Enable all Privileged Gateway Intents

2. **Invite Bot to Server**
   - Generate invite URL with these permissions:
     - Send Messages
     - Embed Links  
     - Attach Files
     - Read Message History
     - Manage Messages
     - Manage Channels
     - Manage Roles
     - Use Slash Commands
   - Select `bot` and `applications.commands` scopes

3. **Server Setup**
   - Create channels for queue and match history
   - Create category for temporary match channels
   - Note down channel/category IDs (Enable Developer Mode)

### Installation

#### Option 1: Docker Deployment (Recommended)

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd discord_5v5_scrims_bot
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env file with your settings
   ```

3. **Start Services**
   ```bash
   docker-compose up -d
   ```

4. **View Logs**
   ```bash
   docker-compose logs -f scrims_bot
   ```

#### Option 2: Manual Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup PostgreSQL**
   - Install PostgreSQL 15+
   - Create database: `CREATE DATABASE scrims_bot;`
   - Create user with permissions

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Run Bot**
   ```bash
   python main.py
   ```

### Initial Bot Configuration

1. **Setup Queue Channel**
   ```
   /queue
   ```
   Run this command in your desired queue channel (requires Manage Messages permission)

2. **Configure Bot Settings** (optional)
   ```
   /config show                    # View current settings
   /config set points_win 30       # Set win points  
   /config set queue_size 10       # Set queue size
   /config set rank_roles_enabled true
   ```

3. **Test Bot**
   - Use `/help` to view all commands
   - Try joining/leaving queue with buttons
   - Check `/permissions` for any missing perms

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_TOKEN` | Bot token from Discord Developer Portal | **Required** |
| `DB_PASSWORD` | PostgreSQL password | **Required** |
| `BOT_PREFIX` | Command prefix for legacy commands | `!` |
| `GUILD_ID` | Main guild ID for testing | Optional |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `DB_NAME` | Database name | `scrims_bot` |
| `DB_USER` | Database user | `postgres` |
| `SCRIMS_QUEUE_CHANNEL` | Queue channel ID | Optional |
| `SCRIM_HISTORY_CHANNEL` | History channel ID | Optional |
| `SCRIM_CATEGORY` | Match category ID | Optional |
| `QUEUE_SIZE` | Players needed for match | `10` |
| `POINTS_WIN` | Points for winning | `30` |
| `POINTS_LOSS` | Points lost for losing | `-30` |
| `POINTS_MVP` | Bonus points for MVP | `10` |
| `STARTING_POINTS` | New player starting points | `1000` |
| `TIMEOUT_MINUTES` | AFK timeout duration | `30` |
| `NO_PROOF_PENALTY` | Penalty for no screenshot | `100` |
| `PROOF_TIMEOUT_MINUTES` | Time to upload proof | `30` |
| `RANK_ROLES_ENABLED` | Auto-assign rank roles | `true` |

### In-Bot Configuration

Use `/config set <setting> <value>` to modify:

- **Point System**: `points_win`, `points_loss`, `points_mvp`
- **Timeouts**: `timeout_minutes`, `proof_timeout_minutes`, `no_proof_penalty`  
- **Match Settings**: `queue_size`, `rank_roles_enabled`

## 🎮 How to Use

### For Players

1. **Join Queue**
   - Go to the queue channel
   - Click 🟢 **Join Queue** button
   - Wait for queue to fill (default: 10 players)

2. **Match Flow**
   - Bot creates private match channel
   - Two random leaders are selected
   - Leaders draft teams alternately
   - Leader B creates custom game lobby
   - All players join lobby and play match
   - Leaders vote on winner and MVP
   - Winning leader uploads screenshot proof

3. **View Stats**
   - `/stats` - Your personal statistics
   - `/leaderboard` - Points leaderboard  
   - `/history` - Recent match results
   - `/rank` - Your current rank

### For Leaders (During Matches)

1. **Drafting Phase**
   - Click player buttons to draft them
   - Leader A gets first pick, then alternating
   - Continue until teams are complete

2. **Lobby Creation**
   - Leader B creates custom game lobby
   - Click "📌 Share Lobby ID" to submit code
   - Leaders can cancel if players don't join

3. **Post-Game Voting**
   - Both leaders vote for winning team
   - Both leaders select MVP player
   - Winning leader uploads screenshot proof
   - Match completes automatically

### For Administrators

1. **Setup Commands**
   ```
   /queue                          # Setup queue in current channel
   /config show                    # View current configuration
   /permissions                    # Check bot permissions
   ```

2. **Player Management**
   ```
   /points add @player 50          # Award points
   /points set @player 1200        # Set exact points
   /timeout add @player 60         # Timeout for 60 minutes
   /timeout remove @player         # Remove timeout
   ```

3. **Match Management**
   ```
   /scrim cancel #001              # Force cancel match
   /scrim forcewinner #001 1       # Force Team 1 as winner
   /scrim forcemvp #001 @player    # Force MVP selection
   ```

4. **Data Management**
   ```
   /clearhistory                   # Clear all match history
   /botstats                       # View bot statistics
   ```

## 🏅 Ranking System

### Rank Tiers

| Rank | Points Required | Role |
|------|----------------|------|
| 🟤 Bronze | 0+ | Bronze |
| ⚪ Silver | 600+ | Silver |
| 🟡 Gold | 1000+ | Gold |
| 🟦 Platinum | 1200+ | Platinum |
| 💎 Diamond | 1500+ | Diamond |
| 🟢 Ascendant | 1800+ | Ascendant |
| 🔥 Immortal | 2200+ | Immortal |
| 🌟 Radiant | Top 5 Players | Radiant |

### Point System

- **Win**: +30 points
- **Loss**: -30 points  
- **MVP**: +10 additional points
- **AFK/No Show**: 30 minute timeout
- **No Screenshot Proof**: -100 points (leaders only)

## 🗂️ Project Structure

```
discord_5v5_scrims_bot/
├── main.py                 # Bot entry point
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container definition
├── docker-compose.yml     # Multi-service orchestration
├── .env.example           # Environment template
├── README.md              # Documentation
├── cogs/                  # Bot command modules
│   ├── queue_system.py    # Queue management
│   ├── match_management.py # Drafting & match flow
│   ├── admin_commands.py  # Administrative functions
│   ├── leaderboard.py     # Statistics & rankings
│   └── utility.py         # Help & general commands
├── database/              # Database layer
│   ├── models.py          # Data models
│   └── db_manager.py      # Database operations
└── utils/                 # Utility modules
    ├── embeds.py          # Discord embed builders
    ├── helpers.py         # Helper functions
    └── constants.py       # Bot constants
```

## 🔧 Development

### Running Locally

1. **Setup Development Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

2. **Setup Local Database**
   ```bash
   # Install PostgreSQL locally or use Docker
   docker run -d \
     --name scrims-postgres \
     -e POSTGRES_PASSWORD=yourpassword \
     -e POSTGRES_DB=scrims_bot \
     -p 5432:5432 \
     postgres:15-alpine
   ```

3. **Run Bot**
   ```bash
   cp .env.example .env
   # Edit .env file
   python main.py
   ```

### Code Style

- **Formatting**: Black code formatter
- **Linting**: Flake8 for code quality
- **Type Hints**: Full type annotation coverage
- **Docstrings**: Comprehensive documentation
- **Error Handling**: Graceful error recovery

### Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes with proper documentation
4. Test thoroughly with real Discord server
5. Submit pull request with clear description

## 📋 Database Schema

### Tables

- **players** - Player statistics and information
- **matches** - Active and completed matches
- **queue** - Current queue state per guild
- **config** - Per-guild bot configuration
- **match_history** - Completed match records

### Key Features

- **Connection Pooling** - Efficient database connections
- **Async Operations** - Non-blocking database queries
- **Data Integrity** - Foreign key constraints and validation
- **Performance** - Indexed queries for fast lookups

## 🚨 Troubleshooting

### Common Issues

**Bot not responding to commands**
- Check bot permissions in server
- Verify bot token is correct
- Use `/permissions` command

**Queue buttons not working**
- Recreate queue with `/queue` command  
- Check channel permissions
- Ensure bot has embed links permission

**Database connection errors**
- Verify PostgreSQL is running
- Check database credentials in .env
- Ensure database exists

**Matches not starting**
- Check bot can create channels
- Verify category permissions
- Look at bot logs for errors

**Rank roles not updating**
- Enable with `/config set rank_roles_enabled true`
- Check bot has manage roles permission
- Verify role hierarchy (bot role above rank roles)

### Support

For additional support:
1. Check bot logs: `docker-compose logs scrims_bot`
2. Use `/botstats` and `/permissions` commands
3. Verify environment variables are correct
4. Test with minimal configuration first

## 📄 License

This project is provided as-is for educational and community use. Please respect Discord's Terms of Service and API guidelines when using this bot.

## 🤝 Acknowledgments

Built with:
- [discord.py](https://discordpy.readthedocs.io/) - Discord API wrapper
- [asyncpg](https://github.com/MagicStack/asyncpg) - PostgreSQL adapter
- [PostgreSQL](https://www.postgresql.org/) - Database system
- [Docker](https://www.docker.com/) - Containerization platform

---

**Happy Scrimming!** 🎮
