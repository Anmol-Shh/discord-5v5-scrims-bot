"""
Match Management Cog for 5v5 Scrims Bot
Handles drafting, lobby creation, voting, and match completion
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
import re

import discord
from discord.ext import commands, tasks

from database.db_manager import DatabaseManager
from database.models import MatchModel, MatchStatus, PlayerModel, MatchHistoryModel
from utils.embeds import EmbedBuilder
from utils.helpers import MatchHelper, PointsHelper, ValidationHelper
from utils.constants import STATUS_MESSAGES, LOBBY_ID_PATTERN
from config import Config

logger = logging.getLogger(__name__)

class DraftView(discord.ui.View):
    """View for drafting players"""

    def __init__(self, cog, match: MatchModel, available_players: List[int], 
                 players_data: Dict[int, PlayerModel]):
        super().__init__(timeout=600)  # 10 minute timeout
        self.cog = cog
        self.match = match
        self.current_pick = len(match.team1_players) + len(match.team2_players) - 1  # Subtract leaders

        # Add buttons for each available player
        for player_id in available_players:
            player = players_data.get(player_id)
            if player:
                button = discord.ui.Button(
                    label=f"{player.username} - {player.points}pts",
                    style=discord.ButtonStyle.primary,
                    custom_id=f"draft_{player_id}"
                )
                button.callback = self.create_draft_callback(player_id)
                self.add_item(button)

    def create_draft_callback(self, player_id: int):
        """Create callback for drafting a specific player"""
        async def draft_callback(interaction: discord.Interaction):
            await self.cog.handle_draft_pick(interaction, self.match.match_id, player_id)
        return draft_callback

class LobbyView(discord.ui.View):
    """View for lobby creation phase"""

    def __init__(self, cog):
        super().__init__(timeout=900)  # 15 minute timeout
        self.cog = cog

    @discord.ui.button(label='Share Lobby ID', style=discord.ButtonStyle.primary, emoji='📌')
    async def share_lobby(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.handle_lobby_share(interaction)

    @discord.ui.button(label='Cancel Match', style=discord.ButtonStyle.danger, emoji='❌')
    async def cancel_match(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.handle_match_cancel_request(interaction)

class VotingView(discord.ui.View):
    """View for match voting (winner and MVP)"""

    def __init__(self, cog):
        super().__init__(timeout=1800)  # 30 minute timeout
        self.cog = cog

    @discord.ui.button(label='Team 1 Wins', style=discord.ButtonStyle.green, emoji='🔵')
    async def team1_wins(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.handle_winner_vote(interaction, 1)

    @discord.ui.button(label='Team 2 Wins', style=discord.ButtonStyle.green, emoji='🔴')
    async def team2_wins(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.handle_winner_vote(interaction, 2)

class MVPSelect(discord.ui.Select):
    """Select dropdown for MVP selection"""

    def __init__(self, cog, match: MatchModel, players_data: Dict[int, PlayerModel]):
        self.cog = cog
        self.match = match

        options = []
        for player_id in match.all_players:
            player = players_data.get(player_id)
            if player:
                # Show which team the player is on
                team = "Team 1" if player_id in match.team1_players else "Team 2"
                options.append(discord.SelectOption(
                    label=f"{player.username} ({team})",
                    description=f"{player.points} points",
                    value=str(player_id)
                ))

        super().__init__(placeholder="Select MVP...", options=options[:25])  # Max 25 options

    async def callback(self, interaction: discord.Interaction):
        await self.cog.handle_mvp_vote(interaction, int(self.values[0]))

class MVPView(discord.ui.View):
    """View containing MVP selection dropdown"""

    def __init__(self, cog, match: MatchModel, players_data: Dict[int, PlayerModel]):
        super().__init__(timeout=1800)
        self.add_item(MVPSelect(cog, match, players_data))

class LobbyModal(discord.ui.Modal):
    """Modal for entering lobby ID"""

    def __init__(self, cog):
        super().__init__(title="Share Lobby ID")
        self.cog = cog

        self.lobby_input = discord.ui.TextInput(
            label="Lobby ID",
            placeholder="Enter the custom game lobby ID...",
            max_length=20,
            required=True
        )
        self.add_item(self.lobby_input)

    async def on_submit(self, interaction: discord.Interaction):
        lobby_id = self.lobby_input.value.strip().upper()
        await self.cog.process_lobby_id(interaction, lobby_id)

class MatchManagement(commands.Cog):
    """Manages match drafting, lobby creation, and completion"""

    def __init__(self, bot):
        self.bot = bot
        self.db: DatabaseManager = bot.db
        self.config = Config()

        # Track active matches
        self.active_matches: Dict[str, MatchModel] = {}  # match_id -> MatchModel
        self.draft_messages: Dict[str, int] = {}  # match_id -> message_id
        self.voting_data: Dict[str, Dict] = {}  # match_id -> {winner_votes, mvp_votes}

        # Start proof timeout checker
        self.check_proof_timeouts.start()

    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.check_proof_timeouts.cancel()

    async def start_drafting(self, channel: discord.TextChannel, match: MatchModel):
        """Start the drafting phase for a match"""
        try:
            self.active_matches[match.match_id] = match
            self.voting_data[match.match_id] = {"winner_votes": {}, "mvp_votes": {}}

            # Get all players except leaders for drafting pool
            remaining_players = [p for p in [
                # This would be all 10 players minus the 2 leaders
                # Need to get this from the original queue
            ]]

            # For now, simulate 8 remaining players (10 total - 2 leaders)
            # In real implementation, this would come from the queue
            all_queue_players = []  # This should be passed from queue
            remaining_players = [p for p in all_queue_players if p not in [match.leader1_id, match.leader2_id]]

            # Get player data
            players_data = {}
            for player_id in match.all_players + remaining_players:
                player = await self.db.get_player(player_id)
                if player:
                    players_data[player_id] = player

            # Create drafting embed and view
            current_drafter = MatchHelper.get_next_drafter(self.current_pick, match.leader1_id, match.leader2_id)
            embed = EmbedBuilder.drafting_embed(match, remaining_players, players_data, current_drafter)
            view = DraftView(self, match, remaining_players, players_data)

            message = await channel.send(embed=embed, view=view)
            self.draft_messages[match.match_id] = message.id

        except Exception as e:
            logger.error(f"Error starting drafting: {e}")
            await channel.send("❌ Failed to start drafting phase!")

    async def handle_draft_pick(self, interaction: discord.Interaction, match_id: str, player_id: int):
        """Handle a draft pick"""
        await interaction.response.defer()

        try:
            match = self.active_matches.get(match_id)
            if not match:
                await interaction.followup.send("❌ Match not found!", ephemeral=True)
                return

            # Check if it's the correct player's turn
            current_pick = len(match.team1_players) + len(match.team2_players) - 2  # Subtract leaders
            current_drafter = MatchHelper.get_next_drafter(current_pick + 1, match.leader1_id, match.leader2_id)

            if interaction.user.id != current_drafter:
                await interaction.followup.send("❌ It's not your turn to pick!", ephemeral=True)
                return

            # Add player to appropriate team
            if current_drafter == match.leader1_id:
                match.team1_players.append(player_id)
            else:
                match.team2_players.append(player_id)

            # Update match in database
            await self.db.update_match_status(match_id, MatchStatus.DRAFTING)

            # Check if drafting is complete
            if MatchHelper.is_drafting_complete(match.team1_players, match.team2_players):
                await self.complete_drafting(interaction.channel, match)
            else:
                await self.update_draft_message(interaction.channel, match)

            await interaction.followup.send(f"✅ Drafted <@{player_id}>!", ephemeral=True)

        except Exception as e:
            logger.error(f"Error handling draft pick: {e}")
            await interaction.followup.send("❌ Error processing draft pick!", ephemeral=True)

    async def update_draft_message(self, channel: discord.TextChannel, match: MatchModel):
        """Update the draft message with current status"""
        try:
            message_id = self.draft_messages.get(match.match_id)
            if not message_id:
                return

            message = await channel.fetch_message(message_id)

            # Get remaining players
            all_players = []  # This should be stored somewhere
            remaining_players = MatchHelper.get_available_players(all_players, match.team1_players, match.team2_players)

            # Get player data
            players_data = {}
            for player_id in match.all_players + remaining_players:
                player = await self.db.get_player(player_id)
                if player:
                    players_data[player_id] = player

            current_pick = len(match.team1_players) + len(match.team2_players) - 2
            current_drafter = MatchHelper.get_next_drafter(current_pick + 1, match.leader1_id, match.leader2_id)

            embed = EmbedBuilder.drafting_embed(match, remaining_players, players_data, current_drafter)
            view = DraftView(self, match, remaining_players, players_data)

            await message.edit(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Error updating draft message: {e}")

    async def complete_drafting(self, channel: discord.TextChannel, match: MatchModel):
        """Complete the drafting phase and move to lobby creation"""
        try:
            # Update match status
            match.status = MatchStatus.WAITING_FOR_LOBBY
            await self.db.update_match_status(match.match_id, MatchStatus.WAITING_FOR_LOBBY)

            # Get player data for display
            players_data = {}
            for player_id in match.all_players:
                player = await self.db.get_player(player_id)
                if player:
                    players_data[player_id] = player

            # Show final teams
            final_teams_embed = EmbedBuilder.final_teams_embed(match, players_data)
            await channel.send(embed=final_teams_embed)

            # Show lobby creation interface
            lobby_embed = EmbedBuilder.lobby_creation_embed(match)
            view = LobbyView(self)
            await channel.send(embed=lobby_embed, view=view)

        except Exception as e:
            logger.error(f"Error completing drafting: {e}")
            await channel.send("❌ Error completing drafting phase!")

    async def handle_lobby_share(self, interaction: discord.Interaction):
        """Handle lobby ID sharing"""
        match = await self.get_match_from_channel(interaction.channel.id)
        if not match:
            await interaction.response.send_message("❌ No active match in this channel!", ephemeral=True)
            return

        # Check if user is leader2 (lobby creator)
        if interaction.user.id != match.leader2_id:
            await interaction.response.send_message("❌ Only the lobby creator can share the lobby ID!", ephemeral=True)
            return

        # Show modal for lobby ID input
        modal = LobbyModal(self)
        await interaction.response.send_modal(modal)

    async def process_lobby_id(self, interaction: discord.Interaction, lobby_id: str):
        """Process the submitted lobby ID"""
        try:
            match = await self.get_match_from_channel(interaction.channel.id)
            if not match:
                await interaction.response.send_message("❌ No active match in this channel!", ephemeral=True)
                return

            # Validate lobby ID
            if not MatchHelper.validate_lobby_id(lobby_id):
                await interaction.response.send_message("❌ Invalid lobby ID format! Use 4-10 alphanumeric characters.", ephemeral=True)
                return

            # Update match with lobby ID
            await self.db.set_match_lobby(match.match_id, lobby_id)
            match.lobby_id = lobby_id
            match.status = MatchStatus.IN_PROGRESS
            await self.db.update_match_status(match.match_id, MatchStatus.IN_PROGRESS)

            # Get player data
            players_data = {}
            for player_id in match.all_players:
                player = await self.db.get_player(player_id)
                if player:
                    players_data[player_id] = player

            # Update final teams embed with lobby ID
            final_teams_embed = EmbedBuilder.final_teams_embed(match, players_data)

            await interaction.response.send_message(
                f"✅ **Lobby ID Set:** `{lobby_id}`\n\n"
                f"**All players join the custom lobby now!**\n"
                f"Match is now in progress. Use voting buttons after the game ends.",
                embed=final_teams_embed
            )

            # Add voting interface
            await self.add_voting_interface(interaction.channel, match)

        except Exception as e:
            logger.error(f"Error processing lobby ID: {e}")
            await interaction.response.send_message("❌ Error setting lobby ID!", ephemeral=True)

    async def add_voting_interface(self, channel: discord.TextChannel, match: MatchModel):
        """Add voting interface for match completion"""
        try:
            voting_embed = EmbedBuilder.voting_embed(match)
            voting_view = VotingView(self)

            await asyncio.sleep(2)  # Small delay
            voting_message = await channel.send(
                "🗳️ **Leaders: Vote for winner and MVP after the match ends**",
                embed=voting_embed,
                view=voting_view
            )

            # Add MVP selection
            players_data = {}
            for player_id in match.all_players:
                player = await self.db.get_player(player_id)
                if player:
                    players_data[player_id] = player

            mvp_view = MVPView(self, match, players_data)
            await channel.send("🌟 **Select MVP:**", view=mvp_view)

        except Exception as e:
            logger.error(f"Error adding voting interface: {e}")

    async def handle_winner_vote(self, interaction: discord.Interaction, winning_team: int):
        """Handle winner vote from leaders"""
        await interaction.response.defer()

        try:
            match = await self.get_match_from_channel(interaction.channel.id)
            if not match or not match.is_leader(interaction.user.id):
                await interaction.followup.send("❌ Only match leaders can vote!", ephemeral=True)
                return

            # Record vote
            voting_data = self.voting_data.get(match.match_id, {})
            voting_data.setdefault("winner_votes", {})[interaction.user.id] = winning_team

            # Check if both leaders voted for the same winner
            winner_votes = voting_data["winner_votes"]
            if len(winner_votes) >= 2:
                votes = list(winner_votes.values())
                if votes[0] == votes[1]:  # Both leaders agree
                    match.winner_team = votes[0]
                    await interaction.followup.send(f"✅ Winner recorded: Team {votes[0]}!", ephemeral=True)

                    # Check if ready to complete
                    await self.check_match_completion(interaction.channel, match)
                else:
                    await interaction.followup.send("❌ Leaders must agree on the winner!", ephemeral=True)
            else:
                await interaction.followup.send("✅ Vote recorded! Waiting for other leader...", ephemeral=True)

        except Exception as e:
            logger.error(f"Error handling winner vote: {e}")
            await interaction.followup.send("❌ Error processing vote!", ephemeral=True)

    async def handle_mvp_vote(self, interaction: discord.Interaction, mvp_id: int):
        """Handle MVP vote"""
        await interaction.response.defer()

        try:
            match = await self.get_match_from_channel(interaction.channel.id)
            if not match or not match.is_leader(interaction.user.id):
                await interaction.followup.send("❌ Only match leaders can select MVP!", ephemeral=True)
                return

            # Record MVP vote
            voting_data = self.voting_data.get(match.match_id, {})
            voting_data.setdefault("mvp_votes", {})[interaction.user.id] = mvp_id

            # Check if both leaders voted
            mvp_votes = voting_data["mvp_votes"]
            if len(mvp_votes) >= 2:
                votes = list(mvp_votes.values())
                if votes[0] == votes[1]:  # Both leaders agree
                    match.mvp_id = votes[0]
                    await interaction.followup.send(f"✅ MVP selected: <@{votes[0]}>!", ephemeral=True)

                    # Check if ready to complete
                    await self.check_match_completion(interaction.channel, match)
                else:
                    await interaction.followup.send("❌ Leaders must agree on MVP!", ephemeral=True)
            else:
                await interaction.followup.send("✅ MVP vote recorded! Waiting for other leader...", ephemeral=True)

        except Exception as e:
            logger.error(f"Error handling MVP vote: {e}")
            await interaction.followup.send("❌ Error processing MVP selection!", ephemeral=True)

    async def check_match_completion(self, channel: discord.TextChannel, match: MatchModel):
        """Check if match can be completed and request proof"""
        if match.winner_team and match.mvp_id:
            # Request screenshot from winning team leader
            winning_leader = match.leader1_id if match.winner_team == 1 else match.leader2_id

            await channel.send(
                f"📸 **<@{winning_leader}>**: Please upload a screenshot of the match scorecard as proof!\n"
                f"⚠️ **Important:** Match will auto-cancel in {self.config.PROOF_TIMEOUT_MINUTES} minutes without proof!"
            )

            match.status = MatchStatus.VOTING
            await self.db.update_match_status(match.match_id, MatchStatus.VOTING)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen for screenshot uploads"""
        if message.author.bot:
            return

        # Check if message has attachment and is in a match channel
        if not message.attachments:
            return

        match = await self.get_match_from_channel(message.channel.id)
        if not match or match.status != MatchStatus.VOTING:
            return

        # Check if uploader is the winning team leader
        winning_leader = match.leader1_id if match.winner_team == 1 else match.leader2_id
        if message.author.id != winning_leader:
            return

        # Validate screenshot
        attachment = message.attachments[0]
        if MatchHelper.is_valid_screenshot(attachment):
            await self.complete_match(message.channel, match, attachment.url)
        else:
            await message.channel.send("❌ Invalid screenshot! Please upload a valid image file.")

    async def complete_match(self, channel: discord.TextChannel, match: MatchModel, screenshot_url: str):
        """Complete the match with all results"""
        try:
            # Get bot config for points
            guild_config = await self.db.get_config(channel.guild.id)

            # Calculate points awarded
            points_awarded = PointsHelper.calculate_points_awarded(
                match.team1_players, match.team2_players, 
                match.winner_team, match.mvp_id, guild_config
            )

            # Update player points and stats
            for player_id, points_change in points_awarded.items():
                await self.db.update_player_points(player_id, points_change)

                won = player_id in (match.team1_players if match.winner_team == 1 else match.team2_players)
                is_mvp = player_id == match.mvp_id
                await self.db.update_player_stats(player_id, won, is_mvp)

            # Complete match in database
            await self.db.complete_match(match.match_id, match.winner_team, match.mvp_id, screenshot_url)

            # Add to match history
            history = MatchHistoryModel(
                match_id=match.match_id,
                guild_id=channel.guild.id,
                team1_players=match.team1_players,
                team2_players=match.team2_players,
                winner_team=match.winner_team,
                mvp_id=match.mvp_id,
                points_awarded=points_awarded,
                screenshot_url=screenshot_url
            )
            await self.db.add_match_history(history)

            # Get updated player data
            players_data = {}
            for player_id in match.all_players:
                player = await self.db.get_player(player_id)
                if player:
                    players_data[player_id] = player

            # Send completion message
            result_embed = EmbedBuilder.match_result_embed(match, players_data, points_awarded, guild_config)
            await channel.send("🎉 **Match Completed!**", embed=result_embed)

            # Forward to history channel
            await self.forward_to_history(channel.guild, result_embed)

            # Clean up
            await self.cleanup_match(match.match_id)

            # Schedule channel deletion
            await asyncio.sleep(60)  # Wait 1 minute
            try:
                await channel.delete()
            except:
                pass

        except Exception as e:
            logger.error(f"Error completing match: {e}")
            await channel.send("❌ Error completing match!")

    async def forward_to_history(self, guild: discord.Guild, embed: discord.Embed):
        """Forward match result to history channel"""
        try:
            if self.config.SCRIM_HISTORY_CHANNEL:
                history_channel = guild.get_channel(self.config.SCRIM_HISTORY_CHANNEL)
                if history_channel:
                    await history_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error forwarding to history: {e}")

    async def get_match_from_channel(self, channel_id: int) -> Optional[MatchModel]:
        """Get active match from channel ID"""
        for match in self.active_matches.values():
            if match.channel_id == channel_id:
                return match
        return None

    async def cleanup_match(self, match_id: str):
        """Clean up match data"""
        self.active_matches.pop(match_id, None)
        self.draft_messages.pop(match_id, None)
        self.voting_data.pop(match_id, None)

    async def handle_match_cancel_request(self, interaction: discord.Interaction):
        """Handle match cancellation request"""
        match = await self.get_match_from_channel(interaction.channel.id)
        if not match or not match.is_leader(interaction.user.id):
            await interaction.response.send_message("❌ Only match leaders can cancel!", ephemeral=True)
            return

        await interaction.response.send_message(
            "⚠️ **Cancel Match**\n"
            "Are you sure you want to cancel this match? This action cannot be undone.\n"
            "Type `CANCEL` to confirm.", 
            ephemeral=True
        )

    @tasks.loop(minutes=5)
    async def check_proof_timeouts(self):
        """Check for matches that need proof timeouts"""
        try:
            for match in list(self.active_matches.values()):
                if match.status == MatchStatus.VOTING:
                    # Check if proof timeout has expired
                    time_since_voting = (datetime.utcnow() - match.updated_at).total_seconds() / 60
                    if time_since_voting > self.config.PROOF_TIMEOUT_MINUTES:
                        await self.auto_cancel_match(match, "No proof provided within time limit")
        except Exception as e:
            logger.error(f"Error checking proof timeouts: {e}")

    async def auto_cancel_match(self, match: MatchModel, reason: str):
        """Auto-cancel match due to timeout or other reason"""
        try:
            # Penalize both leaders
            penalty = self.config.NO_PROOF_PENALTY
            await self.db.update_player_points(match.leader1_id, -penalty)
            await self.db.update_player_points(match.leader2_id, -penalty)

            # Cancel match in database
            await self.db.cancel_match(match.match_id, reason, [])

            # Send notification
            channel = self.bot.get_channel(match.channel_id)
            if channel:
                await channel.send(
                    f"⚠️ **Match {match.match_id} Auto-Cancelled**\n"
                    f"Reason: {reason}\n"
                    f"Both leaders penalized: -{penalty} points"
                )

                # Forward cancellation to history
                if self.config.SCRIM_HISTORY_CHANNEL:
                    history_channel = channel.guild.get_channel(self.config.SCRIM_HISTORY_CHANNEL)
                    if history_channel:
                        await history_channel.send(
                            f"📜 **Match {match.match_id}**\n"
                            f"❌ Cancelled – {reason}\n"
                            f"−{penalty} pts to <@{match.leader1_id}> & <@{match.leader2_id}> (leaders).\n"
                            f"Other players unaffected."
                        )

            # Clean up
            await self.cleanup_match(match.match_id)

        except Exception as e:
            logger.error(f"Error auto-cancelling match: {e}")

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(MatchManagement(bot))
