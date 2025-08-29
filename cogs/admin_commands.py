"""
Admin Commands Cog for 5v5 Scrims Bot
Handles all administrative commands for bot configuration and management
"""

import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from database.db_manager import DatabaseManager
from database.models import MatchStatus
from utils.embeds import EmbedBuilder
from utils.helpers import PermissionHelper, ValidationHelper
from utils.constants import STATUS_MESSAGES
from config import Config

logger = logging.getLogger(__name__)

class AdminCommands(commands.Cog):
    """Administrative commands for bot management"""

    def __init__(self, bot):
        self.bot = bot
        self.db: DatabaseManager = bot.db
        self.config = Config()

    def cog_check(self, ctx):
        """Check if user has permission to use admin commands"""
        return ctx.author.guild_permissions.manage_messages

    # Configuration Commands
    @app_commands.command(name="config")
    @app_commands.describe(
        action="Action to perform",
        setting="Setting to modify", 
        value="New value for the setting"
    )
    async def config_command(self, interaction: discord.Interaction, 
                           action: str = "show", setting: Optional[str] = None, 
                           value: Optional[str] = None):
        """View or modify bot configuration"""
        if action.lower() == "show":
            await self.show_config(interaction)
        elif action.lower() == "set":
            if not setting or not value:
                await interaction.response.send_message(
                    "❌ Please provide both setting and value for set command!", 
                    ephemeral=True
                )
                return
            await self.set_config(interaction, setting, value)
        else:
            await interaction.response.send_message(
                "❌ Invalid action! Use 'show' or 'set'.", 
                ephemeral=True
            )

    async def show_config(self, interaction: discord.Interaction):
        """Show current configuration"""
        try:
            guild_config = await self.db.get_config(interaction.guild.id)

            embed = discord.Embed(
                title="⚙️ Bot Configuration",
                color=self.config.COLOR_INFO
            )

            embed.add_field(
                name="🏆 Points System",
                value=f"Win: +{guild_config.points_win}\n"
                      f"Loss: {guild_config.points_loss}\n"
                      f"MVP: +{guild_config.points_mvp}",
                inline=True
            )

            embed.add_field(
                name="⏰ Timeouts",
                value=f"AFK Timeout: {guild_config.timeout_minutes}min\n"
                      f"No Proof Penalty: -{guild_config.no_proof_penalty} pts\n"
                      f"Proof Timeout: {guild_config.proof_timeout_minutes}min",
                inline=True
            )

            embed.add_field(
                name="🎮 Match Settings",
                value=f"Queue Size: {guild_config.queue_size}\n"
                      f"Rank Roles: {'✅' if guild_config.rank_roles_enabled else '❌'}",
                inline=True
            )

            embed.set_footer(text="Use /config set <setting> <value> to modify settings")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error showing config: {e}")
            await interaction.response.send_message(
                "❌ Error retrieving configuration!", 
                ephemeral=True
            )

    async def set_config(self, interaction: discord.Interaction, setting: str, value: str):
        """Set a configuration value"""
        try:
            setting = setting.lower()

            # Validate and convert value based on setting
            if setting in ["points_win", "points_mvp"]:
                try:
                    int_value = int(value)
                    if not ValidationHelper.validate_points(int_value):
                        await interaction.response.send_message(
                            "❌ Points value must be between -10000 and 10000!", 
                            ephemeral=True
                        )
                        return
                    await self.db.update_config(interaction.guild.id, **{setting: int_value})
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid number format!", 
                        ephemeral=True
                    )
                    return

            elif setting == "points_loss":
                try:
                    int_value = int(value)
                    if not ValidationHelper.validate_points(int_value):
                        await interaction.response.send_message(
                            "❌ Points value must be between -10000 and 10000!", 
                            ephemeral=True
                        )
                        return
                    # Make sure loss points are negative
                    if int_value > 0:
                        int_value = -int_value
                    await self.db.update_config(interaction.guild.id, **{setting: int_value})
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid number format!", 
                        ephemeral=True
                    )
                    return

            elif setting in ["timeout_minutes", "proof_timeout_minutes"]:
                try:
                    int_value = int(value)
                    if not ValidationHelper.validate_timeout_minutes(int_value):
                        await interaction.response.send_message(
                            "❌ Timeout must be between 1 and 1440 minutes!", 
                            ephemeral=True
                        )
                        return
                    await self.db.update_config(interaction.guild.id, **{setting: int_value})
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid number format!", 
                        ephemeral=True
                    )
                    return

            elif setting == "queue_size":
                try:
                    int_value = int(value)
                    if not ValidationHelper.validate_queue_size(int_value):
                        await interaction.response.send_message(
                            "❌ Queue size must be between 4 and 20!", 
                            ephemeral=True
                        )
                        return
                    await self.db.update_config(interaction.guild.id, **{setting: int_value})
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid number format!", 
                        ephemeral=True
                    )
                    return

            elif setting == "no_proof_penalty":
                try:
                    int_value = int(value)
                    if not ValidationHelper.validate_points(int_value):
                        await interaction.response.send_message(
                            "❌ Penalty must be between 0 and 10000!", 
                            ephemeral=True
                        )
                        return
                    await self.db.update_config(interaction.guild.id, **{setting: int_value})
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid number format!", 
                        ephemeral=True
                    )
                    return

            elif setting == "rank_roles_enabled":
                bool_value = value.lower() in ["true", "yes", "1", "on", "enable"]
                await self.db.update_config(interaction.guild.id, **{setting: bool_value})

            else:
                await interaction.response.send_message(
                    f"❌ Unknown setting '{setting}'!\n"
                    f"Available settings: points_win, points_loss, points_mvp, "
                    f"timeout_minutes, proof_timeout_minutes, queue_size, "
                    f"no_proof_penalty, rank_roles_enabled", 
                    ephemeral=True
                )
                return

            await interaction.response.send_message(
                f"✅ Updated {setting} to {value}!", 
                ephemeral=True
            )

        except Exception as e:
            logger.error(f"Error setting config: {e}")
            await interaction.response.send_message(
                "❌ Error updating configuration!", 
                ephemeral=True
            )

    # Points Management Commands
    @app_commands.command(name="points")
    @app_commands.describe(
        action="Action to perform (add/remove/reset/set)",
        player="Player to modify points for",
        amount="Amount of points"
    )
    async def points_command(self, interaction: discord.Interaction,
                           action: str, player: discord.Member, 
                           amount: Optional[int] = 0):
        """Manage player points"""
        action = action.lower()

        if action not in ["add", "remove", "reset", "set"]:
            await interaction.response.send_message(
                "❌ Invalid action! Use add, remove, reset, or set.", 
                ephemeral=True
            )
            return

        try:
            # Get or create player
            db_player = await self.db.get_player(player.id)
            if not db_player:
                db_player = await self.db.create_player(player.id, player.display_name)

            if action == "add":
                if not ValidationHelper.validate_points(amount):
                    await interaction.response.send_message(
                        "❌ Amount must be between -10000 and 10000!", 
                        ephemeral=True
                    )
                    return
                await self.db.update_player_points(player.id, amount)
                await interaction.response.send_message(
                    f"✅ Added {amount} points to {player.display_name}!"
                )

            elif action == "remove":
                if not ValidationHelper.validate_points(amount):
                    await interaction.response.send_message(
                        "❌ Amount must be between -10000 and 10000!", 
                        ephemeral=True
                    )
                    return
                await self.db.update_player_points(player.id, -amount)
                await interaction.response.send_message(
                    f"✅ Removed {amount} points from {player.display_name}!"
                )

            elif action == "set":
                if not ValidationHelper.validate_points(amount):
                    await interaction.response.send_message(
                        "❌ Amount must be between -10000 and 10000!", 
                        ephemeral=True
                    )
                    return
                current_points = db_player.points
                difference = amount - current_points
                await self.db.update_player_points(player.id, difference)
                await interaction.response.send_message(
                    f"✅ Set {player.display_name}'s points to {amount}!"
                )

            elif action == "reset":
                current_points = db_player.points
                difference = self.config.STARTING_POINTS - current_points
                await self.db.update_player_points(player.id, difference)
                await interaction.response.send_message(
                    f"✅ Reset {player.display_name}'s points to {self.config.STARTING_POINTS}!"
                )

        except Exception as e:
            logger.error(f"Error managing points: {e}")
            await interaction.response.send_message(
                "❌ Error managing points!", 
                ephemeral=True
            )

    # Timeout Management Commands
    @app_commands.command(name="timeout")
    @app_commands.describe(
        action="Action to perform (add/remove/check)",
        player="Player to manage timeout for",
        minutes="Timeout duration in minutes"
    )
    async def timeout_command(self, interaction: discord.Interaction,
                            action: str, player: discord.Member,
                            minutes: Optional[int] = 30):
        """Manage player timeouts"""
        action = action.lower()

        if action not in ["add", "remove", "check"]:
            await interaction.response.send_message(
                "❌ Invalid action! Use add, remove, or check.", 
                ephemeral=True
            )
            return

        try:
            # Get or create player
            db_player = await self.db.get_player(player.id)
            if not db_player:
                db_player = await self.db.create_player(player.id, player.display_name)

            if action == "add":
                if not ValidationHelper.validate_timeout_minutes(minutes):
                    await interaction.response.send_message(
                        "❌ Timeout must be between 1 and 1440 minutes!", 
                        ephemeral=True
                    )
                    return

                await self.db.set_player_timeout(player.id, minutes)
                await interaction.response.send_message(
                    f"✅ Applied {minutes} minute timeout to {player.display_name}!"
                )

            elif action == "remove":
                await self.db.remove_player_timeout(player.id)
                await interaction.response.send_message(
                    f"✅ Removed timeout from {player.display_name}!"
                )

            elif action == "check":
                if db_player.is_timed_out:
                    from utils.helpers import TimeHelper
                    time_left = TimeHelper.format_time_remaining(db_player.timeout_until)
                    await interaction.response.send_message(
                        f"⏰ {player.display_name} is timed out for {time_left}!"
                    )
                else:
                    await interaction.response.send_message(
                        f"✅ {player.display_name} is not timed out!"
                    )

        except Exception as e:
            logger.error(f"Error managing timeout: {e}")
            await interaction.response.send_message(
                "❌ Error managing timeout!", 
                ephemeral=True
            )

    # Match Management Commands
    @app_commands.command(name="scrim")
    @app_commands.describe(
        action="Action to perform",
        match_id="Match ID to manage",
        value="Additional value if needed"
    )
    async def scrim_command(self, interaction: discord.Interaction,
                          action: str, match_id: Optional[str] = None,
                          value: Optional[str] = None):
        """Manage scrimmage matches"""
        if not PermissionHelper.is_admin(interaction.user):
            await interaction.response.send_message(
                "❌ You need administrator permission for this command!", 
                ephemeral=True
            )
            return

        action = action.lower()

        if action == "cancel":
            if not match_id:
                await interaction.response.send_message(
                    "❌ Please provide a match ID to cancel!", 
                    ephemeral=True
                )
                return
            await self.force_cancel_match(interaction, match_id)

        elif action == "forcewinner":
            if not match_id or not value:
                await interaction.response.send_message(
                    "❌ Please provide match ID and team number (1 or 2)!", 
                    ephemeral=True
                )
                return
            await self.force_winner(interaction, match_id, value)

        elif action == "forcemvp":
            if not match_id or not value:
                await interaction.response.send_message(
                    "❌ Please provide match ID and player mention!", 
                    ephemeral=True
                )
                return
            await self.force_mvp(interaction, match_id, value)

        else:
            await interaction.response.send_message(
                "❌ Invalid action! Use cancel, forcewinner, or forcemvp.", 
                ephemeral=True
            )

    async def force_cancel_match(self, interaction: discord.Interaction, match_id: str):
        """Force cancel a match"""
        try:
            match = await self.db.get_match(match_id)
            if not match:
                await interaction.response.send_message(
                    f"❌ Match {match_id} not found!", 
                    ephemeral=True
                )
                return

            # Cancel match
            await self.db.cancel_match(match_id, "Admin cancelled", [])

            # Try to notify match channel
            channel = self.bot.get_channel(match.channel_id)
            if channel:
                await channel.send(f"❌ **Match {match_id} cancelled by admin.**")

            await interaction.response.send_message(
                f"✅ Match {match_id} has been cancelled!"
            )

        except Exception as e:
            logger.error(f"Error force cancelling match: {e}")
            await interaction.response.send_message(
                "❌ Error cancelling match!", 
                ephemeral=True
            )

    async def force_winner(self, interaction: discord.Interaction, match_id: str, team_str: str):
        """Force set match winner"""
        try:
            match = await self.db.get_match(match_id)
            if not match:
                await interaction.response.send_message(
                    f"❌ Match {match_id} not found!", 
                    ephemeral=True
                )
                return

            try:
                team = int(team_str)
                if team not in [1, 2]:
                    raise ValueError()
            except ValueError:
                await interaction.response.send_message(
                    "❌ Team must be 1 or 2!", 
                    ephemeral=True
                )
                return

            # Force complete match (will need MVP too)
            await self.db.complete_match(match_id, team, None, None)

            await interaction.response.send_message(
                f"✅ Forced Team {team} as winner for match {match_id}!"
            )

        except Exception as e:
            logger.error(f"Error forcing winner: {e}")
            await interaction.response.send_message(
                "❌ Error setting winner!", 
                ephemeral=True
            )

    async def force_mvp(self, interaction: discord.Interaction, match_id: str, player_mention: str):
        """Force set match MVP"""
        try:
            match = await self.db.get_match(match_id)
            if not match:
                await interaction.response.send_message(
                    f"❌ Match {match_id} not found!", 
                    ephemeral=True
                )
                return

            # Extract user ID from mention
            import re
            user_id_match = re.match(r'<@!?(\d+)>', player_mention)
            if not user_id_match:
                await interaction.response.send_message(
                    "❌ Invalid player mention!", 
                    ephemeral=True
                )
                return

            user_id = int(user_id_match.group(1))

            # Verify player is in match
            if user_id not in match.all_players:
                await interaction.response.send_message(
                    "❌ Player is not in this match!", 
                    ephemeral=True
                )
                return

            # Update match MVP
            # This would need a separate method in the database manager
            # For now, complete the match with the MVP
            await self.db.complete_match(match_id, match.winner_team or 1, user_id, None)

            await interaction.response.send_message(
                f"✅ Forced <@{user_id}> as MVP for match {match_id}!"
            )

        except Exception as e:
            logger.error(f"Error forcing MVP: {e}")
            await interaction.response.send_message(
                "❌ Error setting MVP!", 
                ephemeral=True
            )

    # Data Management Commands
    @app_commands.command(name="resetleaderboard")
    async def reset_leaderboard(self, interaction: discord.Interaction):
        """Reset the entire leaderboard (DANGEROUS)"""
        if not PermissionHelper.is_admin(interaction.user):
            await interaction.response.send_message(
                "❌ You need administrator permission for this command!", 
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "⚠️ **WARNING: This will reset ALL player data!**\n"
            "This action cannot be undone. Type `RESET LEADERBOARD` to confirm.",
            ephemeral=True
        )

        # This would need a confirmation system - skipping for now

    @app_commands.command(name="clearhistory") 
    async def clear_history(self, interaction: discord.Interaction):
        """Clear match history"""
        if not PermissionHelper.is_admin(interaction.user):
            await interaction.response.send_message(
                "❌ You need administrator permission for this command!", 
                ephemeral=True
            )
            return

        try:
            await self.db.clear_match_history(interaction.guild.id)
            await interaction.response.send_message(
                "✅ Match history has been cleared!"
            )
        except Exception as e:
            logger.error(f"Error clearing history: {e}")
            await interaction.response.send_message(
                "❌ Error clearing match history!", 
                ephemeral=True
            )

    # Utility Commands
    @app_commands.command(name="botstats")
    async def bot_stats(self, interaction: discord.Interaction):
        """Show bot statistics"""
        try:
            total_players = await self.db.get_player_match_count()

            embed = discord.Embed(
                title="🤖 Bot Statistics",
                color=self.config.COLOR_INFO
            )

            embed.add_field(
                name="📊 Database",
                value=f"Total Players: {total_players}",
                inline=True
            )

            embed.add_field(
                name="🏠 Servers",
                value=f"Connected: {len(self.bot.guilds)}",
                inline=True
            )

            embed.add_field(
                name="⚡ Performance",
                value=f"Latency: {self.bot.latency * 1000:.0f}ms",
                inline=True
            )

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error getting bot stats: {e}")
            await interaction.response.send_message(
                "❌ Error retrieving bot statistics!", 
                ephemeral=True
            )

    @app_commands.command(name="permissions")
    async def check_permissions(self, interaction: discord.Interaction):
        """Check bot permissions"""
        try:
            has_perms, missing_perms = await PermissionHelper.has_required_permissions(
                self.bot, interaction.guild
            )

            if has_perms:
                embed = EmbedBuilder.success_embed(
                    "✅ Bot has all required permissions!"
                )
            else:
                embed = EmbedBuilder.warning_embed(
                    f"⚠️ Bot is missing permissions:\n• " + "\n• ".join(missing_perms),
                    "Missing Permissions"
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Error checking permissions: {e}")
            await interaction.response.send_message(
                "❌ Error checking permissions!", 
                ephemeral=True
            )

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(AdminCommands(bot))
