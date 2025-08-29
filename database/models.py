"""
Database models for the 5v5 Scrims Bot
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional

class MatchStatus(Enum):
    """Match status enumeration"""
    DRAFTING = "drafting"
    WAITING_FOR_LOBBY = "waiting_for_lobby" 
    IN_PROGRESS = "in_progress"
    VOTING = "voting"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PlayerModel:
    """Player data model"""

    def __init__(self, user_id: int, username: str, points: int = 1000, 
                 matches_played: int = 0, matches_won: int = 0, 
                 mvp_count: int = 0, timeout_until: datetime = None):
        self.user_id = user_id
        self.username = username
        self.points = points
        self.matches_played = matches_played
        self.matches_won = matches_won
        self.mvp_count = mvp_count
        self.timeout_until = timeout_until
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage"""
        if self.matches_played == 0:
            return 0.0
        return (self.matches_won / self.matches_played) * 100

    @property
    def is_timed_out(self) -> bool:
        """Check if player is currently timed out"""
        if not self.timeout_until:
            return False
        return datetime.utcnow() < self.timeout_until

    def get_rank(self, rank_thresholds: dict) -> str:
        """Get player's rank based on points"""
        for rank, threshold in sorted(rank_thresholds.items(), key=lambda x: x[1], reverse=True):
            if self.points >= threshold:
                return rank
        return "BRONZE"

class MatchModel:
    """Match data model"""

    def __init__(self, match_id: str, channel_id: int, team1_players: List[int], 
                 team2_players: List[int], leader1_id: int, leader2_id: int):
        self.match_id = match_id
        self.channel_id = channel_id
        self.team1_players = team1_players
        self.team2_players = team2_players
        self.leader1_id = leader1_id
        self.leader2_id = leader2_id
        self.status = MatchStatus.DRAFTING
        self.winner_team = None
        self.mvp_id = None
        self.screenshot_url = None
        self.lobby_id = None
        self.cancelled_reason = None
        self.cancelled_players = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @property
    def all_players(self) -> List[int]:
        """Get all players in the match"""
        return self.team1_players + self.team2_players

    @property
    def is_team1_leader(self, user_id: int) -> bool:
        """Check if user is team 1 leader"""
        return user_id == self.leader1_id

    @property
    def is_team2_leader(self, user_id: int) -> bool:
        """Check if user is team 2 leader"""
        return user_id == self.leader2_id

    @property
    def is_leader(self, user_id: int) -> bool:
        """Check if user is any leader"""
        return user_id in [self.leader1_id, self.leader2_id]

class QueueModel:
    """Queue data model"""

    def __init__(self, guild_id: int, max_size: int = 10):
        self.guild_id = guild_id
        self.players: List[int] = []
        self.max_size = max_size
        self.last_left_player: Optional[int] = None
        self.message_id: Optional[int] = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def add_player(self, user_id: int) -> bool:
        """Add player to queue"""
        if user_id not in self.players and len(self.players) < self.max_size:
            self.players.append(user_id)
            self.updated_at = datetime.utcnow()
            return True
        return False

    def remove_player(self, user_id: int) -> bool:
        """Remove player from queue"""
        if user_id in self.players:
            self.players.remove(user_id)
            self.last_left_player = user_id
            self.updated_at = datetime.utcnow()
            return True
        return False

    @property
    def is_full(self) -> bool:
        """Check if queue is full"""
        return len(self.players) >= self.max_size

    @property
    def current_size(self) -> int:
        """Get current queue size"""
        return len(self.players)

class ConfigModel:
    """Bot configuration model"""

    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.points_win = 30
        self.points_loss = -30
        self.points_mvp = 10
        self.timeout_minutes = 30
        self.rank_roles_enabled = True
        self.queue_size = 10
        self.no_proof_penalty = 100
        self.proof_timeout_minutes = 30
        self.updated_at = datetime.utcnow()

class MatchHistoryModel:
    """Match history entry model"""

    def __init__(self, match_id: str, guild_id: int, team1_players: List[int], 
                 team2_players: List[int], winner_team: int, mvp_id: int,
                 points_awarded: dict, screenshot_url: str = None):
        self.match_id = match_id
        self.guild_id = guild_id
        self.team1_players = team1_players
        self.team2_players = team2_players
        self.winner_team = winner_team
        self.mvp_id = mvp_id
        self.points_awarded = points_awarded  # {user_id: points_change}
        self.screenshot_url = screenshot_url
        self.completed_at = datetime.utcnow()

    @property
    def losing_team(self) -> int:
        """Get losing team number"""
        return 2 if self.winner_team == 1 else 1

    @property
    def winning_players(self) -> List[int]:
        """Get winning team players"""
        return self.team1_players if self.winner_team == 1 else self.team2_players

    @property
    def losing_players(self) -> List[int]:
        """Get losing team players"""
        return self.team2_players if self.winner_team == 1 else self.team1_players
