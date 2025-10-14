import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime
import asyncio

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]
log_channel_id = int(os.getenv('LOG_CHANNEL_ID'))

class Clear(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name="clear",
        description="🧹 Supprime un certain nombre de messages dans le salon (admins uniquement)"
    )
    @app_commands.describe(
        nombre="Le nombre de messages à supprimer (max 100)"
    )
    async def clear(
        self,
        interaction: discord.Interaction,
        nombre: int
    ):
        """Supprime un certain nombre de messages dans le salon"""
        if interaction.user.id not in OWNER_IDS and not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "🚫 Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True
            )
            return

        if nombre < 1 or nombre > 100:
            await interaction.response.send_message(
                "🚫 Le nombre de messages à supprimer doit être entre 1 et 100.", ephemeral=True
            )
            return

        try:
            now = discord.utils.utcnow()
            deleted = await interaction.channel.purge(
                limit=nombre,
                check=lambda m: (now - m.created_at).days < 14
            )
            
            embed = discord.Embed(
                title="🧹 Messages supprimés",
                description=f"{len(deleted)} message(s) ont été supprimés dans {interaction.channel.mention} ✅",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await asyncio.sleep(5)
            try:
                await interaction.delete_original_response()
            except Exception:
                pass

            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title="🧹 Action de nettoyage",
                    description=f"{interaction.user.mention} a supprimé {len(deleted)} message(s) dans {interaction.channel.mention}.",
                    color=discord.Color.blue(),
                    timestamp=discord.utils.utcnow()
                )
                log_embed.set_footer(text=f"ID de l'utilisateur : {interaction.user.id}")
                await log_channel.send(embed=log_embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur de suppression",
                description=f"Impossible de supprimer les messages.\n**Erreur :** {e}",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await asyncio.sleep(5)
            try:
                await interaction.delete_original_response()
            except Exception:
                pass

async def setup(bot):
    await bot.add_cog(Clear(bot))