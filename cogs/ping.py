import discord
from discord.ext import commands
from discord import app_commands
import datetime

class ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="🏓 Affiche la latence du bot")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"La latence du bot est de `{latency} ms`",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ping(bot))