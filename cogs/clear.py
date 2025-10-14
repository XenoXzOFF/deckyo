import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime
import asyncio

# L'utilisateur doit avoir la permissions de supprimer des messages
# Le bot doit logger l'action dans un salon spécifique
# L'utilisateur peut supprimer un certain nombre de messages
# Utiliser des embeds pour les messages envoyés par le bot, les logs
# Les OWNER_IDS peuvent supprimer des messages
# Ne pas pouvoir supprimer les messages plus vieux que 14 jours (limite de l'API Discord)
# Supprimer le message de confirmation après quelques secondes

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
                "🚫 Tu n’as pas la permission d’utiliser cette commande.", ephemeral=True
            )
            return

        if nombre < 1 or nombre > 100:
            await interaction.response.send_message(
                "🚫 Le nombre de messages à supprimer doit être entre 1 et 100.", ephemeral=True
            )
            return

        try:
            deleted = await interaction.channel.purge(limit=nombre + 1, check=lambda m: (datetime.datetime.utcnow() - m.created_at).days < 14)
            embed = discord.Embed(
                title="🧹 Messages supprimés",
                description=f"{len(deleted)-1} messages ont été supprimés dans {interaction.channel.mention} ✅",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await asyncio.sleep(5)
            try:
                await interaction.delete_original_response()
            except Exception: pass

            # Log dans le salon de log
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title="🧹 Action de nettoyage",
                    description=f"{interaction.user.mention} a supprimé {len(deleted)-1} messages dans {interaction.channel.mention}.",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.utcnow()
                )
                log_embed.set_footer(text=f"ID de l'utilisateur : {interaction.user.id}")
                await log_channel.send(embed=log_embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur de suppression",
                description=f"Impossible de supprimer les messages.\n**Erreur :** {e}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
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