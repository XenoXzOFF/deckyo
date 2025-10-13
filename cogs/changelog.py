import discord
from discord.ext import commands
from discord import app_commands
import datetime
import asyncio
import aiohttp

# URL de l'API GitHub pour récupérer les commits
GITHUB_API_URL = "https://api.github.com/repos/XenoXzOFF/deckyo/commits"

class Changelog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        # Ferme proprement la session aiohttp quand le cog est déchargé
        asyncio.create_task(self.session.close())

    @app_commands.command(
        name="changelog",
        description="Affiche les 5 derniers changements du bot depuis GitHub"
    )
    async def changelog(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            async with self.session.get(GITHUB_API_URL) as response:
                if response.status != 200:
                    await interaction.followup.send(
                        "Impossible de récupérer les changements pour le moment.",
                        ephemeral=True
                    )
                    return

                commits = await response.json()  # JSON des commits

        except Exception as e:
            await interaction.followup.send(
                f"Erreur lors de la récupération des commits : {e}",
                ephemeral=True
            )
            return

        # Crée l'embed pour Discord
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

        embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Changelog(bot))
