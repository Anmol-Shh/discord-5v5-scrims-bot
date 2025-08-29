"""
5v5 Scrims Discord Bot - Main Entry Point
"""

import asyncio
import logging
import os

import discord
from discord.ext import commands

from config import Config
from database.db_manager import DatabaseManager

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
        logger.info("Setting up bot...")
        self.db = DatabaseManager()
        await self.db.initialize()

        for cog in [
            'cogs.queue_system',
            'cogs.match_management',
            'cogs.admin_commands',
            'cogs.leaderboard',
            'cogs.utility'
        ]:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")
        logger.info("Bot setup complete!")

    async def on_ready(self):
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Connected to {len(self.guilds)} guilds')

        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for scrims | /help"
        )
        await self.change_presence(activity=activity, status=discord.Status.online)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("âŒ You don't have permission to use this command!")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("âŒ I don't have the required permissions to execute this command!")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"â° Command on cooldown. Try again in {error.retry_after:.2f}s")
        else:
            logger.error(f"Unhandled error: {error}")
            await ctx.send("âŒ An unexpected error occurred!")

    async def close(self):
        logger.info("Shutting down bot...")
        if self.db:
            await self.db.close()
        await super().close()

async def main():
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