"""
Utility Cog for 5v5 Scrims Bot
Handles help commands, general utilities, and bot information
"""

import logging
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

from database.db_manager import DatabaseManager
from utils.embeds import EmbedBuilder
from utils.constants import HELP_TEXT, STATUS_MESSAGES
from utils.helpers import PermissionHelper
from config import Config

logger = logging.getLogger(__name__)

class HelpView(discord.ui.View):
    """View for help command with different sections"""

    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label='Player Commands', style=discord.ButtonStyle.primary, emoji='👤')
    async def player_commands(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="👤 Player Commands",
            color=Config.COLOR_INFO
        )
        embed.add_field(
            name="Queue Commands",
            value="• Click 🟢 to **Join Queue**\n"
                  "• Click 🔴 to **Leave Queue**\n"
                  "• Queue fills automatically when 10 players join",
            inline=False
        )
        embed.add_field(
            name="Statistics",
            value="• `/stats` - View your personal statistics\n"
                  "• `/stats @player` - View another player's stats\n"
                  "• `/rank` - Check your current rank",
            inline=False
        )
        embed.add_field(
            name="Leaderboards & History",
            value="• `/leaderboard` - View points leaderboard\n"
                  "• `/history` - View recent match history\n"
                  "• `/top points/wins/mvp` - View top players",
            inline=False
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='Match Commands', style=discord.ButtonStyle.secondary, emoji='⚔️')
    async def match_commands(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⚔️ Match Commands (Leaders Only)",
            color=Config.COLOR_MATCH
        )
        embed.add_field(
            name="Drafting Phase",
            value="• Click player buttons to draft them to your team\n"
                  "• Leader A gets first pick, alternating turns\n"
                  "• Leader B must create the lobby",
            inline=False
        )
        embed.add_field(
            name="Lobby Creation",
            value="• Click **📌 Share Lobby ID** to enter lobby code\n"
                  "• Click **❌ Cancel Match** if players don't join\n"
                  "• Lobby ID should be the custom game code",
            inline=False
        )
        embed.add_field(
            name="Post-Game Voting",
            value="• Both leaders vote for **winning team**\n"
                  "• Both leaders select **MVP player**\n"
                  "• Winning leader uploads **screenshot proof**",
            inline=False
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='Admin Commands', style=discord.ButtonStyle.danger, emoji='⚙️')
    async def admin_commands(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not PermissionHelper.is_moderator(interaction.user):
            await interaction.response.send_message(
                "❌ You need moderator permissions to view admin commands!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="⚙️ Admin Commands",
            color=Config.COLOR_WARNING
        )
        embed.add_field(
            name="Configuration",
            value="• `/config show` - View current settings\n"
                  "• `/config set <setting> <value>` - Modify settings\n"
                  "• `/permissions` - Check bot permissions",
            inline=False
        )
        embed.add_field(
            name="Player Management",
            value="• `/points add/remove/set @player <amount>`\n"
                  "• `/timeout add/remove @player [minutes]`\n"
                  "• `/timeout check @player` - Check timeout status",
            inline=False
        )
        embed.add_field(
            name="Match Management",
            value="• `/scrim cancel <match_id>` - Force cancel match\n"
                  "• `/scrim forcewinner <match_id> <team>`\n"
                  "• `/scrim forcemvp <match_id> @player`",
            inline=False
        )
        embed.add_field(
            name="Data Management",
            value="• `/clearhistory` - Clear all match history\n"
                  "• `/resetleaderboard` - Reset all player data\n"
                  "• `/botstats` - View bot statistics",
            inline=False
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='Ranking System', style=discord.ButtonStyle.success, emoji='🏅')
    async def ranking_system(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏅 Ranking System",
            color=Config.COLOR_SUCCESS
        )

        ranks_text = []
        for rank, points in sorted(Config.RANK_THRESHOLDS.items(), key=lambda x: x[1]):
            if rank == "RADIANT":
                ranks_text.append("🌟 **Radiant** - Top 5 players")
            else:
                emoji = Config.RANK_ROLE_NAMES.get(rank, rank).split()[0]
                rank_name = Config.RANK_ROLE_NAMES.get(rank, rank).split(" ", 1)[1]
                if points == 0:
                    ranks_text.append(f"{emoji} **{rank_name}** - {points}+ points")
                else:
                    ranks_text.append(f"{emoji} **{rank_name}** - {points}+ points")

        embed.add_field(
            name="Rank Tiers",
            value="\n".join(ranks_text),
            inline=False
        )

        embed.add_field(
            name="Point System",
            value="• **Win**: +30 points\n"
                  "• **Loss**: -30 points\n"
                  "• **MVP**: +10 additional points\n"
                  "• **AFK/No Show**: 30 minute timeout\n"
                  "• **No Proof**: -100 points (leaders only)",
            inline=False
        )

        embed.add_field(
            name="Rank Roles",
            value="Rank roles are automatically assigned based on your points!\n"
                  "**Radiant** is reserved for the top 5 players on the leaderboard.",
            inline=False
        )

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='How to Play', style=discord.ButtonStyle.success, emoji='🎮')
    async def how_to_play(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎮 How to Play 5v5 Scrims",
            color=Config.COLOR_SUCCESS
        )

        steps = [
            "**1. Join Queue** - Click 🟢 in the queue channel",
            "**2. Wait for Full Queue** - Need 10 players total",
            "**3. Bot Creates Match** - Private channel for your match",
            "**4. Random Leaders** - Two players chosen as team captains",
            "**5. Draft Teams** - Leaders alternate picking players",
            "**6. Create Lobby** - Leader B makes custom game lobby",
            "**7. Play Match** - Join lobby and play your game",
            "**8. Vote Results** - Leaders vote winner and MVP",
            "**9. Upload Proof** - Winning leader posts screenshot",
            "**10. Get Points** - Points awarded, ranks updated!"
        ]

        embed.add_field(
            name="Match Flow",
            value="\n".join(steps),
            inline=False
        )

        embed.add_field(
            name="Important Rules",
            value="• **Be Ready** - Join lobby when match starts\n"
                  "• **Screenshot Required** - Winners must provide proof\n"
                  "• **Both Leaders Vote** - Must agree on winner/MVP\n"
                  "• **30 Min Timeout** - For AFK or no-show players",
            inline=False
        )

        await interaction.response.edit_message(embed=embed, view=self)

