"""
Helper utilities for the 5v5 Scrims Bot
"""

import random
import string
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple

import discord
from discord.ext import commands

from config import Config
from utils.constants import (LOBBY_ID_PATTERN, ALLOWED_IMAGE_EXTENSIONS, 
                           MAX_SCREENSHOT_SIZE_MB, MATCH_ID_PREFIX, MATCH_ID_LENGTH)

class MatchHelper:
    """Helper functions for match management"""

    @staticmethod
    def generate_match_id() -> str:
        """Generate a unique match ID"""
        numbers = ''.join(random.choices(string.digits, k=MATCH_ID_LENGTH))
        return f"{MATCH_ID_PREFIX}{numbers}"

    @staticmethod
    def select_random_leaders(players: List[int]) -> Tuple[int, int]:
        """Select two random leaders from player list"""
        if len(players) < 2:
            raise ValueError("Need at least 2 players to select leaders")

        leaders = random.sample(players, 2)
        return leaders[0], leaders[1]  # leader1 gets first pick, leader2 creates lobby

    @staticmethod
    def create_initial_teams(leader1: int, leader2: int) -> Tuple[List[int], List[int]]:
        """Create initial teams with leaders"""
        return [leader1], [leader2]

    @staticmethod
    def get_available_players(all_players: List[int], team1: List[int], team2: List[int]) -> List[int]:
        """Get list of players not yet drafted"""
        drafted = set(team1 + team2)
        return [p for p in all_players if p not in drafted]

    @staticmethod
    def get_next_drafter(current_pick: int, leader1: int, leader2: int) -> int:
        """Get next player to draft (alternating picks)"""
        # Leader1 gets picks 1, 3, 5, 7, 9 (odd)
        # Leader2 gets picks 2, 4, 6, 8, 10 (even)
        if current_pick % 2 == 1:
            return leader1
        else:
            return leader2

    @staticmethod
    def is_drafting_complete(team1: List[int], team2: List[int], team_size: int = 5) -> bool:
        """Check if drafting is complete"""
        return len(team1) == team_size and len(team2) == team_size

    @staticmethod
    def validate_lobby_id(lobby_id: str) -> bool:
        """Validate lobby ID format"""
        return bool(re.match(LOBBY_ID_PATTERN, lobby_id.upper()))

    @staticmethod
    def is_valid_screenshot(attachment: discord.Attachment) -> bool:
        """Validate screenshot attachment"""
        if not attachment:
            return False

        # Check file size (convert to MB)
        if attachment.size > MAX_SCREENSHOT_SIZE_MB * 1024 * 1024:
            return False

        # Check file extension
        file_ext = attachment.filename.lower().split('.')[-1]
        return f'.{file_ext}' in ALLOWED_IMAGE_EXTENSIONS

class QueueHelper:
    """Helper functions for queue management"""

    @staticmethod  
    def can_join_queue(player_id: int, queue_players: List[int], max_size: int, is_timed_out: bool) -> Tuple[bool, str]:
        """Check if player can join queue"""
        if is_timed_out:
            return False, "You are currently timed out from joining the queue!"

        if player_id in queue_players:
            return False, "You are already in the queue!"

        if len(queue_players) >= max_size:
            return False, "The queue is full!"

        return True, "OK"

    @staticmethod
    def can_leave_queue(player_id: int, queue_players: List[int]) -> Tuple[bool, str]:
        """Check if player can leave queue"""
        if player_id not in queue_players:
            return False, "You are not in the queue!"

        return True, "OK"

class PointsHelper:
    """Helper functions for points and ranking"""

    @staticmethod
    def calculate_points_awarded(team1_players: List[int], team2_players: List[int],
                               winner_team: int, mvp_id: int, config) -> Dict[int, int]:
        """Calculate points awarded for each player"""
        points_awarded = {}

        winning_players = team1_players if winner_team == 1 else team2_players
        losing_players = team2_players if winner_team == 1 else team1_players

        # Award points to winners
        for player_id in winning_players:
            points_awarded[player_id] = config.points_win

        # Deduct points from losers  
        for player_id in losing_players:
            points_awarded[player_id] = config.points_loss

        # Add MVP bonus
        if mvp_id:
            points_awarded[mvp_id] = points_awarded.get(mvp_id, 0) + config.points_mvp

        return points_awarded

    @staticmethod
    def get_player_rank(points: int, rank_thresholds: Dict[str, int]) -> str:
        """Get player rank based on points"""
        for rank, threshold in sorted(rank_thresholds.items(), key=lambda x: x[1], reverse=True):
            if rank == "RADIANT":
                continue  # Radiant is handled separately (top 5)
            if points >= threshold:
                return rank
        return "BRONZE"

    @staticmethod
    def get_rank_color(rank: str) -> int:
        """Get color for rank"""
        return Config.RANK_COLORS.get(rank, Config.COLOR_INFO)

class PermissionHelper:
    """Helper functions for permission checking"""

    @staticmethod
    def is_admin(member: discord.Member) -> bool:
        """Check if member is admin"""
        return member.guild_permissions.administrator

    @staticmethod
    def is_moderator(member: discord.Member) -> bool:
        """Check if member is moderator (manage messages permission)"""
        return member.guild_permissions.manage_messages or member.guild_permissions.administrator

    @staticmethod
    def can_manage_matches(member: discord.Member) -> bool:
        """Check if member can manage matches"""
        return PermissionHelper.is_moderator(member)

    @staticmethod
    async def has_required_permissions(bot: commands.Bot, guild: discord.Guild) -> Tuple[bool, List[str]]:
        """Check if bot has all required permissions"""
        bot_member = guild.get_member(bot.user.id)
        if not bot_member:
            return False, ["Bot not in guild"]

        missing_perms = []
        perms = bot_member.guild_permissions

        required_perms = {
            'send_messages': perms.send_messages,
            'embed_links': perms.embed_links,
            'attach_files': perms.attach_files,
            'read_message_history': perms.read_message_history,
            'manage_messages': perms.manage_messages,
            'manage_channels': perms.manage_channels,
            'manage_roles': perms.manage_roles
        }

        for perm_name, has_perm in required_perms.items():
            if not has_perm:
                missing_perms.append(perm_name)

        return len(missing_perms) == 0, missing_perms

