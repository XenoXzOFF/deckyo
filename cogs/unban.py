import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime
import asyncio

# L'utilisateur doit avoir la permissions de debannir des membres
# L'utilisateur banni doit recevoir un message privé lui indiquant qu'il a été debanni et la raison
# Le bot doit logger l'action dans un salon spécifique
# L'utilisateur peut debannir un utilisateur
# Utiliser des embeds pour les messages envoyés par le bot, les logs et les messages privés
# Mettre dans la raison du ban discord le nom de l'utilisateur qui a debanni, la raison et la durée si applicable
# Utiliser l'id du membre banni et non son nom d'utilisateur pour le debannir

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]
log_channel_id = int(os.getenv('LOG_CHANNEL_ID'))

class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="unban",
        description="🔓 Débannis un utilisateur du serveur (admins uniquement)"
    )
    @app_commands.describe(
        utilisateur_id="L'ID de l'utilisateur à débannir",
        raison="La raison du débannissement"
    )
    async def unban(
        self,
        interaction: discord.Interaction,
        utilisateur_id: str,
        raison: str
    ):
        """Débannis un utilisateur du serveur avec une raison"""
        if interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message(
                "🚫 Tu n’as pas la permission d’utiliser cette commande.", ephemeral=True
            )
            return

        guild = interaction.guild
        if not guild:
            await interaction.response.send_message(
                "🚫 Cette commande doit être utilisée dans un serveur.", ephemeral=True
            )
            return

        try:
            utilisateur_id_int = int(utilisateur_id)
        except ValueError:
            await interaction.response.send_message(
                "🚫 L'ID utilisateur doit être un nombre valide.", ephemeral=True
            )
            return

        try:
            banned_users = await guild.bans()
            user_to_unban = discord.utils.get(banned_users, user__id=utilisateur_id_int)

            if not user_to_unban:
                await interaction.response.send_message(
                    f"🚫 Aucun utilisateur banni trouvé avec l'ID {utilisateur_id}.", ephemeral=True
                )
                return

            await guild.unban(user_to_unban.user, reason=f"Débanni par {interaction.user} pour la raison : {raison}")

            embed = discord.Embed(
                title="🔓 Utilisateur débanni",
                description=f"L'utilisateur `{user_to_unban.user}` a été débanni ✅\n**Raison :** {raison}",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)

            # Log dans le salon de log
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title="🔓 Utilisateur débanni",
                    description=f"L'utilisateur `{user_to_unban.user}` a été débanni par {interaction.user} ✅\n**Raison :** {raison}",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.utcnow()
                )
                await log_channel.send(embed=log_embed)
        except Exception as e:
            await interaction.response.send_message(
                f"🚫 Une erreur est survenue lors du débannissement : {e}", ephemeral=True
            )
async def setup(bot):
    await bot.add_cog(Unban(bot))
