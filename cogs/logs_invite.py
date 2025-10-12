import discord
from discord.ext import commands
import datetime
import traceback
import asyncio
import os

LOG_INVITE_CHANNEL_ID = int(os.getenv('LOG_INVITE_CHANNEL_ID'))

class InviteLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_log(self, embed: discord.Embed):
        channel = self.bot.get_channel(LOG_INVITE_CHANNEL_ID)
        if not channel:
            print(f"⚠️ Salon de logs introuvable : {LOG_INVITE_CHANNEL_ID}")
            return
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        embed = discord.Embed(title="🤖 Bot ajouté à un serveur", color=discord.Color.green(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Nom du serveur", value=guild.name, inline=False)
        embed.add_field(name="ID du serveur", value=guild.id, inline=False)
        embed.add_field(name="Propriétaire", value=f"{guild.owner} ({guild.owner_id})", inline=False)
        embed.add_field(name="Membres", value=guild.member_count, inline=False)
        embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")
        await self.send_log(embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        embed = discord.Embed(title="❌ Bot retiré d'un serveur", color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Nom du serveur", value=guild.name, inline=False)
        embed.add_field(name="ID du serveur", value=guild.id, inline=False)
        embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")
        await self.send_log(embed)

async def setup(bot):
    await bot.add_cog(InviteLogs(bot))
