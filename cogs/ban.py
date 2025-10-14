import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime

# L'utilisateur doit avoir la permissions de bannir des membres
# L'utilisateur banni doit recevoir un message privé lui indiquant qu'il a été banni et la raison
# Le bot doit logger l'action dans un salon spécifique
# L'utilisateur peut bannir un utilisateur en spécifiant une durée (ex: 7d pour 7 jours, 12h pour 12 heures, 30m pour 30 minutes)

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]
log_channel_id = int(os.getenv('LOG_CHANNEL_ID'))


class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ban",
        description="🔨 Bannir un utilisateur du serveur (développeurs uniquement)"
    )
    @app_commands.describe(
        utilisateur="L'utilisateur à bannir",
        raison="La raison du bannissement",
        duree="La durée du bannissement (ex: 7d pour 7 jours, 12h pour 12 heures, 30m pour 30 minutes) - optionnel"
    )
    async def ban(
        self,
        interaction: discord.Interaction,
        utilisateur: discord.Member,
        raison: str,
        duree: str = None
    ):
        """Bannir un utilisateur du serveur avec une raison et une durée optionnelle"""
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

        # Calcul de la durée en secondes
        ban_duration = None
        if duree:
            try:
                unit = duree[-1]
                amount = int(duree[:-1])
                if unit == 'd':
                    ban_duration = amount * 86400  # jours en secondes
                elif unit == 'h':
                    ban_duration = amount * 3600   # heures en secondes
                elif unit == 'm':
                    ban_duration = amount * 60     # minutes en secondes
                else:
                    raise ValueError("Unité de temps invalide")
            except Exception:
                await interaction.response.send_message(
                    "🚫 Format de durée invalide. Utilise par exemple `7d` pour 7 jours, `12h` pour 12 heures, ou `30m` pour 30 minutes.", ephemeral=True
                )
                return

        try:
            # Envoi du message privé à l'utilisateur banni
            dm_message = f"Tu as été banni du serveur **{guild.name}**."
            if raison:
                dm_message += f"\n**Raison :** {raison}"
            if ban_duration:
                dm_message += f"\n**Durée :** {duree}"
            else:
                dm_message += "\n**Durée :** Permanent"
            try:
                await utilisateur.send(dm_message)
            except Exception:
                pass  # L'utilisateur a peut-être désactivé les messages privés
            # Bannissement de l'utilisateur
            await guild.ban(utilisateur, reason=raison)
            embed = discord.Embed(
                title="🔨 Utilisateur banni",
                description=f"L'utilisateur `{utilisateur}` a été banni du serveur ✅",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="Raison", value=raison, inline=False)
            if ban_duration:
                embed.add_field(name="Durée", value=duree, inline=False)
            else:
                embed.add_field(name="Durée", value="Permanent", inline=False)
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)
            # Log de l'action dans un salon spécifique
            log_channel = guild.get_channel(log_channel_id)
            if log_channel:
                await log_channel.send(embed=embed)
            # Si une durée est spécifiée, lever le bannissement après la durée
            if ban_duration:
                await discord.utils.sleep_until(datetime.datetime.utcnow() + datetime.timedelta(seconds=ban_duration))
                await guild.unban(utilisateur, reason="Durée de bannissement expirée")
                unban_embed = discord.Embed(
                    title="🔓 Utilisateur débanni",
                    description=f"L'utilisateur `{utilisateur}` a été débanni du serveur après la durée spécifiée ✅",
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.utcnow()
                )
                unban_embed.set_footer(text="Système de bannissement", icon_url=self.bot.user.display_avatar)
                if log_channel:
                    await log_channel.send(embed=unban_embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur de bannissement",
                description=f"Impossible de bannir l'utilisateur `{utilisateur}`.\n**Erreur :** {e}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)
            # Log de l'erreur dans un salon spécifique
            log_channel = guild.get_channel(log_channel_id)
            if log_channel:
                await log_channel.send(embed=embed)
async def setup(bot):
    await bot.add_cog(Ban(bot))