class TimeHelper:
    """Helper functions for time operations"""

    @staticmethod
    def format_time_remaining(target_time: datetime) -> str:
        """Format time remaining until target"""
        now = datetime.utcnow()
        if target_time <= now:
            return "Expired"

        delta = target_time - now

        if delta.days > 0:
            return f"{delta.days}d {delta.seconds // 3600}h"
        elif delta.seconds >= 3600:
            return f"{delta.seconds // 3600}h {(delta.seconds % 3600) // 60}m"
        elif delta.seconds >= 60:
            return f"{delta.seconds // 60}m"
        else:
            return f"{delta.seconds}s"

    @staticmethod
    def is_timeout_expired(timeout_time: Optional[datetime]) -> bool:
        """Check if timeout has expired"""
        if not timeout_time:
            return True
        return datetime.utcnow() >= timeout_time

    @staticmethod
    def add_timeout(minutes: int) -> datetime:
        """Add timeout minutes to current time"""
        return datetime.utcnow() + timedelta(minutes=minutes)

class MessageHelper:
    """Helper functions for message operations"""

    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to max length"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

    @staticmethod
    def format_player_list(player_ids: List[int], max_players: int = 10) -> str:
        """Format list of player mentions"""
        if not player_ids:
            return "None"

        players = [f"<@{pid}>" for pid in player_ids[:max_players]]
        if len(player_ids) > max_players:
            players.append(f"... and {len(player_ids) - max_players} more")

        return ", ".join(players)

    @staticmethod
    def create_progress_bar(current: int, maximum: int, length: int = 10) -> str:
        """Create a text progress bar"""
        if maximum == 0:
            return "▱" * length

        filled = int((current / maximum) * length)
        return "▰" * filled + "▱" * (length - filled)

class ValidationHelper:
    """Helper functions for input validation"""

    @staticmethod
    def validate_points(points: int) -> bool:
        """Validate points value"""
        return -10000 <= points <= 10000

    @staticmethod
    def validate_timeout_minutes(minutes: int) -> bool:
        """Validate timeout minutes"""
        return 1 <= minutes <= 1440  # 1 minute to 24 hours

    @staticmethod
    def validate_queue_size(size: int) -> bool:
        """Validate queue size"""
        return 4 <= size <= 20  # Minimum 4, maximum 20

    @staticmethod
    def validate_user_mention(mention: str) -> bool:
        """Validate Discord user mention format"""
        return bool(re.match(r'^<@!?\\d+>$', mention))

class ChannelHelper:
    """Helper functions for channel operations"""

    @staticmethod
    async def create_match_channel(guild: discord.Guild, category: discord.CategoryChannel,
                                 match_id: str, players: List[int]) -> Optional[discord.TextChannel]:
        """Create private match channel"""
        try:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            # Add permissions for all match players
            for player_id in players:
                member = guild.get_member(player_id)
                if member:
                    overwrites[member] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            channel = await guild.create_text_channel(
                name=f"scrim-{match_id.lower()}",
                category=category,
                overwrites=overwrites,
                topic=f"🎮 5v5 Scrim Match {match_id}"
            )

            return channel

        except Exception:
            return None

    @staticmethod
    async def delete_match_channel(channel: discord.TextChannel, delay: int = 30):
        """Delete match channel with delay"""
        try:
            await asyncio.sleep(delay)
            await channel.delete()
        except Exception:
            pass  # Channel might already be deleted

class RankHelper:
    """Helper functions for rank management"""

    @staticmethod
    async def update_player_rank_role(member: discord.Member, new_rank: str, config: Config):
        """Update player's rank role"""
        try:
            # Remove all existing rank roles
            roles_to_remove = []
            for role in member.roles:
                if role.name in config.RANK_ROLE_NAMES.values():
                    roles_to_remove.append(role)

            if roles_to_remove:
                await member.remove_roles(*roles_to_remove)

            # Add new rank role
            new_role_name = config.RANK_ROLE_NAMES.get(new_rank)
            if new_role_name:
                rank_role = discord.utils.get(member.guild.roles, name=new_role_name)

                if not rank_role:
                    # Create the role if it doesn't exist
                    rank_role = await member.guild.create_role(
                        name=new_role_name,
                        color=config.RANK_COLORS.get(new_rank, 0x99AAB5),
                        hoist=True,
                        mentionable=False
                    )

                await member.add_roles(rank_role)

        except Exception as e:
            # Log error but don't raise - rank roles are not critical
            pass

    @staticmethod
    def calculate_rank_changes(old_points: int, new_points: int, thresholds: dict) -> Tuple[str, str, bool]:
        """Calculate if rank changed between old and new points"""
        old_rank = PointsHelper.get_player_rank(old_points, thresholds)
        new_rank = PointsHelper.get_player_rank(new_points, thresholds)
        rank_changed = old_rank != new_rank

        return old_rank, new_rank, rank_changed
