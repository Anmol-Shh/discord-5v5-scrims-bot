"""
Leaderboard Cog for 5v5 Scrims Bot
Handles leaderboard display, player statistics, and match history
"""

import asyncio
import logging
from typing import List, Optional

import discord
from discord import app_commands
from discord.ext import commands

from database.db_manager import DatabaseManager
from database.models import PlayerModel, MatchHistoryModel
from utils.embeds import EmbedBuilder
from utils.helpers import PointsHelper
from utils.constants import LEADERBOARD_PER_PAGE, HISTORY_PER_PAGE
from config import Config

logger = logging.getLogger(__name__)

class LeaderboardPaginationView(discord.ui.View):
    """Pagination view for leaderboard"""

    def __init__(self, cog, guild_id: int, total_pages: int, current_page: int = 1):
        super().__init__(timeout=300)  # 5 minute timeout
        self.cog = cog
        self.guild_id = guild_id
        self.total_pages = total_pages
        self.current_page = current_page

        # Disable buttons if not applicable
        if current_page <= 1:
            self.previous_button.disabled = True
        if current_page >= total_pages:
            self.next_button.disabled = True

    @discord.ui.button(label='⬅️ Previous', style=discord.ButtonStyle.primary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 1:
            self.current_page -= 1
            await self.update_leaderboard(interaction)

    @discord.ui.button(label='Next ➡️', style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages:
            self.current_page += 1
            await self.update_leaderboard(interaction)

    async def update_leaderboard(self, interaction: discord.Interaction):
        """Update leaderboard display"""
        await interaction.response.defer()

        try:
            # Get leaderboard data for current page
            offset = (self.current_page - 1) * LEADERBOARD_PER_PAGE
            players = await self.cog.db.get_leaderboard(LEADERBOARD_PER_PAGE, offset)

            if not players:
                await interaction.followup.edit_message(
                    interaction.message.id,
                    content="❌ No players found on this page!",
                    embed=None,
                    view=None
                )
                return

            # Create embed
            embed = EmbedBuilder.leaderboard_embed(
                players, self.current_page, self.total_pages,
                self.cog.config.RANK_THRESHOLDS, self.cog.config.RANK_COLORS
            )

            # Update button states
            self.previous_button.disabled = (self.current_page <= 1)
            self.next_button.disabled = (self.current_page >= self.total_pages)

            await interaction.followup.edit_message(
                interaction.message.id,
                embed=embed,
                view=self
            )

        except Exception as e:
            logger.error(f"Error updating leaderboard: {e}")
            await interaction.followup.send("❌ Error updating leaderboard!", ephemeral=True)

class HistoryPaginationView(discord.ui.View):
    """Pagination view for match history"""

    def __init__(self, cog, guild_id: int, total_pages: int, current_page: int = 1):
        super().__init__(timeout=300)
        self.cog = cog
        self.guild_id = guild_id
        self.total_pages = total_pages
        self.current_page = current_page

        if current_page <= 1:
            self.previous_button.disabled = True
        if current_page >= total_pages:
            self.next_button.disabled = True

    @discord.ui.button(label='⬅️ Previous', style=discord.ButtonStyle.primary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 1:
            self.current_page -= 1
            await self.update_history(interaction)

    @discord.ui.button(label='Next ➡️', style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages:
            self.current_page += 1
            await self.update_history(interaction)

    async def update_history(self, interaction: discord.Interaction):
        """Update history display"""
        await interaction.response.defer()

        try:
            offset = (self.current_page - 1) * HISTORY_PER_PAGE
            history_entries = await self.cog.db.get_match_history(
                self.guild_id, HISTORY_PER_PAGE, offset
            )

            if not history_entries:
                await interaction.followup.edit_message(
                    interaction.message.id,
                    content="❌ No match history found on this page!",
                    embed=None,
                    view=None
                )
                return

            embed = await self.cog.create_history_embed(history_entries, self.current_page, self.total_pages)

            self.previous_button.disabled = (self.current_page <= 1)
            self.next_button.disabled = (self.current_page >= self.total_pages)

            await interaction.followup.edit_message(
                interaction.message.id,
                embed=embed,
                view=self
            )

        except Exception as e:
            logger.error(f"Error updating history: {e}")
            await interaction.followup.send("❌ Error updating history!", ephemeral=True)

class Leaderboard(commands.Cog):
    """Manages leaderboard and statistics display"""

    def __init__(self, bot):
        self.bot = bot
        self.db: DatabaseManager = bot.db
        self.config = Config()

    @app_commands.command(name="leaderboard")
    @app_commands.describe(page="Page number to view")
    async def leaderboard(self, interaction: discord.Interaction, page: Optional[int] = 1):
        """Display the points leaderboard"""
        try:
            if page < 1:
                page = 1

            # Get total player count to calculate pages
            total_players = await self.db.get_player_match_count()
            if total_players == 0:
                await interaction.response.send_message(
                    "📊 No players have joined yet! Start playing scrims to see the leaderboard.",
                    ephemeral=True
                )
                return

            total_pages = (total_players + LEADERBOARD_PER_PAGE - 1) // LEADERBOARD_PER_PAGE

            if page > total_pages:
                page = total_pages

            # Get leaderboard data
            offset = (page - 1) * LEADERBOARD_PER_PAGE
            players = await self.db.get_leaderboard(LEADERBOARD_PER_PAGE, offset)

            if not players:
                await interaction.response.send_message(
                    "❌ No players found on this page!",
                    ephemeral=True
                )
                return

            # Handle Radiant rank (top 5 players)
            if page == 1:
                for i, player in enumerate(players[:5]):
                    # Mark top 5 as Radiant in the display logic
                    pass

            # Create embed
            embed = EmbedBuilder.leaderboard_embed(
                players, page, total_pages,
                self.config.RANK_THRESHOLDS, self.config.RANK_COLORS
            )

            # Add pagination if multiple pages
            if total_pages > 1:
                view = LeaderboardPaginationView(self, interaction.guild.id, total_pages, page)
                await interaction.response.send_message(embed=embed, view=view)
            else:
                await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error displaying leaderboard: {e}")
            await interaction.response.send_message(
                "❌ Error retrieving leaderboard!",
                ephemeral=True
            )

    @app_commands.command(name="stats")
    @app_commands.describe(player="Player to view stats for (leave empty for your own)")
    async def stats(self, interaction: discord.Interaction, player: Optional[discord.Member] = None):
        """View player statistics"""
        target_player = player or interaction.user

        try:
            # Get player data
            db_player = await self.db.get_player(target_player.id)
            if not db_player:
                if target_player == interaction.user:
                    await interaction.response.send_message(
                        "📊 You haven't played any scrims yet! Join the queue to start playing.",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        f"📊 {target_player.display_name} hasn't played any scrims yet!",
                        ephemeral=True
                    )
                return

            # Get rank position
            rank_position = await self.db.get_player_rank_position(target_player.id)

            # Determine rank
            rank_name = PointsHelper.get_player_rank(db_player.points, self.config.RANK_THRESHOLDS)

            # Special handling for Radiant (top 5)
            if rank_position <= 5:
                rank_name = "RADIANT"

            # Create stats embed
            embed = EmbedBuilder.player_stats_embed(db_player, rank_position, rank_name)

            # Set thumbnail to player's avatar
            if target_player.avatar:
                embed.set_thumbnail(url=target_player.avatar.url)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error displaying stats: {e}")
            await interaction.response.send_message(
                "❌ Error retrieving player statistics!",
                ephemeral=True
            )

    @app_commands.command(name="history")
    @app_commands.describe(page="Page number to view")
    async def history(self, interaction: discord.Interaction, page: Optional[int] = 1):
        """View recent match history"""
        try:
            if page < 1:
                page = 1

            # Get match history
            offset = (page - 1) * HISTORY_PER_PAGE
            history_entries = await self.db.get_match_history(
                interaction.guild.id, HISTORY_PER_PAGE, offset
            )

            if not history_entries:
                if page == 1:
                    await interaction.response.send_message(
                        "📜 No matches have been completed yet! Play some scrims to see match history.",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        "❌ No matches found on this page!",
                        ephemeral=True
                    )
                return

            # Calculate total pages (this is an approximation)
            total_pages = page  # We don't know the exact count without another query
            if len(history_entries) == HISTORY_PER_PAGE:
                total_pages = page + 1  # There might be more pages

            # Create history embed
            embed = await self.create_history_embed(history_entries, page, total_pages)

            # Add pagination if there might be more pages
            if len(history_entries) == HISTORY_PER_PAGE or page > 1:
                view = HistoryPaginationView(self, interaction.guild.id, total_pages, page)
                await interaction.response.send_message(embed=embed, view=view)
            else:
                await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error displaying history: {e}")
            await interaction.response.send_message(
                "❌ Error retrieving match history!",
                ephemeral=True
            )

    async def create_history_embed(self, history_entries: List[MatchHistoryModel], 
                                 page: int, total_pages: int) -> discord.Embed:
        """Create match history embed"""
        embed = discord.Embed(
            title="📜 Recent Match History",
            color=self.config.COLOR_INFO
        )

        history_text = []
        for entry in history_entries:
            # Get winner and loser info
            winning_team_emoji = "🔵" if entry.winner_team == 1 else "🔴"
            losing_team_emoji = "🔴" if entry.winner_team == 1 else "🔵"

            # Format player lists
            winning_players = " ".join([f"<@{pid}>" for pid in entry.winning_players[:3]])
            if len(entry.winning_players) > 3:
                winning_players += f" +{len(entry.winning_players) - 3}"

            losing_players = " ".join([f"<@{pid}>" for pid in entry.losing_players[:3]])
            if len(entry.losing_players) > 3:
                losing_players += f" +{len(entry.losing_players) - 3}"

            # MVP info
            mvp_text = ""
            if entry.mvp_id:
                mvp_text = f"\n🌟 MVP: <@{entry.mvp_id}>"

            # Timestamp
            timestamp = entry.completed_at.strftime("%m/%d %H:%M")

            history_text.append(
                f"**Match {entry.match_id}** • {timestamp}\n"
                f"{winning_team_emoji} **Winners:** {winning_players}\n"
                f"{losing_team_emoji} **Losers:** {losing_players}{mvp_text}"
            )

        embed.description = "\n\n".join(history_text)
        embed.set_footer(text=f"Page {page}/{total_pages}")

        return embed

    @app_commands.command(name="rank")
    @app_commands.describe(player="Player to check rank for")
    async def rank(self, interaction: discord.Interaction, player: Optional[discord.Member] = None):
        """Check player's current rank"""
        target_player = player or interaction.user

        try:
            db_player = await self.db.get_player(target_player.id)
            if not db_player:
                await interaction.response.send_message(
                    f"📊 {target_player.display_name} hasn't played any scrims yet!",
                    ephemeral=True
                )
                return

            # Get rank info
            rank_position = await self.db.get_player_rank_position(target_player.id)
            rank_name = PointsHelper.get_player_rank(db_player.points, self.config.RANK_THRESHOLDS)

            if rank_position <= 5:
                rank_name = "RADIANT"

            rank_display_name = self.config.RANK_ROLE_NAMES.get(rank_name, rank_name)
            rank_color = self.config.RANK_COLORS.get(rank_name, self.config.COLOR_INFO)

            embed = discord.Embed(
                title=f"🏅 {target_player.display_name}'s Rank",
                color=rank_color
            )

            embed.add_field(
                name="Current Rank",
                value=f"#{rank_position} • {rank_display_name}",
                inline=False
            )

            embed.add_field(
                name="Points",
                value=str(db_player.points),
                inline=True
            )

            # Show points needed for next rank
            current_threshold = self.config.RANK_THRESHOLDS.get(rank_name, 0)
            next_rank = None
            next_threshold = None

            for rank, threshold in sorted(self.config.RANK_THRESHOLDS.items(), key=lambda x: x[1]):
                if threshold > db_player.points:
                    next_rank = rank
                    next_threshold = threshold
                    break

            if next_rank and next_rank != "RADIANT":
                points_needed = next_threshold - db_player.points
                embed.add_field(
                    name="Next Rank",
                    value=f"{self.config.RANK_ROLE_NAMES.get(next_rank)}\n({points_needed} points needed)",
                    inline=True
                )
            elif rank_name != "RADIANT":
                embed.add_field(
                    name="Next Rank",
                    value="🌟 Radiant\n(Reach top 5 players)",
                    inline=True
                )

            if target_player.avatar:
                embed.set_thumbnail(url=target_player.avatar.url)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error displaying rank: {e}")
            await interaction.response.send_message(
                "❌ Error retrieving rank information!",
                ephemeral=True
            )

    @app_commands.command(name="top")
    @app_commands.describe(category="Category to show top players for")
    async def top_players(self, interaction: discord.Interaction, 
                         category: Optional[str] = "points"):
        """Show top players in different categories"""
        category = category.lower()

        if category not in ["points", "wins", "winrate", "mvp"]:
            await interaction.response.send_message(
                "❌ Invalid category! Use: points, wins, winrate, mvp",
                ephemeral=True
            )
            return

        try:
            # For now, just show top by points (can extend later)
            players = await self.db.get_leaderboard(10, 0)

            if not players:
                await interaction.response.send_message(
                    "📊 No players found!",
                    ephemeral=True
                )
                return

            embed = discord.Embed(
                title=f"🏆 Top 10 by {category.title()}",
                color=self.config.COLOR_INFO
            )

            top_list = []
            for i, player in enumerate(players, 1):
                medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"#{i}"

                if category == "points":
                    value = f"{player.points} pts"
                elif category == "wins":
                    value = f"{player.matches_won} wins"
                elif category == "winrate":
                    wr = player.win_rate if player.matches_played > 0 else 0
                    value = f"{wr:.1f}%"
                elif category == "mvp":
                    value = f"{player.mvp_count} MVPs"

                top_list.append(f"{medal} **<@{player.user_id}>** - {value}")

            embed.description = "\n".join(top_list)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error displaying top players: {e}")
            await interaction.response.send_message(
                "❌ Error retrieving top players!",
                ephemeral=True
            )

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(Leaderboard(bot))
