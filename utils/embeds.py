"""
Embed utilities for the 5v5 Scrims Bot
"""

import discord
from datetime import datetime
from typing import List, Optional, Dict

from config import Config
from database.models import PlayerModel, MatchModel, QueueModel, MatchHistoryModel
from utils.constants import STATUS_MESSAGES

class EmbedBuilder:
    """Utility class for building Discord embeds"""

    @staticmethod
    def queue_embed(queue: QueueModel, players_data: Dict[int, PlayerModel]) -> discord.Embed:
        """Create queue status embed"""
        embed = discord.Embed(
            title="📌 5v5 Scrim Queue",
            color=Config.COLOR_QUEUE,
            timestamp=datetime.utcnow()
        )

        embed.add_field(
            name="Players in queue",
            value=f"{queue.current_size}/{queue.max_size}",
            inline=True
        )

        if queue.players:
            players_list = []
            for i, player_id in enumerate(queue.players, 1):
                player = players_data.get(player_id)
                if player:
                    players_list.append(f"{i}. <@{player_id}> — {player.points} pts")
                else:
                    players_list.append(f"{i}. <@{player_id}> — ??? pts")

            embed.add_field(
                name="👥 Joined Players",
                value="\n".join(players_list) if players_list else "None",
                inline=False
            )

        if queue.last_left_player:
            embed.add_field(
                name="❌ Last left",
                value=f"<@{queue.last_left_player}>",
                inline=True
            )

        embed.set_footer(text="Use buttons below to join/leave queue")
        return embed

    @staticmethod
    def drafting_embed(match: MatchModel, available_players: List[int], 
                      players_data: Dict[int, PlayerModel], current_drafter: int) -> discord.Embed:
        """Create drafting phase embed"""
        embed = discord.Embed(
            title="⚔️ Team Drafting Phase",
            color=Config.COLOR_MATCH,
            timestamp=datetime.utcnow()
        )

        embed.add_field(
            name="👑 Leaders",
            value=f"<@{match.leader1_id}> (First Pick) | <@{match.leader2_id}> (Lobby Creator)",
            inline=False
        )

        if available_players:
            players_list = []
            for player_id in available_players:
                player = players_data.get(player_id)
                if player:
                    players_list.append(f"<@{player_id}> — {player.points} pts")
                else:
                    players_list.append(f"<@{player_id}> — ??? pts")

            embed.add_field(
                name="📋 Available Players",
                value="\n".join(players_list),
                inline=False
            )

        # Show current teams
        team1_list = [f"<@{match.leader1_id}> 👑"]
        for player_id in match.team1_players:
            if player_id != match.leader1_id:
                team1_list.append(f"<@{player_id}>")

        team2_list = [f"<@{match.leader2_id}> 👑"]  
        for player_id in match.team2_players:
            if player_id != match.leader2_id:
                team2_list.append(f"<@{player_id}>")

        embed.add_field(
            name="🔵 Team 1",
            value="\n".join(team1_list),
            inline=True
        )

        embed.add_field(
            name="🔴 Team 2", 
            value="\n".join(team2_list),
            inline=True
        )

        embed.add_field(
            name="⏰ Current Turn",
            value=f"<@{current_drafter}>",
            inline=False
        )

        embed.set_footer(text="Click on a player to draft them!")
        return embed

    @staticmethod
    def lobby_creation_embed(match: MatchModel) -> discord.Embed:
        """Create lobby creation embed"""
        embed = discord.Embed(
            title="📌 Lobby Creation Phase",
            description=f"<@{match.leader2_id}> must create custom lobby in-game.",
            color=Config.COLOR_INFO,
            timestamp=datetime.utcnow()
        )

        embed.add_field(
            name="Instructions",
            value="1. Create a custom game lobby\n2. Copy the lobby code\n3. Click 'Share Lobby ID' below",
            inline=False
        )

        embed.set_footer(text="Leaders can cancel match if players don't join")
        return embed

    @staticmethod
    def final_teams_embed(match: MatchModel, players_data: Dict[int, PlayerModel]) -> discord.Embed:
        """Create final teams embed"""
        embed = discord.Embed(
            title="🎮 Final Teams",
            color=Config.COLOR_SUCCESS,
            timestamp=datetime.utcnow()
        )

        team1_list = []
        for player_id in match.team1_players:
            player = players_data.get(player_id)
            crown = " 👑" if player_id == match.leader1_id else ""
            points = player.points if player else "???"
            team1_list.append(f"<@{player_id}>{crown} — {points} pts")

        team2_list = []
        for player_id in match.team2_players:
            player = players_data.get(player_id)
            crown = " 👑" if player_id == match.leader2_id else ""
            points = player.points if player else "???"
            team2_list.append(f"<@{player_id}>{crown} — {points} pts")

        embed.add_field(
            name="🔵 Team 1",
            value="\n".join(team1_list),
            inline=True
        )

        embed.add_field(
            name="🔴 Team 2",
            value="\n".join(team2_list), 
            inline=True
        )

        if match.lobby_id:
            embed.add_field(
                name="🎯 Lobby ID",
                value=f"`{match.lobby_id}`",
                inline=False
            )

        embed.set_footer(text=f"Match ID: {match.match_id}")
        return embed

    @staticmethod
    def voting_embed(match: MatchModel) -> discord.Embed:
        """Create voting embed for leaders"""
        embed = discord.Embed(
            title=f"🗳️ Match {match.match_id} Voting Panel",
            description="**Leaders only** - Vote for winner and select MVP",
            color=Config.COLOR_WARNING,
            timestamp=datetime.utcnow()
        )

        embed.add_field(
            name="🔵 Team 1",
            value="\n".join([f"<@{pid}>" for pid in match.team1_players]),
            inline=True
        )

        embed.add_field(
            name="🔴 Team 2",
            value="\n".join([f"<@{pid}>" for pid in match.team2_players]),
            inline=True
        )

        embed.add_field(
            name="⚠️ Important",
            value="Winning leader must upload screenshot proof after voting!",
            inline=False
        )

        embed.set_footer(text="Vote for the winning team first, then select MVP")
        return embed

    @staticmethod  
    def match_result_embed(match: MatchModel, players_data: Dict[int, PlayerModel],
                          points_awarded: Dict[int, int], config) -> discord.Embed:
        """Create match result embed"""
        embed = discord.Embed(
            title=f"📜 Match Completed – ID: {match.match_id}",
            color=Config.COLOR_SUCCESS,
            timestamp=datetime.utcnow()
        )

        winning_team = match.team1_players if match.winner_team == 1 else match.team2_players
        losing_team = match.team2_players if match.winner_team == 1 else match.team1_players

        winner_list = []
        for player_id in winning_team:
            player = players_data.get(player_id)
            points_change = points_awarded.get(player_id, 0)
            mvp_bonus = " 🌟" if player_id == match.mvp_id else ""
            winner_list.append(f"<@{player_id}>{mvp_bonus} (+{abs(points_change)} pts)")

        loser_list = []
        for player_id in losing_team:
            points_change = points_awarded.get(player_id, 0)
            mvp_bonus = " 🌟" if player_id == match.mvp_id else ""
            loser_list.append(f"<@{player_id}>{mvp_bonus} ({points_change} pts)")

        embed.add_field(
            name="🏆 Winners",
            value="\n".join(winner_list),
            inline=True
        )

        embed.add_field(
            name="❌ Losers", 
            value="\n".join(loser_list),
            inline=True
        )

        if match.mvp_id:
            embed.add_field(
                name="🌟 MVP",
                value=f"<@{match.mvp_id}> (+{config.points_mvp} pts)",
                inline=False
            )

        if match.screenshot_url:
            embed.add_field(
                name="🖼️ Proof",
                value="Screenshot uploaded",
                inline=True
            )
            embed.set_image(url=match.screenshot_url)

        embed.set_footer(text=f"Match completed • {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        return embed

    @staticmethod
    def leaderboard_embed(players: List[PlayerModel], page: int, total_pages: int,
                         rank_thresholds: dict, rank_colors: dict) -> discord.Embed:
        """Create leaderboard embed"""
        embed = discord.Embed(
            title="🏆 Leaderboard",
            color=Config.COLOR_INFO,
            timestamp=datetime.utcnow()
        )

        if not players:
            embed.description = "No players found!"
            return embed

        leaderboard_text = []
        start_rank = (page - 1) * 10 + 1

        for i, player in enumerate(players):
            rank = start_rank + i
            rank_name = player.get_rank(rank_thresholds)

            if rank <= 3:
                medal = ["🥇", "🥈", "🥉"][rank - 1]
            else:
                medal = f"#{rank}"

            wr = f"{player.win_rate:.1f}%" if player.matches_played > 0 else "N/A"

            leaderboard_text.append(
                f"{medal} **<@{player.user_id}>** - {player.points} pts\n"
                f"     {rank_name} | {player.matches_won}W-{player.matches_played - player.matches_won}L ({wr}) | {player.mvp_count} MVP"
            )

        embed.description = "\n\n".join(leaderboard_text)
        embed.set_footer(text=f"Page {page}/{total_pages} • Total players: {len(players) + (page-1)*10}")
        return embed

    @staticmethod
    def player_stats_embed(player: PlayerModel, rank_position: int, rank_name: str) -> discord.Embed:
        """Create player statistics embed"""
        rank_color = Config.RANK_COLORS.get(rank_name, Config.COLOR_INFO)

        embed = discord.Embed(
            title=f"📊 {player.username}'s Stats",
            color=rank_color,
            timestamp=datetime.utcnow()
        )

        embed.add_field(name="💰 Points", value=str(player.points), inline=True)
        embed.add_field(name="🏅 Rank", value=f"#{rank_position}", inline=True)
        embed.add_field(name="🎖️ Tier", value=Config.RANK_ROLE_NAMES.get(rank_name, rank_name), inline=True)

        embed.add_field(name="🎮 Matches Played", value=str(player.matches_played), inline=True)
        embed.add_field(name="🏆 Matches Won", value=str(player.matches_won), inline=True)

        win_rate = player.win_rate if player.matches_played > 0 else 0
        embed.add_field(name="📈 Win Rate", value=f"{win_rate:.1f}%", inline=True)

        embed.add_field(name="🌟 MVP Awards", value=str(player.mvp_count), inline=True)

        if player.is_timed_out:
            time_left = player.timeout_until - datetime.utcnow()
            minutes_left = int(time_left.total_seconds() / 60)
            embed.add_field(name="⏰ Timeout", value=f"{minutes_left}m remaining", inline=True)

        embed.set_footer(text=f"Player since {player.created_at.strftime('%Y-%m-%d')}")
        return embed

    @staticmethod
    def error_embed(message: str, title: str = "Error") -> discord.Embed:
        """Create error embed"""
        embed = discord.Embed(
            title=f"❌ {title}",
            description=message,
            color=Config.COLOR_ERROR,
            timestamp=datetime.utcnow()
        )
        return embed

    @staticmethod
    def success_embed(message: str, title: str = "Success") -> discord.Embed:
        """Create success embed"""
        embed = discord.Embed(
            title=f"✅ {title}",
            description=message,
            color=Config.COLOR_SUCCESS,
            timestamp=datetime.utcnow()
        )
        return embed

    @staticmethod
    def warning_embed(message: str, title: str = "Warning") -> discord.Embed:
        """Create warning embed"""
        embed = discord.Embed(
            title=f"⚠️ {title}",
            description=message,
            color=Config.COLOR_WARNING,
            timestamp=datetime.utcnow()
        )
        return embed

    @staticmethod
    def info_embed(message: str, title: str = "Info") -> discord.Embed:
        """Create info embed"""
        embed = discord.Embed(
            title=f"ℹ️ {title}",
            description=message,
            color=Config.COLOR_INFO,
            timestamp=datetime.utcnow()
        )
        return embed
