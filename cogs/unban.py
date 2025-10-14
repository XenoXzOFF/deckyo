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

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]
log_channel_id = int(os.getenv('LOG_CHANNEL_ID'))

class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="unban",
        description="🔨 Débannis un utilisateur du serveur (développeurs uniquement)"
    )
    @app_commands.describe(
        utilisateur="L'utilisateur à débannir (format: nom#tag)",
        raison="La raison du débannissement"
    )
    async def unban(
        self,
        interaction: discord.Interaction,
        utilisateur: str,
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

        banned_users = await guild.bans()
        user = None
        for ban_entry in banned_users:
            if str(ban_entry.user) == utilisateur:
                user = ban_entry.user
                break

        if not user:
            await interaction.response.send_message(
                f"🚫 L'utilisateur `{utilisateur}` n'est pas banni ou n'existe pas.", ephemeral=True
            )
            return

        try:
            await guild.unban(user, reason=f"Débanni par {interaction.user} pour la raison : {raison}")
            embed = discord.Embed(
                title="🔨 Utilisateur débanni",
                description=f"L'utilisateur `{utilisateur}` a été débanni ✅\n**Raison :** {raison}",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)

            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title="🔨 Utilisateur débanni",
                    description=f"L'utilisateur `{utilisateur}` a été débanni par {interaction.user.mention}\n**Raison :** {raison}",
                    color=discord.Color.orange(),
                    timestamp=datetime.datetime.utcnow()
                )
                log_embed.set_footer(text=f"ID de l'utilisateur : {user.id}")
                await log_channel.send(embed=log_embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur de débannissement",
                description=f"Impossible de débannir l'utilisateur `{utilisateur}`.\n**Erreur :** {e}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)
            return
async def setup(bot):
    await bot.add_cog(Unban(bot))