import discord
from discord.ext import commands
from discord import app_commands
import datetime
import os
import asyncio

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]

class RemoveRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="removerole",
        description="❌ Retire un rôle à un utilisateur (permission Gérer les rôles requise)"
    )
    @app_commands.describe(
        utilisateur="L'utilisateur à qui retirer le rôle",
        role="Le rôle à retirer",
        envoyer_mp="Envoyer un message privé à l'utilisateur ?",
        duree="Durée pendant laquelle le rôle est retiré (ex: 10m, 2h, 7d). Laisser vide pour permanent."
    )
    async def removerole(
        self,
        interaction: discord.Interaction,
        utilisateur: discord.Member,
        role: discord.Role,
        envoyer_mp: bool,
        duree: str = None
    ):
        if interaction.user.id not in OWNER_IDS and not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "🚫 Tu n’as pas la permission d’utiliser cette commande.", ephemeral=True
            )
            return

        duration = None
        if duree:
            time_unit = duree[-1].lower()
            if time_unit not in ['d', 'h', 'm', 's']:
                await interaction.response.send_message(
                    "🚫 La durée doit se terminer par 'd' (jours), 'h' (heures), 'm' (minutes) ou 's' (secondes).", ephemeral=True
                )
                return
            try:
                time_value = int(duree[:-1])
                if time_value <= 0:
                    raise ValueError
            except ValueError:
                await interaction.response.send_message(
                    "🚫 La durée doit être un nombre positif suivi de 'd', 'h', 'm' ou 's'.", ephemeral=True
                )
                return

            if time_unit == 'd':
                duration = datetime.timedelta(days=time_value)
            elif time_unit == 'h':
                duration = datetime.timedelta(hours=time_value)
            elif time_unit == 'm':
                duration = datetime.timedelta(minutes=time_value)
            elif time_unit == 's':
                duration = datetime.timedelta(seconds=time_value)

        try:
            mp_sent_status = ""
            if envoyer_mp:
                try:
                    embed_dm = discord.Embed(
                        title="❌ Rôle Retiré",
                        description=f"Le rôle **{role.name}** vous a été retiré sur le serveur **{interaction.guild.name}**"
                                    + (f" pour une durée de **{duree}**." if duration else "."),
                        color=discord.Color.red(),
                        timestamp=datetime.datetime.utcnow()
                    )
                    embed_dm.set_footer(text=f"Action effectuée par {interaction.user.display_name}")
                    await utilisateur.send(embed=embed_dm)
                    mp_sent_status = "\n✅ MP envoyé à l'utilisateur."
                except discord.Forbidden:
                    mp_sent_status = "\n⚠️ Impossible d'envoyer un MP à l'utilisateur (MPs fermés ou bot bloqué)."
                except Exception as e:
                    mp_sent_status = f"\n❌ Erreur lors de l'envoi du MP : {e}"

            await utilisateur.remove_roles(role)

            description_msg = f"Le rôle `{role.name}` a été retiré à {utilisateur.mention} ✅"
            if duration:
                description_msg += f" pour une durée de **{duree}**."
            description_msg += mp_sent_status

            embed = discord.Embed(
                title="❌ Rôle retiré",
                description=description_msg,
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)

            if duration:
                await asyncio.sleep(duration.total_seconds())
                try:
                    # Vérifier si l'utilisateur est toujours sur le serveur
                    if interaction.guild.get_member(utilisateur.id):
                        await utilisateur.add_roles(role, reason="Fin de la suppression temporaire du rôle.")
                        try:
                            await utilisateur.send(f"Le rôle **{role.name}** vous a été rendu sur le serveur **{interaction.guild.name}** après la période de suppression temporaire.")
                        except discord.Forbidden:
                            pass
                except discord.HTTPException:
                    pass

        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur de retrait",
                description=f"Impossible de retirer le rôle `{role.name}` à {utilisateur.mention}.\n**Erreur :** {e}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(RemoveRole(bot))