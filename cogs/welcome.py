import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime

WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID'))

class WelcomeMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        if not channel:
            print(f"⚠️ Salon de bienvenue introuvable : {WELCOME_CHANNEL_ID}")
            return

        embed = discord.Embed(
            title="Bienvenue!",
            description=f"Bienvenue sur le serveur, {member.mention}!\nNous sommes ravis de t'avoir parmi nous. N'oublie pas de lire les règles et de te présenter dans le salon approprié.",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
         )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")

        await channel.send(embed=embed)
async def setup(bot):
    await bot.add_cog(WelcomeMessage(bot))