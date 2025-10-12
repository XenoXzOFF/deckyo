import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime

WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID'))

class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Envoie un message de bienvenue lorsqu'un nouveau membre rejoint le serveur."""
        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="Bienvenue!",
                description=f"Bienvenue sur le serveur, {member.mention}!\nNous sommes ravis de t'avoir parmi nous.",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.set_footer(text="Passe un bon moment ici!")
            await channel.send(embed=embed)

    @app_commands.command(name="welcome", description="Envoie un message de bienvenue personnalisé.")
    @app_commands.describe(member="Le membre à qui envoyer le message de bienvenue.")
    async def welcome(self, interaction: discord.Interaction, member: discord.Member):
        """Commande slash pour envoyer un message de bienvenue personnalisé."""
        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="Bienvenue!",
                description=f"Bienvenue sur le serveur, {member.mention}!\nNous sommes ravis de t'avoir parmi nous.",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.set_footer(text="Passe un bon moment ici!")
            await channel.send(embed=embed)
            await interaction.response.send_message(f"Message de bienvenue envoyé pour {member.mention}.", ephemeral=True)
        else:
            await interaction.response.send_message("Le canal de bienvenue n'a pas été trouvé.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))