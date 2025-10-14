import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime
import asyncio

# L'utilisateur doit avoir la permissions de bannir des membres
# L'utilisateur banni doit recevoir un message privé lui indiquant qu'il a été banni et la raison
# Le bot doit logger l'action dans un salon spécifique
# L'utilisateur peut bannir un utilisateur en spécifiant une durée (ex: 7d pour 7 jours, 12h pour 12 heures, 30m pour 30 minutes)
# Utiliser des embeds pour les messages envoyés par le bot, les logs et les messages privés
# Mettre dans la raison du ban discord le nom de l'utilisateur qui a banni, la raison et la durée si applicable

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]
log_channel_id = int(os.getenv('LOG_CHANNEL_ID'))

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ban",
        description="🔨 Bannis un utilisateur du serveur (admins uniquement)"
    )
    @app_commands.describe(
        utilisateur="L'utilisateur à bannir",
        raison="La raison du ban",
        duree="La durée du ban (ex: 7d pour 7 jours, 12h pour 12 heures, 30m pour 30 minutes) - optionnel"
    )
    async def ban(
        self,
        interaction: discord.Interaction,
        utilisateur: discord.Member,
        raison: str,
        duree: str = None
    ):
        """Bannis un utilisateur du serveur avec une raison et une durée optionnelle"""
        # Vérifier si l'utilisateur est owner ou a la permission de bannir
        if interaction.user.id not in OWNER_IDS and not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(
                "🚫 Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True
            )
            return

        guild = interaction.guild
        if not guild:
            await interaction.response.send_message(
                "🚫 Cette commande doit être utilisée dans un serveur.", ephemeral=True
            )
            return

        if utilisateur == interaction.user:
            await interaction.response.send_message(
                "🚫 Tu ne peux pas te bannir toi-même.", ephemeral=True
            )
            return

        if utilisateur == guild.owner:
            await interaction.response.send_message(
                "🚫 Tu ne peux pas bannir le propriétaire du serveur.", ephemeral=True
            )
            return

        if not guild.me.guild_permissions.ban_members:
            await interaction.response.send_message(
                "🚫 Je n'ai pas la permission de bannir des membres.", ephemeral=True
            )
            return

        if utilisateur.top_role >= interaction.user.top_role and interaction.user != guild.owner:
            await interaction.response.send_message(
                "🚫 Tu ne peux pas bannir cet utilisateur car son rôle est supérieur ou égal au tien.", ephemeral=True
            )
            return

        if utilisateur.top_role >= guild.me.top_role:
            await interaction.response.send_message(
                "🚫 Je ne peux pas bannir cet utilisateur car son rôle est supérieur ou égal au mien.", ephemeral=True
            )
            return
        duration = None
        if duree:
            time_unit = duree[-1]
            if time_unit not in ['d', 'h', 'm']:
                await interaction.response.send_message(
                    "🚫 La durée doit se terminer par 'd' (jours), 'h' (heures) ou 'm' (minutes).", ephemeral=True
                )
                return
            try:
                time_value = int(duree[:-1])
                if time_value <= 0:
                    raise ValueError
            except ValueError:
                await interaction.response.send_message(
                    "🚫 La durée doit être un nombre positif suivi de 'd', 'h' ou 'm'.", ephemeral=True
                )
                return
            if time_unit == 'd':
                duration = datetime.timedelta(days=time_value)
            elif time_unit == 'h':
                duration = datetime.timedelta(hours=time_value)
            elif time_unit == 'm':
                duration = datetime.timedelta(minutes=time_value)
            ban_until = datetime.datetime.utcnow() + duration
        else:
            ban_until = None
        full_reason = f"Banni par {interaction.user} | Raison: {raison}"
        if duration:
            full_reason += f" | Durée: {duree}"
        try:
            embed_dm = discord.Embed(
                title="🔨 Vous avez été banni",
                description=f"Vous avez été banni du serveur **{guild.name}**.\n\n**Raison :** {raison}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            if duration:
                embed_dm.add_field(name="Durée", value=duree, inline=False)
                embed_dm.add_field(name="Fin du ban", value=ban_until.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
            embed_dm.set_footer(text="Si vous pensez que c'est une erreur, contactez un administrateur.")
            await utilisateur.send(embed=embed_dm)
        except Exception:
            pass
        try:
            await guild.ban(utilisateur, reason=full_reason, delete_message_days=0)
            embed = discord.Embed(
                title="🔨 Utilisateur banni",
                description=f"{utilisateur.mention} a été banni du serveur ✅",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="Raison", value=raison)
            if duration:
                embed.add_field(name="Durée", value=duree)
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)

            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                embed_log = discord.Embed(
                    title="🔨 Nouveau ban",
                    color=discord.Color.red(),
                    timestamp=datetime.datetime.utcnow()
                )
                embed_log.add_field(name="Utilisateur", value=f"{utilisateur} ({utilisateur.id})", inline=False)
                embed_log.add_field(name="Banni par", value=f"{interaction.user} ({interaction.user.id})", inline=False)
                embed_log.add_field(name="Raison", value=raison, inline=False)
                embed_log.set_footer(text=f"ID du ban: {utilisateur.id}-{int(datetime.datetime.utcnow().timestamp())}")

                if duration:
                    embed_log.add_field(name="Durée", value=duree, inline=False)
                    embed_log.add_field(name="Fin du ban", value=ban_until.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
                await log_channel.send(embed=embed_log)

            if duration:
                await asyncio.sleep(duration.total_seconds())
                try:
                    await guild.unban(utilisateur, reason="Durée de ban terminée")
                    if log_channel:
                        embed_unban = discord.Embed(
                            title="✅ Utilisateur débanni",
                            description=f"{utilisateur} a été débanni automatiquement après la fin de sa durée de ban.",
                            color=discord.Color.green(),
                            timestamp=datetime.datetime.utcnow()
                        )
                        await log_channel.send(embed=embed_unban)
                except Exception as e:
                    if log_channel:
                        embed_error = discord.Embed(
                            title="❌ Erreur lors du déban",
                            description=f"Impossible de débannir {utilisateur} automatiquement.\n**Erreur :** {e}",
                            color=discord.Color.red(),
                            timestamp=datetime.datetime.utcnow()
                        )
                        await log_channel.send(embed=embed_error)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur de ban",
                description=f"Impossible de bannir {utilisateur.mention}.\n**Erreur :** {e}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)
            return
async def setup(bot):
    await bot.add_cog(Ban(bot))