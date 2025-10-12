import discord
from discord.ext import commands
from discord import app_commands
import datetime
import os
import asyncio

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]



class DeleteRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="deleterole",
        description="🗑️ Supprime un rôle du serveur (développeurs uniquement)"
    )
    @app_commands.describe(
        role="Le rôle à supprimer"
    )
    async def deleterole(
        self,
        interaction: discord.Interaction,
        role: discord.Role
    ):
        """Supprime un rôle spécifique du serveur"""
        if interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message(
                "🚫 Tu n’as pas la permission d’utiliser cette commande.", ephemeral=True
            )
            return

        try:
            await role.delete()
            embed = discord.Embed(
                title="🗑️ Rôle supprimé",
                description=f"Le rôle `{role.name}` a été supprimé du serveur ✅",
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
                title="❌ Erreur de suppression",
                description=f"Impossible de supprimer le rôle `{role.name}`.\n**Erreur :** {e}",
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
    await bot.add_cog(DeleteRole(bot))