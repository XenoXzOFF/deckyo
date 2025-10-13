import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="8ball",
        description="🎱 Pose une question et obtiens une réponse mystérieuse"
    )
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        responses = [
            "C'est certain ✨",
            "Sans aucun doute 💫",
            "Très probable 🌟",
            "Oui ⭐",
            "C'est non 🌑",
            "Peu probable 💫",
            "N'y compte pas 🌘",
            "Impossible de prédire 🌗",
            "Repose ta question 🌓",
            "Concentre-toi et redemande 🌔"
        ]
        
        embed = discord.Embed(
            title="🎱 La boule magique a parlé !",
            color=discord.Color.purple()
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Réponse", value=random.choice(responses), inline=False)
        embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="coinflip",
        description="🎲 Lance une pièce"
    )
    async def coinflip(self, interaction: discord.Interaction):
        choices = ["Pile 🦅", "Face 👑"]
        result = random.choice(choices)
        
        embed = discord.Embed(
            title="🎲 Lancer de pièce",
            description=f"La pièce tourne...",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
        message = await interaction.response.send_message(embed=embed)        
        await asyncio.sleep(2)
        
        embed.description = f"**Résultat:** {result}"
        await interaction.edit_original_response(embed=embed)

    @app_commands.command(
        name="roll",
        description="🎲 Lance un dé avec le nombre de faces spécifié"
    )
    async def roll(self, interaction: discord.Interaction, faces: int = 6):
        if faces < 2:
            await interaction.response.send_message("❌ Le dé doit avoir au moins 2 faces!", ephemeral=True)
            return
            
        result = random.randint(1, faces)
        
        embed = discord.Embed(
            title="🎲 Lancer de dé",
            description=f"Le dé à {faces} faces roule...",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
        await interaction.response.send_message(embed=embed)
        
        
        await asyncio.sleep(2)
        
        embed.description = f"**Résultat:** {result}"
        await interaction.edit_original_response(embed=embed)

    @app_commands.command(
        name="choice",
        description="🎯 Fait un choix aléatoire parmi les options données"
    )
    async def choice(self, interaction: discord.Interaction, options: str):
        choices = [option.strip() for option in options.split(",")]
        
        if len(choices) < 2:
            await interaction.response.send_message(
                "❌ Tu dois donner au moins 2 options séparées par des virgules!",
                ephemeral=True
            )
            return
            
        embed = discord.Embed(
            title="🎯 Choix aléatoire",
            description="Je réfléchis...",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
        await interaction.response.send_message(embed=embed)
        
        await asyncio.sleep(2)
        
        chosen = random.choice(choices)
        embed.description = f"**J'ai choisi:** {chosen}"
        await interaction.edit_original_response(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))