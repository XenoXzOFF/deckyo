import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime
import asyncio

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]
log_channel_id = int(os.getenv('LOG_CHANNEL_ID'))

class Timeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def parse_duration(self, duree_str: str):
        if not duree_str:
            return None, "La durée ne peut pas être vide."
        
        time_unit = duree_str[-1].lower()
        if time_unit not in ['d', 'h', 'm', 's']:
            return None, "La durée doit se terminer par 'd' (jours), 'h' (heures), 'm' (minutes) ou 's' (secondes)."
        
        try:
            time_value = int(duree_str[:-1])
            if time_value <= 0:
                raise ValueError
        except ValueError:
            return None, "La durée doit être un nombre positif suivi de 'd', 'h', 'm' ou 's'."

        if time_unit == 'd':
            return datetime.timedelta(days=time_value), None
        elif time_unit == 'h':
            return datetime.timedelta(hours=time_value), None
        elif time_unit == 'm':
            return datetime.timedelta(minutes=time_value), None
        elif time_unit == 's':
            return datetime.timedelta(seconds=time_value), None
        
        return None, "Unité de temps invalide."

    @app_commands.command(
        name="timeout",
        description="⏳ Exclut temporairement un utilisateur (modérateurs uniquement)"
    )
    @app_commands.describe(
        utilisateur="L'utilisateur à exclure",
        duree="La durée de l'exclusion (ex: 10m, 2h, 7d)",
        raison="La raison de l'exclusion"
    )
    async def timeout(
        self,
        interaction: discord.Interaction,
        utilisateur: discord.Member,
        duree: str,
        raison: str
    ):
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("🚫 Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
            return

        if utilisateur == interaction.user:
            await interaction.response.send_message("🚫 Tu ne peux pas t'exclure toi-même.", ephemeral=True)
            return

        if utilisateur.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("🚫 Tu ne peux pas exclure cet utilisateur car son rôle est supérieur ou égal au tien.", ephemeral=True)
            return

        duration, error_msg = self.parse_duration(duree)
        if error_msg:
            await interaction.response.send_message(f"🚫 {error_msg}", ephemeral=True)
            return

        if duration.total_seconds() > (28 * 24 * 60 * 60):
            await interaction.response.send_message("🚫 La durée du timeout ne peut pas dépasser 28 jours.", ephemeral=True)
            return

        try:
            await utilisateur.timeout(duration, reason=f"Par {interaction.user} | Raison: {raison}")
            
            embed = discord.Embed(
                title="⏳ Utilisateur Exclu Temporairement",
                description=f"{utilisateur.mention} a été exclu pour **{duree}**.",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="Raison", value=raison, inline=False)
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)

            try:
                dm_embed = discord.Embed(
                    title="⏳ Vous avez été exclu temporairement",
                    description=f"Vous avez été exclu du serveur **{interaction.guild.name}** pour **{duree}**.",
                    color=discord.Color.orange(),
                    timestamp=datetime.datetime.utcnow()
                )
                dm_embed.add_field(name="Raison", value=raison, inline=False)
                await utilisateur.send(embed=dm_embed)
            except discord.Forbidden:
                pass

            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title="⏳ Nouveau Timeout",
                    color=discord.Color.orange(),
                    timestamp=datetime.datetime.utcnow()
                )
                log_embed.add_field(name="Utilisateur", value=f"{utilisateur} ({utilisateur.id})", inline=False)
                log_embed.add_field(name="Exclu par", value=f"{interaction.user} ({interaction.user.id})", inline=False)
                log_embed.add_field(name="Durée", value=duree, inline=False)
                log_embed.add_field(name="Raison", value=raison, inline=False)
                await log_channel.send(embed=log_embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Une erreur est survenue : {e}", ephemeral=True)

    @app_commands.command(
        name="untimeout",
        description="✅ Lève l'exclusion temporaire d'un utilisateur (modérateurs uniquement)"
    )
    @app_commands.describe(
        utilisateur="L'utilisateur à réintégrer",
        raison="La raison de la levée de l'exclusion"
    )
    async def untimeout(
        self,
        interaction: discord.Interaction,
        utilisateur: discord.Member,
        raison: str
    ):
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("🚫 Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
            return

        try:
            await utilisateur.timeout(None, reason=f"Par {interaction.user} | Raison: {raison}")
            
            embed = discord.Embed(
                title="✅ Exclusion Levée",
                description=f"L'exclusion de {utilisateur.mention} a été levée.",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="Raison", value=raison, inline=False)
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Une erreur est survenue : {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Timeout(bot))