"""
Database manager for the 5v5 Scrims Bot using asyncpg
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
import asyncpg
import json

from config import Config
from .models import PlayerModel, MatchModel, QueueModel, ConfigModel, MatchHistoryModel, MatchStatus

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages all database operations using asyncpg"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.config = Config()

    async def initialize(self):
        """Initialize database connection pool and create tables"""
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                host=self.config.DB_HOST,
                port=self.config.DB_PORT,
                user=self.config.DB_USER,
                password=self.config.DB_PASSWORD,
                database=self.config.DB_NAME,
                min_size=5,
                max_size=20,
                command_timeout=60
            )

            logger.info("Database connection pool created")

            # Create tables
            await self.create_tables()
            logger.info("Database tables initialized")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    async def create_tables(self):
        """Create all required database tables"""
        async with self.pool.acquire() as conn:
            # Players table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(100) NOT NULL,
                    points INTEGER DEFAULT 1000,
                    matches_played INTEGER DEFAULT 0,
                    matches_won INTEGER DEFAULT 0,
                    mvp_count INTEGER DEFAULT 0,
                    timeout_until TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Matches table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    match_id VARCHAR(20) PRIMARY KEY,
                    channel_id BIGINT NOT NULL,
                    team1_players BIGINT[] NOT NULL,
                    team2_players BIGINT[] NOT NULL,
                    leader1_id BIGINT NOT NULL,
                    leader2_id BIGINT NOT NULL,
                    status VARCHAR(20) DEFAULT 'drafting',
                    winner_team INTEGER,
                    mvp_id BIGINT,
                    screenshot_url TEXT,
                    lobby_id VARCHAR(100),
                    cancelled_reason TEXT,
                    cancelled_players BIGINT[],
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Queue table  
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS queue (
                    guild_id BIGINT PRIMARY KEY,
                    players BIGINT[] DEFAULT '{}',
                    max_size INTEGER DEFAULT 10,
                    last_left_player BIGINT,
                    message_id BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Bot configuration table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    guild_id BIGINT PRIMARY KEY,
                    points_win INTEGER DEFAULT 30,
                    points_loss INTEGER DEFAULT -30,
                    points_mvp INTEGER DEFAULT 10,
                    timeout_minutes INTEGER DEFAULT 30,
                    rank_roles_enabled BOOLEAN DEFAULT TRUE,
                    queue_size INTEGER DEFAULT 10,
                    no_proof_penalty INTEGER DEFAULT 100,
                    proof_timeout_minutes INTEGER DEFAULT 30,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Match history table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS match_history (
                    id SERIAL PRIMARY KEY,
                    match_id VARCHAR(20) NOT NULL,
                    guild_id BIGINT NOT NULL,
                    team1_players BIGINT[] NOT NULL,
                    team2_players BIGINT[] NOT NULL,
                    winner_team INTEGER NOT NULL,
                    mvp_id BIGINT,
                    points_awarded JSONB NOT NULL,
                    screenshot_url TEXT,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_players_points ON players(points DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_match_history_guild ON match_history(guild_id)")

    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    # Player operations
    async def get_player(self, user_id: int) -> Optional[PlayerModel]:
        """Get player by user ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM players WHERE user_id = $1", user_id
            )
            if row:
                return PlayerModel(
                    user_id=row['user_id'],
                    username=row['username'],
                    points=row['points'],
                    matches_played=row['matches_played'],
                    matches_won=row['matches_won'],
                    mvp_count=row['mvp_count'],
                    timeout_until=row['timeout_until']
                )
            return None

    async def create_player(self, user_id: int, username: str) -> PlayerModel:
        """Create a new player"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO players (user_id, username)
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    updated_at = CURRENT_TIMESTAMP
            """, user_id, username)

        return await self.get_player(user_id)

    async def update_player_points(self, user_id: int, points_change: int):
        """Update player points"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE players SET 
                    points = points + $2,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
            """, user_id, points_change)

    async def update_player_stats(self, user_id: int, won: bool, is_mvp: bool = False):
        """Update player match statistics"""
        async with self.pool.acquire() as conn:
            mvp_increment = 1 if is_mvp else 0
            won_increment = 1 if won else 0

            await conn.execute("""
                UPDATE players SET
                    matches_played = matches_played + 1,
                    matches_won = matches_won + $2,
                    mvp_count = mvp_count + $3,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
            """, user_id, won_increment, mvp_increment)

    async def set_player_timeout(self, user_id: int, timeout_minutes: int):
        """Set player timeout"""
        timeout_until = datetime.utcnow() + timedelta(minutes=timeout_minutes)
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE players SET 
                    timeout_until = $2,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
            """, user_id, timeout_until)

    async def remove_player_timeout(self, user_id: int):
        """Remove player timeout"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE players SET 
                    timeout_until = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
            """, user_id)

    async def get_leaderboard(self, limit: int = 50, offset: int = 0) -> List[PlayerModel]:
        """Get leaderboard sorted by points"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM players 
                ORDER BY points DESC, matches_won DESC, mvp_count DESC
                LIMIT $1 OFFSET $2
            """, limit, offset)

            return [
                PlayerModel(
                    user_id=row['user_id'],
                    username=row['username'], 
                    points=row['points'],
                    matches_played=row['matches_played'],
                    matches_won=row['matches_won'],
                    mvp_count=row['mvp_count'],
                    timeout_until=row['timeout_until']
                )
                for row in rows
            ]

    async def get_player_rank_position(self, user_id: int) -> int:
        """Get player's rank position on leaderboard"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT rank FROM (
                    SELECT user_id, 
                           ROW_NUMBER() OVER (ORDER BY points DESC, matches_won DESC, mvp_count DESC) as rank
                    FROM players
                ) ranked 
                WHERE user_id = $1
            """, user_id)
            return result or 0

    # Match operations
    async def create_match(self, match: MatchModel) -> bool:
        """Create a new match"""
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO matches (
                        match_id, channel_id, team1_players, team2_players,
                        leader1_id, leader2_id, status
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, 
                match.match_id, match.channel_id, match.team1_players, match.team2_players,
                match.leader1_id, match.leader2_id, match.status.value)
                return True
            except Exception as e:
                logger.error(f"Failed to create match: {e}")
                return False

    async def get_match(self, match_id: str) -> Optional[MatchModel]:
        """Get match by ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM matches WHERE match_id = $1", match_id)
            if row:
                match = MatchModel(
                    match_id=row['match_id'],
                    channel_id=row['channel_id'],
                    team1_players=row['team1_players'],
                    team2_players=row['team2_players'],
                    leader1_id=row['leader1_id'],
                    leader2_id=row['leader2_id']
                )
                match.status = MatchStatus(row['status'])
                match.winner_team = row['winner_team']
                match.mvp_id = row['mvp_id']
                match.screenshot_url = row['screenshot_url']
                match.lobby_id = row['lobby_id']
                match.cancelled_reason = row['cancelled_reason']
                match.cancelled_players = row['cancelled_players'] or []
                return match
            return None

    async def update_match_status(self, match_id: str, status: MatchStatus):
        """Update match status"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE matches SET 
                    status = $2,
                    updated_at = CURRENT_TIMESTAMP
                WHERE match_id = $1
            """, match_id, status.value)

    async def set_match_lobby(self, match_id: str, lobby_id: str):
        """Set match lobby ID"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE matches SET 
                    lobby_id = $2,
                    updated_at = CURRENT_TIMESTAMP
                WHERE match_id = $1
            """, match_id, lobby_id)

    async def complete_match(self, match_id: str, winner_team: int, mvp_id: int, screenshot_url: str = None):
        """Complete a match with results"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE matches SET
                    status = 'completed',
                    winner_team = $2,
                    mvp_id = $3,
                    screenshot_url = $4,
                    updated_at = CURRENT_TIMESTAMP
                WHERE match_id = $1
            """, match_id, winner_team, mvp_id, screenshot_url)

    async def cancel_match(self, match_id: str, reason: str, cancelled_players: List[int]):
        """Cancel a match"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE matches SET
                    status = 'cancelled',
                    cancelled_reason = $2,
                    cancelled_players = $3,
                    updated_at = CURRENT_TIMESTAMP
                WHERE match_id = $1
            """, match_id, reason, cancelled_players)

    # Queue operations
    async def get_queue(self, guild_id: int) -> QueueModel:
        """Get guild queue"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM queue WHERE guild_id = $1", guild_id)
            if row:
                queue = QueueModel(guild_id=guild_id, max_size=row['max_size'])
                queue.players = row['players'] or []
                queue.last_left_player = row['last_left_player']
                queue.message_id = row['message_id']
                return queue
            else:
                # Create new queue
                await conn.execute("""
                    INSERT INTO queue (guild_id) VALUES ($1)
                """, guild_id)
                return QueueModel(guild_id=guild_id)

    async def update_queue(self, queue: QueueModel):
        """Update queue in database"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE queue SET
                    players = $2,
                    last_left_player = $3,
                    message_id = $4,
                    updated_at = CURRENT_TIMESTAMP
                WHERE guild_id = $1
            """, queue.guild_id, queue.players, queue.last_left_player, queue.message_id)

    # Configuration operations
    async def get_config(self, guild_id: int) -> ConfigModel:
        """Get guild configuration"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM config WHERE guild_id = $1", guild_id)
            if row:
                config = ConfigModel(guild_id)
                config.points_win = row['points_win']
                config.points_loss = row['points_loss']
                config.points_mvp = row['points_mvp']
                config.timeout_minutes = row['timeout_minutes']
                config.rank_roles_enabled = row['rank_roles_enabled']
                config.queue_size = row['queue_size']
                config.no_proof_penalty = row['no_proof_penalty']
                config.proof_timeout_minutes = row['proof_timeout_minutes']
                return config
            else:
                # Create default config
                await conn.execute("INSERT INTO config (guild_id) VALUES ($1)", guild_id)
                return ConfigModel(guild_id)

    async def update_config(self, guild_id: int, **kwargs):
        """Update guild configuration"""
        async with self.pool.acquire() as conn:
            # Build dynamic update query
            set_clauses = []
            values = [guild_id]
            counter = 2

            for key, value in kwargs.items():
                set_clauses.append(f"{key} = ${counter}")
                values.append(value)
                counter += 1

            if set_clauses:
                query = f"""
                    UPDATE config SET
                        {', '.join(set_clauses)},
                        updated_at = CURRENT_TIMESTAMP
                    WHERE guild_id = $1
                """
                await conn.execute(query, *values)

    # Match history operations
    async def add_match_history(self, history: MatchHistoryModel):
        """Add completed match to history"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO match_history (
                    match_id, guild_id, team1_players, team2_players,
                    winner_team, mvp_id, points_awarded, screenshot_url
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, 
            history.match_id, history.guild_id, history.team1_players, history.team2_players,
            history.winner_team, history.mvp_id, json.dumps(history.points_awarded), history.screenshot_url)

    async def get_match_history(self, guild_id: int, limit: int = 50, offset: int = 0) -> List[MatchHistoryModel]:
        """Get match history for guild"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM match_history 
                WHERE guild_id = $1
                ORDER BY completed_at DESC
                LIMIT $2 OFFSET $3
            """, guild_id, limit, offset)

            return [
                MatchHistoryModel(
                    match_id=row['match_id'],
                    guild_id=row['guild_id'],
                    team1_players=row['team1_players'],
                    team2_players=row['team2_players'],
                    winner_team=row['winner_team'],
                    mvp_id=row['mvp_id'],
                    points_awarded=json.loads(row['points_awarded']),
                    screenshot_url=row['screenshot_url']
                )
                for row in rows
            ]

    async def clear_match_history(self, guild_id: int):
        """Clear all match history for guild"""
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM match_history WHERE guild_id = $1", guild_id)

    async def get_player_match_count(self) -> int:
        """Get total number of players"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM players")
