"""
Queue System Cog for 5v5 Scrims Bot
Handles queue management, player joining/leaving, and queue status display
"""

import asyncio
import logging
from typing import Dict, List

import discord
from discord.ext import commands, tasks

from database.db_manager import DatabaseManager
from database.models import QueueModel, PlayerModel
from utils.embeds import EmbedBuilder
from utils.helpers import QueueHelper, MatchHelper, ChannelHelper
from utils.constants import STATUS_MESSAGES, TEMP_CHANNEL_NAME_FORMAT
from config import Config

logger = logging.getLogger(__name__)

class QueueView(discord.ui.View):
    """View for queue interaction buttons"""

    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label='Join Queue', style=discord.ButtonStyle.green, emoji='ðŸŸ¢')
    async def join_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.handle_join_queue(interaction)

    @discord.ui.button(label='Leave Queue', style=discord.ButtonStyle.red, emoji='ðŸ”´')
    async def leave_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.handle_leave_queue(interaction)

class QueueSystem(commands.Cog):
    """Manages the 5v5 scrim queue system"""

    def __init__(self, bot):
        self.bot = bot
        self.db: DatabaseManager = bot.db
        self.config = Config()
        self.active_queues: Dict[int, QueueModel] = {}  # guild_id -> QueueModel
        self.queue_messages: Dict[int, int] = {}  # guild_id -> message_id

        # Start background task
        self.update_queue_display.start()

    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.update_queue_display.cancel()

    async def get_or_create_queue(self, guild_id: int) -> QueueModel:
        """Get existing queue or create new one"""
        if guild_id in self.active_queues:
            return self.active_queues[guild_id]

        queue = await self.db.get_queue(guild_id)
        self.active_queues[guild_id] = queue
        return queue

    async def update_queue_in_db(self, queue: QueueModel):
        """Update queue in database"""
        await self.db.update_queue(queue)
        self.active_queues[queue.guild_id] = queue

    @commands.hybrid_command(name="queue")
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def setup_queue(self, ctx):
        """Set up the queue embed in current channel"""
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send("âŒ You need Manage Messages permission to set up the queue!", ephemeral=True)
            return

        queue = await self.get_or_create_queue(ctx.guild.id)

        # Get player data for display
        players_data = {}
        for player_id in queue.players:
            player = await self.db.get_player(player_id)
            if player:
                players_data[player_id] = player

        # Create embed and view
        embed = EmbedBuilder.queue_embed(queue, players_data)
        view = QueueView(self)

        # Send message
        message = await ctx.send(embed=embed, view=view)

        # Store message info
        queue.message_id = message.id
        await self.update_queue_in_db(queue)
        self.queue_messages[ctx.guild.id] = message.id

        await ctx.send("âœ… Queue has been set up in this channel!", ephemeral=True)

    async def handle_join_queue(self, interaction: discord.Interaction):
        """Handle player joining queue"""
        await interaction.response.defer()

        try:
            # Get or create player
            player = await self.db.get_player(interaction.user.id)
            if not player:
                player = await self.db.create_player(interaction.user.id, interaction.user.display_name)

            # Check if player can join
            queue = await self.get_or_create_queue(interaction.guild.id)
            can_join, reason = QueueHelper.can_join_queue(
                interaction.user.id, 
                queue.players, 
                queue.max_size, 
                player.is_timed_out if player else False
            )

            if not can_join:
                await interaction.followup.send(reason, ephemeral=True)
                return

            # Add player to queue
            queue.add_player(interaction.user.id)
            await self.update_queue_in_db(queue)

            # Update display
            await self.update_queue_message(interaction.guild.id)

            # Check if queue is full and start match
            if queue.is_full:
                await self.start_match(interaction.guild, queue)
            else:
                await interaction.followup.send(STATUS_MESSAGES["queue_join_success"], ephemeral=True)

        except Exception as e:
            logger.error(f"Error handling join queue: {e}")
            await interaction.followup.send(STATUS_MESSAGES["unknown_error"], ephemeral=True)

    async def handle_leave_queue(self, interaction: discord.Interaction):
        """Handle player leaving queue"""
        await interaction.response.defer()

        try:
            queue = await self.get_or_create_queue(interaction.guild.id)

            can_leave, reason = QueueHelper.can_leave_queue(interaction.user.id, queue.players)
            if not can_leave:
                await interaction.followup.send(reason, ephemeral=True)
                return

            # Remove player from queue
            queue.remove_player(interaction.user.id)
            await self.update_queue_in_db(queue)

            # Update display
            await self.update_queue_message(interaction.guild.id)

            await interaction.followup.send(STATUS_MESSAGES["queue_leave_success"], ephemeral=True)

        except Exception as e:
            logger.error(f"Error handling leave queue: {e}")
            await interaction.followup.send(STATUS_MESSAGES["unknown_error"], ephemeral=True)

    async def update_queue_message(self, guild_id: int):
        """Update queue display message"""
        try:
            if guild_id not in self.queue_messages:
                return

            queue = await self.get_or_create_queue(guild_id)
            message_id = self.queue_messages[guild_id]

            # Get player data
            players_data = {}
            for player_id in queue.players:
                player = await self.db.get_player(player_id)
                if player:
                    players_data[player_id] = player

            # Find message and update
            for guild in self.bot.guilds:
                if guild.id == guild_id:
                    for channel in guild.text_channels:
                        try:
                            message = await channel.fetch_message(message_id)
                            embed = EmbedBuilder.queue_embed(queue, players_data)
                            await message.edit(embed=embed)
                            return
                        except (discord.NotFound, discord.Forbidden):
                            continue

        except Exception as e:
            logger.error(f"Error updating queue message: {e}")

    async def start_match(self, guild: discord.Guild, queue: QueueModel):
        """Start a match when queue is full"""
        try:
            # Generate match ID
            match_id = MatchHelper.generate_match_id()

            # Select random leaders
            leader1, leader2 = MatchHelper.select_random_leaders(queue.players)

            # Create temporary channel for match
            category = None
            if self.config.SCRIM_CATEGORY:
                category = guild.get_channel(self.config.SCRIM_CATEGORY)

            match_channel = await ChannelHelper.create_match_channel(
                guild, category, match_id, queue.players
            )

            if not match_channel:
                await self.send_error_to_queue_channel(guild, "Failed to create match channel!")
                return

            # Create match in database
            from database.models import MatchModel, MatchStatus
            match = MatchModel(
                match_id=match_id,
                channel_id=match_channel.id,
                team1_players=[leader1],
                team2_players=[leader2],
                leader1_id=leader1,
                leader2_id=leader2
            )
            match.status = MatchStatus.DRAFTING

            success = await self.db.create_match(match)
            if not success:
                await match_channel.delete()
                await self.send_error_to_queue_channel(guild, "Failed to create match in database!")
                return

            # Clear queue
            queue.players.clear()
            queue.last_left_player = None
            await self.update_queue_in_db(queue)
            await self.update_queue_message(guild.id)

            # Start drafting in match channel
            await self.bot.get_cog("MatchManagement").start_drafting(match_channel, match)

            # Notify players
            player_mentions = " ".join([f"<@{pid}>" for pid in queue.players])
            await match_channel.send(
                f"ðŸŽ® **Match {match_id} Started!**\n\n"
                f"{player_mentions}\n\n"
                f"ðŸ‘‘ **Leaders:**\n"
                f"â€¢ <@{leader1}> - Gets first draft pick\n"
                f"â€¢ <@{leader2}> - Must create lobby\n\n"
                f"**Drafting will begin shortly...**"
            )

        except Exception as e:
            logger.error(f"Error starting match: {e}")
            await self.send_error_to_queue_channel(guild, f"Failed to start match: {str(e)}")

    async def send_error_to_queue_channel(self, guild: discord.Guild, error_message: str):
        """Send error message to queue channel"""
        try:
            if guild.id in self.queue_messages:
                message_id = self.queue_messages[guild.id]
                for channel in guild.text_channels:
                    try:
                        message = await channel.fetch_message(message_id)
                        await message.channel.send(f"âŒ **Error:** {error_message}")
                        return
                    except (discord.NotFound, discord.Forbidden):
                        continue
        except Exception as e:
            logger.error(f"Error sending error message: {e}")

    @tasks.loop(seconds=30)
    async def update_queue_display(self):
        """Periodically update queue displays"""
        try:
            for guild_id in list(self.queue_messages.keys()):
                await self.update_queue_message(guild_id)
        except Exception as e:
            logger.error(f"Error in queue update task: {e}")

    @update_queue_display.before_loop
    async def before_update_queue_display(self):
        """Wait for bot to be ready before starting task"""
        await self.bot.wait_until_ready()

    @commands.command(name="clearqueue")
    @commands.has_permissions(manage_messages=True)
    async def clear_queue(self, ctx):
        """Clear the current queue (Admin only)"""
        queue = await self.get_or_create_queue(ctx.guild.id)
        queue.players.clear()
        queue.last_left_player = None
        await self.update_queue_in_db(queue)
        await self.update_queue_message(ctx.guild.id)

        await ctx.send("âœ… Queue has been cleared!")

    @commands.command(name="forcestart")
    @commands.has_permissions(manage_messages=True)
    async def force_start(self, ctx):
        """Force start a match with current queue (Admin only)"""
        queue = await self.get_or_create_queue(ctx.guild.id)

        current_players = len(queue.players)

        if current_players < 4:
            await ctx.send("âŒ Need at least 4 players to start a match!")
            return

        if current_players % 2 != 0:
            await ctx.send("âŒ Need an even number of players for balanced teams!")
            return

        # Force start with current players
        await self.start_match(ctx.guild, queue)
        await ctx.send(f"âœ… Match force started with {current_players} players!")

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(QueueSystem(bot))