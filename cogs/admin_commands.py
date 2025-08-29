import discord
from discord.ext import commands
from discord import app_commands

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="config")
    async def config_command(self, interaction: discord.Interaction):
        await interaction.response.send_message("Config command placeholder", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))