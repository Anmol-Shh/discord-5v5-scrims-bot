"""
5v5 Scrims Discord Bot - Main Entry Point
A comprehensive Discord bot for managing 5v5 scrimmage matches with queue system,
team drafting, match management, and ranking system.
"""

import asyncio
import logging
import os
from pathlib import Path

import discord
from discord.ext import commands

from config import Config
from database.db_manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScrimsBot(commands.Bot):
    """Custom bot class for 5v5 Scrims Bot"""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(
            command_prefix=Config.BOT_PREFIX,
            intents=intents,
            help_command=None,
            case_insensitive=True
        )

        self.db: DatabaseManager = None
        self.config = Config()

    async def setup_hook(self):
        """Initialize the bot and load extensions"""
        logger.info("Setting up bot...")

        # Initialize database
        self.db = DatabaseManager()
        await self.db.initialize()

        # Load all cogs
        cogs_to_load = [
            'cogs.queue_system',
            'cogs.match_management', 
            'cogs.admin_commands',
            'cogs.leaderboard',
            'cogs.utility'
        ]

        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")

        logger.info("Bot setup complete!")

    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Connected to {len(self.guilds)} guilds')

        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for scrims | /help"
        )
        await self.change_presence(activity=activity, status=discord.Status.online)

    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command!")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ I don't have the required permissions to execute this command!")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command on cooldown. Try again in {error.retry_after:.2f}s")
        else:
            logger.error(f"Unhandled error: {error}")
            await ctx.send("❌ An unexpected error occurred!")

    async def close(self):
        """Cleanup when bot shuts down"""
        logger.info("Shutting down bot...")
        if self.db:
            await self.db.close()
        await super().close()

async def main():
    """Main function to run the bot"""
    bot = ScrimsBot()

    try:
        await bot.start(Config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
