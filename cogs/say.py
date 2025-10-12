import discord
from discord.ext import commands
from discord import app_commands

class Say(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="say", description="Envoie un message")
    @app_commands.describe(message="Message à envoyer")
    async def say(self, interaction: discord.Interaction, message: str = None):
        if message:
            await interaction.response.send_message(f"{interaction.user.mention} a envoyé `{message}`")
        else:
            await interaction.response.send_message(f"{interaction.user.mention} n'a rien envoyé!") 

async def setup(bot):
    await bot.add_cog(Say(bot))