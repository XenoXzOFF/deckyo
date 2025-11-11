import discord
from discord.ext import commands
from discord import app_commands
import datetime
import os
import asyncio

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]

class GiveRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="giverole",
        description="🎖️ Donne un rôle à un utilisateur (permission Gérer les rôles requise)"
    )
    @app_commands.describe(
        utilisateur="L'utilisateur à qui donner le rôle",
        role="Le rôle à donner",
        envoyer_mp="Envoyer un message privé à l'utilisateur ?",
        duree="Durée pendant laquelle le rôle est attribué (ex: 10m, 2h, 7d). Laisser vide pour permanent."
    )
    async def giverole(
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
                        title="🎖️ Rôle Ajouté",
                        description=f"Le rôle **{role.name}** vous a été ajouté sur le serveur **{interaction.guild.name}**"
                                    + (f" pour une durée de **{duree}**." if duration else "."),
                        color=discord.Color.green(),
                        timestamp=datetime.datetime.utcnow()
                    )
                    embed_dm.set_footer(text=f"Action effectuée par {interaction.user.display_name}")
                    await utilisateur.send(embed=embed_dm)
                    mp_sent_status = "\n✅ MP envoyé à l'utilisateur."
                except discord.Forbidden:
                    mp_sent_status = "\n⚠️ Impossible d'envoyer un MP à l'utilisateur (MPs fermés ou bot bloqué)."
                except Exception as e:
                    mp_sent_status = f"\n❌ Erreur lors de l'envoi du MP : {e}"

            await utilisateur.add_roles(role)

            description_msg = f"Le rôle `{role.name}` a été donné à {utilisateur.mention} ✅"
            if duration:
                description_msg += f" pour une durée de **{duree}**."
            description_msg += mp_sent_status

            embed = discord.Embed(
                title="🎖️ Rôle attribué",
                description=description_msg,
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)

            if duration:
                await asyncio.sleep(duration.total_seconds())
                try:
                    if role in utilisateur.roles:
                        await utilisateur.remove_roles(role, reason="Durée du rôle temporaire expirée.")
                        # Optionnel: notifier l'utilisateur que le rôle a été retiré
                        try:
                            await utilisateur.send(f"Le rôle temporaire **{role.name}** sur le serveur **{interaction.guild.name}** a expiré et vous a été retiré.")
                        except discord.Forbidden:
                            pass
                except discord.HTTPException:
                    # Gérer les erreurs si l'utilisateur a quitté le serveur, etc.
                    pass

        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur d'attribution",
                description=f"Impossible de donner le rôle `{role.name}` à {utilisateur.mention}.\n**Erreur :** {e}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(GiveRole(bot))