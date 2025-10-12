import discord
from discord.ext import commands
from discord import app_commands
import datetime
import asyncio
import os

# Prends les derniers changements effectués dans le bot avec la repositorie GitHub
# Envoies les changelogs dans un embed

GITHUB_REPO_URL = int(os.getenv('GITHUB_REPO_URL'))

class Changelog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="changelog", description="Affiche les derniers changements du bot")
    async def changelog(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Récupère les 5 derniers commits depuis la repo GitHub
        async with self.bot.session.get(f"{GITHUB_REPO_URL}/commits") as response:
            if response.status != 200:
                await interaction.followup.send("Impossible de récupérer les changements pour le moment.", ephemeral=True)
                return
            commits = await response.json()

        embed = discord.Embed(
            title="📜 Derniers changements",
            description="Voici les 5 derniers changements effectués dans le bot :",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )

        for commit in commits[:5]:
            message = commit['commit']['message']
            url = commit['html_url']
            date = commit['commit']['author']['date']
            author = commit['commit']['author']['name']
            embed.add_field(
                name=f"🔹 {message.splitlines()[0]}",
                value=f"Auteur: {author}\nDate: {date}\n[Voir le commit]({url})",
                inline=False
            )

        embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")
        await interaction.followup.send(embed=embed, ephemeral=True)
async def setup(bot):
    await bot.add_cog(Changelog(bot))