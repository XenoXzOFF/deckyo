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
        description="🎖️ Donne un rôle à un utilisateur (développeurs uniquement)"
    )
    @app_commands.describe(
        utilisateur="L'utilisateur à qui donner le rôle",
        role="Le rôle à donner"
        envoyer_mp="Envoyer un message privé à l'utilisateur ?"
    )
    async def giverole(
        self,
        interaction: discord.Interaction,
        utilisateur: discord.Member,
        role: discord.Role,
        envoyer_mp: bool
    ):
        if interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message(
                "🚫 Tu n’as pas la permission d’utiliser cette commande.", ephemeral=True
            )
            return

        try:
            mp_sent_status = ""
            if envoyer_mp:
                try:
                    embed_dm = discord.Embed(
                        title="🎖️ Rôle Ajouté",
                        description=f"Le rôle **{role.name}** vous a été ajouté sur le serveur **{interaction.guild.name}**.",
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

            embed = discord.Embed(
                title="🎖️ Rôle attribué",
                description=f"Le rôle `{role.name}` a été donné à {utilisateur.mention} ✅{mp_sent_status}",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)
            await asyncio.sleep(5)
            try:
                await interaction.delete_original_response()
            except Exception: pass
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur d'attribution",
                description=f"Impossible de donner le rôle `{role.name}` à {utilisateur.mention}.\n**Erreur :** {e}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)
            await asyncio.sleep(5)
            try:
                await interaction.delete_original_response()
            except Exception: pass

async def setup(bot):
    await bot.add_cog(GiveRole(bot))