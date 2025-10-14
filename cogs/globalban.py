import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]
log_channel_id = int(os.getenv('LOG_CHANNEL_ID'))

class GlobalBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="globalban",
        description="🌍 Bannis un utilisateur de TOUS les serveurs où le bot est présent (owners uniquement)"
    )
    @app_commands.describe(
        utilisateur_id="L'ID de l'utilisateur à bannir globalement",
        raison="La raison du ban global"
    )
    async def globalban(
        self,
        interaction: discord.Interaction,
        utilisateur_id: str,
        raison: str
    ):
        """Bannis un utilisateur de tous les serveurs où le bot est présent"""
        if interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message(
                "🚫 Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            user_id = int(utilisateur_id)
            user = await self.bot.fetch_user(user_id)
        except ValueError:
            await interaction.followup.send(
                "🚫 L'ID utilisateur doit être un nombre entier.", ephemeral=True
            )
            return
        except discord.NotFound:
            await interaction.followup.send(
                f"🚫 Aucun utilisateur trouvé avec l'ID `{utilisateur_id}`.", ephemeral=True
            )
            return
        except Exception as e:
            await interaction.followup.send(
                f"🚫 Erreur lors de la récupération de l'utilisateur: {e}", ephemeral=True
            )
            return

        banned_guilds = []
        failed_guilds = []
        already_banned = []

        for guild in self.bot.guilds:
            try:
                try:
                    ban_entry = await guild.fetch_ban(user)
                    already_banned.append(guild.name)
                    continue
                except discord.NotFound:
                    pass

                if not guild.me.guild_permissions.ban_members:
                    failed_guilds.append(f"{guild.name} (pas de permission)")
                    continue

                full_reason = f"[GLOBAL BAN] Par {interaction.user} | Raison: {raison}"
                await guild.ban(discord.Object(id=user_id), reason=full_reason, delete_message_days=0)
                banned_guilds.append(guild.name)

            except Exception as e:
                failed_guilds.append(f"{guild.name} ({str(e)[:50]})")

        try:
            embed_dm = discord.Embed(
                title="🌍 Ban Global",
                description=f"Tu as été banni de **{len(banned_guilds)}** serveur(s) par les propriétaires du bot.",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed_dm.add_field(name="Raison", value=raison, inline=False)
            embed_dm.add_field(name="Type", value="Ban Global", inline=False)
            embed_dm.set_footer(text="Si tu penses que c'est une erreur, contacte les propriétaires du bot.")
            await user.send(embed=embed_dm)
        except Exception:
            pass

        embed = discord.Embed(
            title="🌍 Ban Global Exécuté",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Utilisateur", value=f"{user} ({user.id})", inline=False)
        embed.add_field(name="Raison", value=raison, inline=False)
        embed.add_field(name="✅ Serveurs bannis", value=f"{len(banned_guilds)} serveur(s)", inline=True)
        
        if already_banned:
            embed.add_field(name="⚠️ Déjà banni", value=f"{len(already_banned)} serveur(s)", inline=True)
        
        if failed_guilds:
            embed.add_field(name="❌ Échecs", value=f"{len(failed_guilds)} serveur(s)", inline=True)

        if banned_guilds:
            servers_list = "\n".join(banned_guilds[:10])
            if len(banned_guilds) > 10:
                servers_list += f"\n... et {len(banned_guilds) - 10} autres"
            embed.add_field(name="Serveurs concernés", value=servers_list, inline=False)

        embed.set_footer(text=f"Exécuté par {interaction.user}", icon_url=interaction.user.display_avatar)
        await interaction.followup.send(embed=embed)

        log_channel = self.bot.get_channel(log_channel_id)
        if log_channel:
            embed_log = discord.Embed(
                title="🌍 Ban Global",
                color=discord.Color.dark_red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed_log.add_field(name="Utilisateur", value=f"{user} ({user.id})", inline=False)
            embed_log.add_field(name="Exécuté par", value=f"{interaction.user} ({interaction.user.id})", inline=False)
            embed_log.add_field(name="Raison", value=raison, inline=False)
            embed_log.add_field(name="Serveurs bannis", value=str(len(banned_guilds)), inline=True)
            embed_log.add_field(name="Déjà banni", value=str(len(already_banned)), inline=True)
            embed_log.add_field(name="Échecs", value=str(len(failed_guilds)), inline=True)
            await log_channel.send(embed=embed_log)

    @app_commands.command(
        name="globalunban",
        description="🌍 Débannis un utilisateur de TOUS les serveurs où le bot est présent (owners uniquement)"
    )
    @app_commands.describe(
        utilisateur_id="L'ID de l'utilisateur à débannir globalement",
        raison="La raison du déban global"
    )
    async def globalunban(
        self,
        interaction: discord.Interaction,
        utilisateur_id: str,
        raison: str
    ):
        """Débannis un utilisateur de tous les serveurs où le bot est présent"""
        if interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message(
                "🚫 Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            user_id = int(utilisateur_id)
            user = await self.bot.fetch_user(user_id)
        except ValueError:
            await interaction.followup.send(
                "🚫 L'ID utilisateur doit être un nombre entier.", ephemeral=True
            )
            return
        except discord.NotFound:
            await interaction.followup.send(
                f"🚫 Aucun utilisateur trouvé avec l'ID `{utilisateur_id}`.", ephemeral=True
            )
            return
        except Exception as e:
            await interaction.followup.send(
                f"🚫 Erreur lors de la récupération de l'utilisateur: {e}", ephemeral=True
            )
            return

        unbanned_guilds = []
        failed_guilds = []
        not_banned = []
        invites = {}

        for guild in self.bot.guilds:
            try:
                try:
                    await guild.fetch_ban(discord.Object(id=user_id))
                except discord.NotFound:
                    not_banned.append(guild.name)
                    continue

                if not guild.me.guild_permissions.ban_members:
                    failed_guilds.append(f"{guild.name} (pas de permission)")
                    continue

                full_reason = f"[GLOBAL UNBAN] Par {interaction.user} | Raison: {raison}"
                await guild.unban(discord.Object(id=user_id), reason=full_reason)
                unbanned_guilds.append(guild.name)

                try:
                    invite_channel = None
                    for channel in guild.text_channels:
                        if channel.permissions_for(guild.me).create_instant_invite:
                            invite_channel = channel
                            break
                    
                    if invite_channel:
                        invite = await invite_channel.create_invite(
                            max_age=0,  
                            max_uses=1,  
                            unique=True,
                            reason=f"Invitation pour {user} après déban global"
                        )
                        invites[guild.name] = invite.url
                except Exception:
                    pass

            except Exception as e:
                failed_guilds.append(f"{guild.name} ({str(e)[:50]})")

        try:
            embed_dm = discord.Embed(
                title="🎉 Déban Global",
                description=f"Tu as été débanni de **{len(unbanned_guilds)}** serveur(s) !",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed_dm.add_field(name="Raison", value=raison, inline=False)
            
            if invites:
                invite_text = ""
                for guild_name, invite_url in invites.items():
                    invite_text += f"**{guild_name}**: [Rejoindre]({invite_url})\n"
                
                if len(invite_text) > 1024:
                    chunks = [invite_text[i:i+1024] for i in range(0, len(invite_text), 1024)]
                    for i, chunk in enumerate(chunks):
                        embed_dm.add_field(
                            name=f"Liens d'invitation {f'({i+1})' if len(chunks) > 1 else ''}", 
                            value=chunk, 
                            inline=False
                        )
                else:
                    embed_dm.add_field(name="Liens d'invitation", value=invite_text, inline=False)
            
            embed_dm.set_footer(text="Les invitations sont à usage unique et n'expirent jamais.")
            await user.send(embed=embed_dm)
        except Exception:
            pass

        embed = discord.Embed(
            title="🌍 Déban Global Exécuté",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Utilisateur", value=f"{user} ({user.id})", inline=False)
        embed.add_field(name="Raison", value=raison, inline=False)
        embed.add_field(name="✅ Serveurs débannis", value=f"{len(unbanned_guilds)} serveur(s)", inline=True)
        
        if not_banned:
            embed.add_field(name="⚠️ Pas banni", value=f"{len(not_banned)} serveur(s)", inline=True)
        
        if failed_guilds:
            embed.add_field(name="❌ Échecs", value=f"{len(failed_guilds)} serveur(s)", inline=True)

        embed.add_field(name="🔗 Invitations créées", value=f"{len(invites)} invitation(s)", inline=True)

        if unbanned_guilds:
            servers_list = "\n".join(unbanned_guilds[:10])
            if len(unbanned_guilds) > 10:
                servers_list += f"\n... et {len(unbanned_guilds) - 10} autres"
            embed.add_field(name="Serveurs concernés", value=servers_list, inline=False)

        embed.set_footer(text=f"Exécuté par {interaction.user}", icon_url=interaction.user.display_avatar)
        await interaction.followup.send(embed=embed)

        log_channel = self.bot.get_channel(log_channel_id)
        if log_channel:
            embed_log = discord.Embed(
                title="🌍 Déban Global",
                color=discord.Color.dark_green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed_log.add_field(name="Utilisateur", value=f"{user} ({user.id})", inline=False)
            embed_log.add_field(name="Exécuté par", value=f"{interaction.user} ({interaction.user.id})", inline=False)
            embed_log.add_field(name="Raison", value=raison, inline=False)
            embed_log.add_field(name="Serveurs débannis", value=str(len(unbanned_guilds)), inline=True)
            embed_log.add_field(name="Pas banni", value=str(len(not_banned)), inline=True)
            embed_log.add_field(name="Échecs", value=str(len(failed_guilds)), inline=True)
            embed_log.add_field(name="Invitations créées", value=str(len(invites)), inline=True)
            await log_channel.send(embed=embed_log)

async def setup(bot):
    await bot.add_cog(GlobalBan(bot))