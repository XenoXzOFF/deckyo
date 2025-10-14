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
# Utiliser des embeds pour les messages envoyés par le bot

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]
log_channel_id = int(os.getenv('LOG_CHANNEL_ID'))

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ban",
        description="🔨 Bannis un utilisateur du serveur"
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
        """Bannis un utilisateur du serveur avec une raison et une durée optionnelle"""
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(
                "🚫 Tu n’as pas la permission de bannir des membres.", ephemeral=True
            )
            return

        if utilisateur == interaction.user:
            await interaction.response.send_message(
                "🚫 Tu ne peux pas te bannir toi-même.", ephemeral=True
            )
            return

        if utilisateur == self.bot.user:
            await interaction.response.send_message(
                "🚫 Tu ne peux pas bannir le bot.", ephemeral=True
            )
            return

        if not interaction.guild:
            await interaction.response.send_message(
                "🚫 Cette commande doit être utilisée dans un serveur.", ephemeral=True
            )
            return

        try:
            await utilisateur.send(
                f"🚫 Tu as été banni du serveur **{interaction.guild.name}** pour la raison suivante : {raison}"
            )
        except Exception:
            pass  # L'utilisateur n'a peut-être pas pu recevoir le message privé

        try:
            await interaction.guild.ban(utilisateur, reason=raison)
            embed = discord.Embed(
                title="🔨 Utilisateur banni",
                description=f"{utilisateur.mention} a été banni du serveur ✅",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="Raison", value=raison, inline=False)
            if duree:
                embed.add_field(name="Durée", value=duree, inline=False)
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                await log_channel.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur de bannissement",
                description=f"Impossible de bannir {utilisateur.mention}.\n**Erreur :** {e}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await asyncio.sleep(5)
            try:
                await interaction.delete_original_response()
            except Exception: pass
            return
        if duree:
            time_multiplier = {'d': 86400, 'h': 3600, 'm': 60}
            try:
                unit = duree[-1]
                amount = int(duree[:-1])
                if unit in time_multiplier:
                    await asyncio.sleep(amount * time_multiplier[unit])
                    await interaction.guild.unban(utilisateur, reason="Durée de bannissement expirée")
                    embed = discord.Embed(
                        title="🔓 Utilisateur débanni",
                        description=f"{utilisateur.mention} a été débanni du serveur après la durée spécifiée ✅",
                        color=discord.Color.green(),
                        timestamp=datetime.datetime.utcnow()
                    )
                    embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
                    if log_channel:
                        await log_channel.send(embed=embed)
                else:
                    raise ValueError("Unité de temps invalide")
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Erreur de durée",
                    description=f"La durée spécifiée est invalide.\n**Erreur :** {e}",
                    color=discord.Color.red(),
                    timestamp=datetime.datetime.utcnow()
                )
                embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
                await interaction.followup.send(embed=embed, ephemeral=True)
                await asyncio.sleep(5)
                try:
                    await interaction.delete_original_response()
                except Exception: pass
                return
async def setup(bot):
    await bot.add_cog(Ban(bot))