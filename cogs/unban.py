import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime
import asyncio

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]
log_channel_id = int(os.getenv('LOG_CHANNEL_ID'))

class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="unban",
        description="🔨 Débannis un utilisateur du serveur (admins uniquement)"
    )
    @app_commands.describe(
        utilisateur="L'utilisateur à débannir (ID)",
        raison="La raison du débannissement"
    )
    async def unban(
        self,
        interaction: discord.Interaction,
        utilisateur: str,
        raison: str
    ):
        """Débannis un utilisateur du serveur avec une raison"""

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

        try:
            user_id = int(utilisateur)
            user_to_unban = None
            async for ban_entry in guild.bans():
                if ban_entry.user.id == user_id:
                    user_to_unban = ban_entry.user
                    break

            if not user_to_unban:
                await interaction.response.send_message(
                    f"🚫 L'utilisateur avec l'ID `{utilisateur}` n'est pas banni.", ephemeral=True
                )
                return

            await guild.unban(user_to_unban, reason=f"Débanni par {interaction.user} | Raison: {raison}")


            try:
                invite = await interaction.channel.create_invite(
                    max_age=0,  
                    max_uses=1,  
                    unique=True,
                    reason=f"Invitation pour {user_to_unban} après débannissement"
                )
                
                dm_embed = discord.Embed(
                    title="🎉 Tu as été débanni !",
                    description=f"Tu as été débanni du serveur **{guild.name}**.",
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.utcnow()
                )
                dm_embed.add_field(name="Raison", value=raison, inline=False)
                dm_embed.add_field(name="Lien d'invitation", value=f"[Clique ici pour rejoindre]({invite.url})", inline=False)
                dm_embed.set_footer(text=f"Serveur: {guild.name}")
                
                await user_to_unban.send(embed=dm_embed)
            except discord.Forbidden:
                pass
            except Exception:
                pass

            embed = discord.Embed(
                title="🔨 Utilisateur débanni",
                description=f"L'utilisateur `{user_to_unban}` a été débanni ✅",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="Raison", value=raison, inline=False)
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)

            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                embed_log = discord.Embed(
                    title="🔨 Utilisateur débanni",
                    color=discord.Color.orange(),
                    timestamp=datetime.datetime.utcnow()
                )
                embed_log.add_field(name="Utilisateur", value=f"{user_to_unban} ({user_to_unban.id})", inline=False)
                embed_log.add_field(name="Débanni par", value=f"{interaction.user} ({interaction.user.id})", inline=False)
                embed_log.add_field(name="Raison", value=raison, inline=False)
                embed_log.set_footer(text=f"ID du débannissement: {user_to_unban.id}-{int(datetime.datetime.utcnow().timestamp())}")
                await log_channel.send(embed=embed_log)
        except ValueError:
            await interaction.response.send_message(
                "🚫 L'ID utilisateur doit être un nombre entier.", ephemeral=True
            )
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur de débannissement",
                description=f"Impossible de débannir l'utilisateur avec l'ID `{utilisateur}`.\n**Erreur :** {e}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Unban(bot))