class Utility(commands.Cog):
    """General utility commands and help system"""

    def __init__(self, bot):
        self.bot = bot
        self.db: DatabaseManager = bot.db
        self.config = Config()

    @app_commands.command(name="help")
    async def help_command(self, interaction: discord.Interaction):
        """Show help information about the bot"""
        embed = discord.Embed(
            title="📘 5v5 Scrims Bot Help",
            description="Welcome to the 5v5 Scrims Bot! This bot manages competitive 5v5 matches with drafting, rankings, and statistics.",
            color=self.config.COLOR_INFO
        )

        embed.add_field(
            name="🚀 Quick Start",
            value="1. Join the queue by clicking 🟢\n"
                  "2. Wait for 10 players to join\n"
                  "3. Bot will create your match!",
            inline=False
        )

        embed.add_field(
            name="📖 Need More Help?",
            value="Use the buttons below to explore different sections:\n"
                  "• **Player Commands** - Basic commands for all users\n"
                  "• **Match Commands** - Commands for team leaders\n"
                  "• **Admin Commands** - Administrative functions\n"
                  "• **Ranking System** - How points and ranks work\n"
                  "• **How to Play** - Step-by-step match guide",
            inline=False
        )

        embed.add_field(
            name="🔗 Quick Links",
            value="• `/stats` - Your statistics\n"
                  "• `/leaderboard` - Points leaderboard\n"
                  "• `/history` - Recent matches",
            inline=False
        )

        embed.set_footer(text="Click the buttons below for detailed help!")

        view = HelpView()
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="about")
    async def about(self, interaction: discord.Interaction):
        """Show information about the bot"""
        embed = discord.Embed(
            title="🤖 About 5v5 Scrims Bot",
            description="A comprehensive Discord bot for managing competitive 5v5 scrimmage matches.",
            color=self.config.COLOR_INFO
        )

        embed.add_field(
            name="✨ Features",
            value="• **Queue System** - Automatic matchmaking\n"
                  "• **Team Drafting** - Snake draft with visible stats\n"
                  "• **Match Management** - Lobby creation & voting\n"
                  "• **Points & Rankings** - Competitive progression\n"
                  "• **Statistics** - Detailed player analytics\n"
                  "• **Match History** - Complete game records",
            inline=False
        )

        embed.add_field(
            name="📊 Statistics",
            value=f"• **Servers**: {len(self.bot.guilds)}\n"
                  f"• **Latency**: {self.bot.latency * 1000:.0f}ms\n"
                  f"• **Uptime**: {self.get_uptime()}",
            inline=True
        )

        embed.add_field(
            name="🛠️ Technical",
            value="• **Language**: Python 3.12\n"
                  "• **Framework**: discord.py\n"
                  "• **Database**: PostgreSQL",
            inline=True
        )

        embed.set_footer(text="Use /help for commands and usage information")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ping")
    async def ping(self, interaction: discord.Interaction):
        """Check bot latency and response time"""
        start_time = datetime.utcnow()

        embed = discord.Embed(
            title="🏓 Pong!",
            color=self.config.COLOR_INFO
        )

        # Discord API latency
        api_latency = self.bot.latency * 1000

        embed.add_field(
            name="📡 Discord API",
            value=f"{api_latency:.0f}ms",
            inline=True
        )

        await interaction.response.send_message(embed=embed)

        # Calculate response time
        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds() * 1000

        embed.add_field(
            name="⚡ Response Time",
            value=f"{response_time:.0f}ms",
            inline=True
        )

        # Database ping (simple query)
        try:
            db_start = datetime.utcnow()
            await self.db.get_player_match_count()
            db_end = datetime.utcnow()
            db_latency = (db_end - db_start).total_seconds() * 1000

            embed.add_field(
                name="💾 Database",
                value=f"{db_latency:.0f}ms",
                inline=True
            )
        except Exception:
            embed.add_field(
                name="💾 Database",
                value="Error",
                inline=True
            )

        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="invite")
    async def invite(self, interaction: discord.Interaction):
        """Get bot invite link"""
        # Generate invite URL with required permissions
        permissions = discord.Permissions(
            send_messages=True,
            embed_links=True,
            attach_files=True,
            read_message_history=True,
            manage_messages=True,
            manage_channels=True,
            manage_roles=True,
            use_slash_commands=True
        )

        invite_url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=permissions,
            scopes=["bot", "applications.commands"]
        )

        embed = discord.Embed(
            title="🔗 Invite 5v5 Scrims Bot",
            description="Add this bot to your server to start hosting 5v5 scrims!",
            color=self.config.COLOR_SUCCESS
        )

        embed.add_field(
            name="Required Permissions",
            value="• Send Messages & Embeds\n"
                  "• Attach Files\n"
                  "• Manage Messages\n"
                  "• Manage Channels\n"
                  "• Manage Roles\n"
                  "• Use Slash Commands",
            inline=False
        )

        embed.add_field(
            name="Setup Steps",
            value="1. Click the invite link below\n"
                  "2. Select your server\n"
                  "3. Grant the required permissions\n"
                  "4. Use `/queue` to set up the queue channel\n"
                  "5. Configure with `/config` if needed",
            inline=False
        )

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="Invite Bot",
                url=invite_url,
                style=discord.ButtonStyle.link,
                emoji="🔗"
            )
        )

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="status")
    async def status(self, interaction: discord.Interaction):
        """Show bot status and system information"""
        embed = discord.Embed(
            title="📊 Bot Status",
            color=self.config.COLOR_INFO,
            timestamp=datetime.utcnow()
        )

        # Basic stats
        embed.add_field(
            name="🏠 Servers",
            value=str(len(self.bot.guilds)),
            inline=True
        )

        embed.add_field(
            name="👥 Users",
            value=str(len(self.bot.users)),
            inline=True
        )

        embed.add_field(
            name="📡 Latency",
            value=f"{self.bot.latency * 1000:.0f}ms",
            inline=True
        )

        # Database stats
        try:
            total_players = await self.db.get_player_match_count()
            embed.add_field(
                name="🎮 Total Players",
                value=str(total_players),
                inline=True
            )
        except Exception:
            embed.add_field(
                name="🎮 Total Players",
                value="Error",
                inline=True
            )

        embed.add_field(
            name="⏰ Uptime",
            value=self.get_uptime(),
            inline=True
        )

        embed.add_field(
            name="🔋 Status",
            value="🟢 Online",
            inline=True
        )

        embed.set_footer(text="Bot is running smoothly!")

        await interaction.response.send_message(embed=embed)

    def get_uptime(self) -> str:
        """Get bot uptime as formatted string"""
        # This would need to track bot start time
        # For now, return a placeholder
        return "Running"

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync_commands(self, ctx):
        """Sync slash commands (Owner only)"""
        try:
            synced = await self.bot.tree.sync()
            await ctx.send(f"✅ Synced {len(synced)} command(s)!")
        except Exception as e:
            await ctx.send(f"❌ Failed to sync commands: {e}")

    @app_commands.command(name="support")
    async def support(self, interaction: discord.Interaction):
        """Get support information"""
        embed = discord.Embed(
            title="🆘 Support & Help",
            description="Need help with the 5v5 Scrims Bot? Here are your options:",
            color=self.config.COLOR_INFO
        )

        embed.add_field(
            name="📖 Documentation",
            value="• Use `/help` for command information\n"
                  "• Use `/about` for bot details\n"
                  "• Check command descriptions in Discord",
            inline=False
        )

        embed.add_field(
            name="🔧 Common Issues",
            value="• **Bot not responding**: Check permissions\n"
                  "• **Commands not working**: Try `/permissions`\n"
                  "• **Queue not working**: Recreate with `/queue`\n"
                  "• **Rank roles not updating**: Enable in `/config`",
            inline=False
        )

        embed.add_field(
            name="⚙️ Admin Tools",
            value="• `/config show` - Check current settings\n"
                  "• `/permissions` - Verify bot permissions\n"
                  "• `/botstats` - View bot statistics",
            inline=False
        )

        embed.set_footer(text="Still need help? Contact your server administrators.")

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(Utility(bot))
