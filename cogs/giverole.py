import discord
from discord.ext import commands
from discord import app_commands
import datetime
import os
import asyncio

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]

class GiveRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="giverole",
        description="🎖️ Donne un rôle à un utilisateur (développeurs uniquement)"
    )
    @app_commands.describe(
        utilisateur="L'utilisateur à qui donner le rôle",
        role="Le rôle à donner"
    )
    async def giverole(
        self,
        interaction: discord.Interaction,
        utilisateur: discord.Member,
        role: discord.Role
    ):
        """Donne un rôle spécifique à un utilisateur"""
        if interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message(
                "🚫 Tu n’as pas la permission d’utiliser cette commande.", ephemeral=True
            )
            return

        try:
            await utilisateur.add_roles(role)
            embed = discord.Embed(
                title="🎖️ Rôle attribué",
                description=f"Le rôle `{role.name}` a été donné à {utilisateur.mention} ✅",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")
            await interaction.response.send_message(embed=embed)
            await asyncio.sleep(5)
            try:
                await interaction.delete_original_response()
            except Exception: pass
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur d'attribution",
                description=f"Impossible de donner le rôle `{role.name}` à {utilisateur.mention}.\n**Erreur :** {e}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")
            await interaction.response.send_message(embed=embed)
            await asyncio.sleep(5)
            try:
                await interaction.delete_original_response()
            except Exception: pass

async def setup(bot):
    await bot.add_cog(GiveRole(bot))