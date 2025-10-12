import discord
from discord.ext import commands
from discord import app_commands

class Bombe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="bombe", description="💣 Envoie une bombe à un utilisateur (optionnel)")
    @app_commands.describe(utilisateur="La personne à qui tu veux envoyer une bombe 💥")
    async def bombe(self, interaction: discord.Interaction, utilisateur: discord.User = None):
        if utilisateur:
            await interaction.response.send_message(f"💣 {interaction.user.mention} a lancé une bombe sur {utilisateur.mention} 💥")
        else:
            await interaction.response.send_message("💥 BOUM ! La bombe a explosé toute seule !")

async def setup(bot):
    await bot.add_cog(Bombe(bot))
