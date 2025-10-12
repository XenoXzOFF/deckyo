import discord
from discord.ext import commands
from discord import app_commands
import os

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]

class Errors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if interaction.user.id in OWNER_IDS:
            await interaction.response.send_message(f"🚫 Une erreur est survenue : {error}", ephemeral=True)
        else:
            await interaction.response.send_message("🚫 Une erreur est survenue lors de l'exécution de la commande.", ephemeral=True)
        # Log the error details to console for developers
        print(f"Erreur dans la commande {interaction.command.name} : {error}")
        import traceback
        traceback.print_exception(type(error), error, error.__traceback__)
async def setup(bot):
    await bot.add_cog(Errors(bot))
    