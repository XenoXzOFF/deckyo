import discord
from discord import app_commands
from discord.ext import commands
import os
import datetime
import asyncio

try:
    USER_REPORTS_CHANNEL_ID = int(os.getenv('USER_REPORTS_CHANNEL_ID'))
except (TypeError, ValueError):
    print("⚠️ ATTENTION: USER_REPORTS_CHANNEL_ID n'est pas défini dans le .env")
    USER_REPORTS_CHANNEL_ID = None

try:
    OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]
except (TypeError, ValueError, AttributeError):
    print("⚠️ ATTENTION: OWNER_IDS n'est pas défini dans le .env")
    OWNER_IDS = []
STATUS_OPTIONS = {
    "waiting": ("⏳ En attente", discord.Color.greyple()),
    "pending": ("🔄 En cours de traitement", discord.Color.orange()),
    "resolved": ("✅ Traité", discord.Color.green()),
    "dismissed": ("❌ Non pris en compte", discord.Color.red())
}

REPORT_REASONS = [
    app_commands.Choice(name="Spam / Flood", value="spam"),
    app_commands.Choice(name="Harcèlement", value="harassment"),
    app_commands.Choice(name="Propos inappropriés", value="inappropriate"),
    app_commands.Choice(name="Comportement toxique", value="toxic"),
    app_commands.Choice(name="Contenu NSFW non autorisé", value="nsfw"),
    app_commands.Choice(name="Usurpation d'identité", value="impersonation"),
    app_commands.Choice(name="Publicité non sollicitée", value="advertising"),
    app_commands.Choice(name="Autre", value="other")
]

class ReportUser(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reportuser", description="Signale un utilisateur problématique")
    @app_commands.describe(
        user="L'utilisateur à signaler",
        reason="Raison du signalement",
        details="Détails supplémentaires sur le signalement (obligatoire)",
        proof="Capture d'écran ou preuve (optionnel)"
    )
    @app_commands.choices(reason=REPORT_REASONS)
    async def reportuser(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member,
        reason: app_commands.Choice[str],
        details: str,
        proof: discord.Attachment = None
    ):
        if user.id == interaction.user.id:
            error_embed = discord.Embed(
                title="🚫 Erreur",
                description="Vous ne pouvez pas vous signaler vous-même.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        if user.bot:
            error_embed = discord.Embed(
                title="🚫 Erreur",
                description="Vous ne pouvez pas signaler un bot.\nContactez directement un administrateur.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        if not details or len(details.strip()) == 0:
            error_embed = discord.Embed(
                title="🚫 Erreur",
                description="Les détails du signalement ne peuvent pas être vides.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        reports_channel = self.bot.get_channel(USER_REPORTS_CHANNEL_ID)
        if not reports_channel:
            error_embed = discord.Embed(
                title="⚠️ Erreur de configuration",
                description="Le salon de signalement est introuvable.\nVeuillez contacter un administrateur.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        if proof and not proof.content_type.startswith('image/'):
            error_embed = discord.Embed(
                title="🚫 Erreur",
                description="Le fichier fourni n'est pas une image valide.\nFormats acceptés: PNG, JPG, JPEG, GIF, WEBP",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        reason_emoji = {
            "spam": "📨",
            "harassment": "😡",
            "inappropriate": "⚠️",
            "toxic": "☠️",
            "nsfw": "🔞",
            "impersonation": "🎭",
            "advertising": "📢",
            "other": "❓"
        }

        embed = discord.Embed(
            title="🚨 Nouveau signalement d'utilisateur",
            description=f"**Motif:** {reason_emoji.get(reason.value, '❓')} {reason.name}\n\n**Détails:**\n{details}",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(
            name="👤 Utilisateur signalé", 
            value=f"{user.mention}\n`{user}` (ID: `{user.id}`)\nCompte créé: <t:{int(user.created_at.timestamp())}:R>", 
            inline=False
        )
        
        embed.add_field(
            name="📝 Signalé par", 
            value=f"{interaction.user.mention}\n`{interaction.user}` (ID: `{interaction.user.id}`)", 
            inline=False
        )
        
        embed.add_field(
            name="🏠 Serveur", 
            value=f"**{interaction.guild.name}**\n(ID: `{interaction.guild.id}`)", 
            inline=True
        )
        embed.add_field(
            name="💬 Salon", 
            value=f"{interaction.channel.mention}\n(ID: `{interaction.channel.id}`)", 
            inline=True
        )
        embed.add_field(
            name="📊 État", 
            value=STATUS_OPTIONS["waiting"][0], 
            inline=False
        )
        
        embed.set_footer(
            text=f"Signalement par {interaction.user}",
            icon_url=interaction.user.display_avatar.url
        )
        
        if proof:
            embed.set_image(url=proof.url)
            embed.add_field(
                name="📎 Preuve jointe",
                value=f"[Voir l'image]({proof.url})",
                inline=False
            )

        class UnbanModal(discord.ui.Modal, title="Raison du débannissement"):
            def __init__(self, unban_type: str):
                super().__init__()
                self.unban_type = unban_type
                
            raison = discord.ui.TextInput(
                label="Raison du déban",
                placeholder="Entrez la raison du débannissement...",
                required=True,
                style=discord.TextStyle.paragraph,
                max_length=500
            )
            
            async def on_submit(self, modal_interaction: discord.Interaction):
                await modal_interaction.response.defer(ephemeral=True)
                
                raison_text = self.raison.value
                
                if self.unban_type == "global":
                    await self.execute_global_unban(modal_interaction, raison_text)
                else:
                    await self.execute_local_unban(modal_interaction, raison_text)
            
            async def execute_global_unban(self, modal_interaction: discord.Interaction, raison_text: str):
                """Exécute un déban global"""
                unbanned_guilds = []
                failed_guilds = []
                not_banned = []
                invites = {}
                
                for guild in modal_interaction.client.guilds:
                    try:
                        try:
                            await guild.fetch_ban(discord.Object(id=user.id))
                        except discord.NotFound:
                            not_banned.append(guild.name)
                            continue
                        
                        if not guild.me.guild_permissions.ban_members:
                            failed_guilds.append(f"{guild.name} (pas de permission)")
                            continue
                        
                        full_reason = f"[GLOBAL UNBAN depuis rapport] Par {modal_interaction.user} | Raison: {raison_text}"
                        await guild.unban(discord.Object(id=user.id), reason=full_reason)
                        unbanned_guilds.append(guild.name)
                        
                        # Création d'invitation
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
                                    reason=f"Invitation pour {user} après déban global depuis rapport"
                                )
                                invites[guild.name] = invite.url
                        except Exception:
                            pass
                    except Exception as e:
                        failed_guilds.append(f"{guild.name} ({str(e)[:50]})")
                
                # Notification à l'utilisateur débanni
                try:
                    embed_dm = discord.Embed(
                        title="🎉 Déban Global",
                        description=f"Tu as été débanni de **{len(unbanned_guilds)}** serveur(s) !",
                        color=discord.Color.green(),
                        timestamp=datetime.datetime.utcnow()
                    )
                    embed_dm.add_field(name="Raison", value=raison_text, inline=False)
                    
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
                
                # Mise à jour du rapport
                embed.color = discord.Color.green()
                embed.add_field(
                    name="✅ Action prise",
                    value=f"🌍 **Déban Global** par {modal_interaction.user.mention}\n**Raison:** {raison_text}\n✅ Débanni de {len(unbanned_guilds)} serveur(s)\n🔗 {len(invites)} invitation(s) créée(s)",
                    inline=False
                )
                await message_report.edit(embed=embed)
                
                # Réponse à l'admin
                response_embed = discord.Embed(
                    title="🌍 Déban Global Exécuté",
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.utcnow()
                )
                response_embed.add_field(name="Utilisateur", value=f"{user} ({user.id})", inline=False)
                response_embed.add_field(name="Raison", value=raison_text, inline=False)
                response_embed.add_field(name="✅ Serveurs débannis", value=f"{len(unbanned_guilds)}", inline=True)
                if not_banned:
                    response_embed.add_field(name="⚠️ Pas banni", value=f"{len(not_banned)}", inline=True)
                if failed_guilds:
                    response_embed.add_field(name="❌ Échecs", value=f"{len(failed_guilds)}", inline=True)
                response_embed.add_field(name="🔗 Invitations", value=f"{len(invites)}", inline=True)
                
                await modal_interaction.followup.send(embed=response_embed, ephemeral=True)
            
            async def execute_local_unban(self, modal_interaction: discord.Interaction, raison_text: str):
                guild = interaction.guild
                
                # Vérifications
                if not guild.me.guild_permissions.ban_members:
                    await modal_interaction.followup.send(
                        "🚫 Je n'ai pas la permission de débannir des membres sur ce serveur.",
                        ephemeral=True
                    )
                    return
                
                try:
                    try:
                        await guild.fetch_ban(discord.Object(id=user.id))
                    except discord.NotFound:
                        await modal_interaction.followup.send(
                            f"🚫 L'utilisateur `{user}` n'est pas banni sur ce serveur.",
                            ephemeral=True
                        )
                        return
                    
                    full_reason = f"[Déban depuis rapport] Par {modal_interaction.user} | Raison: {raison_text}"
                    await guild.unban(discord.Object(id=user.id), reason=full_reason)
                    
                    invite_url = None
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
                                reason=f"Invitation pour {user} après débannissement"
                            )
                            invite_url = invite.url
                    except Exception:
                        pass
                    
                    try:
                        embed_dm = discord.Embed(
                            title="🎉 Tu as été débanni !",
                            description=f"Tu as été débanni du serveur **{guild.name}**.",
                            color=discord.Color.green(),
                            timestamp=datetime.datetime.utcnow()
                        )
                        embed_dm.add_field(name="Raison", value=raison_text, inline=False)
                        if invite_url:
                            embed_dm.add_field(name="Lien d'invitation", value=f"[Clique ici pour rejoindre]({invite_url})", inline=False)
                        embed_dm.set_footer(text=f"Serveur: {guild.name}")
                        await user.send(embed=embed_dm)
                    except Exception:
                        pass
                    
                    embed.color = discord.Color.green()
                    action_text = f"🔨 **Déban Local** par {modal_interaction.user.mention}\n**Raison:** {raison_text}\n**Serveur:** {guild.name}"
                    if invite_url:
                        action_text += "\n🔗 Invitation envoyée"
                    embed.add_field(
                        name="✅ Action prise",
                        value=action_text,
                        inline=False
                    )
                    await message_report.edit(embed=embed)
                    
                    response_embed = discord.Embed(
                        title="🔨 Déban Local Exécuté",
                        description=f"L'utilisateur `{user}` a été débanni de **{guild.name}** ✅",
                        color=discord.Color.green(),
                        timestamp=datetime.datetime.utcnow()
                    )
                    response_embed.add_field(name="Raison", value=raison_text, inline=False)
                    if invite_url:
                        response_embed.add_field(name="Invitation", value="✅ Créée et envoyée", inline=False)
                    await modal_interaction.followup.send(embed=response_embed, ephemeral=True)
                    
                except Exception as e:
                    await modal_interaction.followup.send(
                        f"❌ Erreur lors du déban: {str(e)}",
                        ephemeral=True
                    )

        class BanModal(discord.ui.Modal, title="Raison du bannissement"):
            def __init__(self, ban_type: str):
                super().__init__()
                self.ban_type = ban_type
                
            raison = discord.ui.TextInput(
                label="Raison du ban",
                placeholder="Entrez la raison du bannissement...",
                required=True,
                style=discord.TextStyle.paragraph,
                max_length=500
            )
            
            duree = discord.ui.TextInput(
                label="Durée (optionnel, seulement pour ban local)",
                placeholder="Ex: 7d, 12h, 30m (vide = permanent)",
                required=False,
                style=discord.TextStyle.short,
                max_length=10
            )
            
            async def on_submit(self, modal_interaction: discord.Interaction):
                await modal_interaction.response.defer(ephemeral=True)
                
                raison_text = self.raison.value
                duree_text = self.duree.value.strip() if self.duree.value else None
                
                duration = None
                ban_until = None
                if duree_text and self.ban_type == "local":
                    time_unit = duree_text[-1]
                    if time_unit not in ['d', 'h', 'm']:
                        await modal_interaction.followup.send(
                            "🚫 La durée doit se terminer par 'd' (jours), 'h' (heures) ou 'm' (minutes).",
                            ephemeral=True
                        )
                        return
                    try:
                        time_value = int(duree_text[:-1])
                        if time_value <= 0:
                            raise ValueError
                    except ValueError:
                        await modal_interaction.followup.send(
                            "🚫 La durée doit être un nombre positif suivi de 'd', 'h' ou 'm'.",
                            ephemeral=True
                        )
                        return
                    
                    if time_unit == 'd':
                        duration = datetime.timedelta(days=time_value)
                    elif time_unit == 'h':
                        duration = datetime.timedelta(hours=time_value)
                    elif time_unit == 'm':
                        duration = datetime.timedelta(minutes=time_value)
                    ban_until = datetime.datetime.utcnow() + duration
                
                if self.ban_type == "global":
                    await self.execute_global_ban(modal_interaction, raison_text)
                else:
                    await self.execute_local_ban(modal_interaction, raison_text, duree_text, duration, ban_until)
            
            async def execute_global_ban(self, modal_interaction: discord.Interaction, raison_text: str):
                banned_guilds = []
                failed_guilds = []
                already_banned = []
                
                for guild in modal_interaction.client.guilds:
                    try:
                        try:
                            await guild.fetch_ban(user)
                            already_banned.append(guild.name)
                            continue
                        except discord.NotFound:
                            pass
                        
                        if not guild.me.guild_permissions.ban_members:
                            failed_guilds.append(f"{guild.name} (pas de permission)")
                            continue
                        
                        full_reason = f"[GLOBAL BAN depuis rapport] Par {modal_interaction.user} | Raison: {raison_text}"
                        await guild.ban(discord.Object(id=user.id), reason=full_reason, delete_message_days=0)
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
                    embed_dm.add_field(name="Raison", value=raison_text, inline=False)
                    embed_dm.add_field(name="Type", value="Ban Global", inline=False)
                    embed_dm.set_footer(text="Si tu penses que c'est une erreur, contacte les propriétaires du bot.")
                    await user.send(embed=embed_dm)
                except Exception:
                    pass
                
                embed.color = discord.Color.dark_red()
                embed.add_field(
                    name="⚠️ Action prise",
                    value=f"🌍 **Ban Global** par {modal_interaction.user.mention}\n**Raison:** {raison_text}\n✅ Banni de {len(banned_guilds)} serveur(s)",
                    inline=False
                )
                await message_report.edit(embed=embed)
                
                response_embed = discord.Embed(
                    title="🌍 Ban Global Exécuté",
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.utcnow()
                )
                response_embed.add_field(name="Utilisateur", value=f"{user} ({user.id})", inline=False)
                response_embed.add_field(name="Raison", value=raison_text, inline=False)
                response_embed.add_field(name="✅ Serveurs bannis", value=f"{len(banned_guilds)}", inline=True)
                if already_banned:
                    response_embed.add_field(name="⚠️ Déjà banni", value=f"{len(already_banned)}", inline=True)
                if failed_guilds:
                    response_embed.add_field(name="❌ Échecs", value=f"{len(failed_guilds)}", inline=True)
                
                await modal_interaction.followup.send(embed=response_embed, ephemeral=True)
            
            async def execute_local_ban(self, modal_interaction: discord.Interaction, raison_text: str, duree_text: str, duration, ban_until):
                guild = interaction.guild
                
                if not guild.me.guild_permissions.ban_members:
                    await modal_interaction.followup.send(
                        "🚫 Je n'ai pas la permission de bannir des membres sur ce serveur.",
                        ephemeral=True
                    )
                    return
                
                try:
                    member = await guild.fetch_member(user.id)
                except:
                    member = None
                
                if member and member.top_role >= guild.me.top_role:
                    await modal_interaction.followup.send(
                        "🚫 Je ne peux pas bannir cet utilisateur car son rôle est supérieur ou égal au mien.",
                        ephemeral=True
                    )
                    return
                
                full_reason = f"[Ban depuis rapport] Par {modal_interaction.user} | Raison: {raison_text}"
                if duration:
                    full_reason += f" | Durée: {duree_text}"
                
                try:
                    try:
                        embed_dm = discord.Embed(
                            title="🔨 Vous avez été banni",
                            description=f"Vous avez été banni du serveur **{guild.name}**.\n\n**Raison :** {raison_text}",
                            color=discord.Color.red(),
                            timestamp=datetime.datetime.utcnow()
                        )
                        if duration:
                            embed_dm.add_field(name="Durée", value=duree_text, inline=False)
                            embed_dm.add_field(name="Fin du ban", value=ban_until.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
                        embed_dm.set_footer(text="Si vous pensez que c'est une erreur, contactez un administrateur.")
                        await user.send(embed=embed_dm)
                    except Exception:
                        pass
                    
                    await guild.ban(discord.Object(id=user.id), reason=full_reason, delete_message_days=0)
                    
                    embed.color = discord.Color.dark_red()
                    action_text = f"🔨 **Ban Local** par {modal_interaction.user.mention}\n**Raison:** {raison_text}\n**Serveur:** {guild.name}"
                    if duration:
                        action_text += f"\n**Durée:** {duree_text}"
                    embed.add_field(
                        name="⚠️ Action prise",
                        value=action_text,
                        inline=False
                    )
                    await message_report.edit(embed=embed)
                    
                    response_embed = discord.Embed(
                        title="🔨 Ban Local Exécuté",
                        description=f"{user.mention} a été banni de **{guild.name}** ✅",
                        color=discord.Color.green(),
                        timestamp=datetime.datetime.utcnow()
                    )
                    response_embed.add_field(name="Raison", value=raison_text, inline=False)
                    if duration:
                        response_embed.add_field(name="Durée", value=duree_text, inline=False)
                    await modal_interaction.followup.send(embed=response_embed, ephemeral=True)
                    
                    if duration:
                        await asyncio.sleep(duration.total_seconds())
                        try:
                            await guild.unban(discord.Object(id=user.id), reason="Durée de ban terminée")
                        except Exception:
                            pass
                            
                except Exception as e:
                    await modal_interaction.followup.send(
                        f"❌ Erreur lors du ban: {str(e)}",
                        ephemeral=True
                    )

        class StatusView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)  
                
            @discord.ui.button(
                label="Ban Global",
                style=discord.ButtonStyle.danger,
                custom_id="ban_global_user",
                emoji="🌍",
                row=0
            )
            async def ban_global(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                if interaction_btn.user.id not in OWNER_IDS:
                    error_embed = discord.Embed(
                        title="🚫 Permission refusée",
                        description="Seuls les propriétaires du bot peuvent utiliser cette action.",
                        color=discord.Color.red()
                    )
                    await interaction_btn.response.send_message(embed=error_embed, ephemeral=True)
                    return
                
                modal = BanModal("global")
                await interaction_btn.response.send_modal(modal)
            
            @discord.ui.button(
                label="Ban Local",
                style=discord.ButtonStyle.danger,
                custom_id="ban_local_user",
                emoji="🔨",
                row=0
            )
            async def ban_local(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                if interaction_btn.user.id not in OWNER_IDS:
                    error_embed = discord.Embed(
                        title="🚫 Permission refusée",
                        description="Seuls les propriétaires du bot peuvent utiliser cette action.",
                        color=discord.Color.red()
                    )
                    await interaction_btn.response.send_message(embed=error_embed, ephemeral=True)
                    return
                
                modal = BanModal("local")
                await interaction_btn.response.send_modal(modal)
            
            @discord.ui.button(
                label="Unban Global",
                style=discord.ButtonStyle.success,
                custom_id="unban_global_user",
                emoji="🌍",
                row=0
            )
            async def unban_global(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                if interaction_btn.user.id not in OWNER_IDS:
                    error_embed = discord.Embed(
                        title="🚫 Permission refusée",
                        description="Seuls les propriétaires du bot peuvent utiliser cette action.",
                        color=discord.Color.red()
                    )
                    await interaction_btn.response.send_message(embed=error_embed, ephemeral=True)
                    return
                
                modal = UnbanModal("global")
                await interaction_btn.response.send_modal(modal)
            
            @discord.ui.button(
                label="Unban Local",
                style=discord.ButtonStyle.success,
                custom_id="unban_local_user",
                emoji="🔓",
                row=0
            )
            async def unban_local(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                if interaction_btn.user.id not in OWNER_IDS:
                    error_embed = discord.Embed(
                        title="🚫 Permission refusée",
                        description="Seuls les propriétaires du bot peuvent utiliser cette action.",
                        color=discord.Color.red()
                    )
                    await interaction_btn.response.send_message(embed=error_embed, ephemeral=True)
                    return
                
                modal = UnbanModal("local")
                await interaction_btn.response.send_modal(modal)
                
            @discord.ui.button(
                label="En cours de traitement",
                style=discord.ButtonStyle.secondary,
                custom_id="status_pending_user",
                emoji="🔄",
                row=1
            )
            async def pending(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                await self.update_status(interaction_btn, "pending")

            @discord.ui.button(
                label="Traité",
                style=discord.ButtonStyle.success,
                custom_id="status_resolved_user",
                emoji="✅",
                row=1
            )
            async def resolved(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                await self.update_status(interaction_btn, "resolved")

            @discord.ui.button(
                label="Non pris en compte",
                style=discord.ButtonStyle.danger,
                custom_id="status_dismissed_user",
                emoji="❌",
                row=1
            )
            async def dismissed(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                await self.update_status(interaction_btn, "dismissed")

            async def update_status(self, interaction_btn: discord.Interaction, status_key: str):
                if interaction_btn.user.id not in OWNER_IDS:
                    error_embed = discord.Embed(
                        title="🚫 Permission refusée",
                        description="Vous n'avez pas la permission de modifier l'état des signalements.",
                        color=discord.Color.red()
                    )
                    await interaction_btn.response.send_message(embed=error_embed, ephemeral=True)
                    return

                status_text, status_color = STATUS_OPTIONS[status_key]
                embed.color = status_color
                embed.set_field_at(4, name="📊 État", value=status_text, inline=False)
                
                embed.set_footer(
                    text=f"Signalement par {interaction.user} • Mis à jour par {interaction_btn.user}",
                    icon_url=interaction.user.display_avatar.url
                )
                
                await message_report.edit(embed=embed)
                
                success_embed = discord.Embed(
                    title="✅ Statut mis à jour",
                    description=f"Le signalement a été marqué comme : **{status_text}**",
                    color=status_color
                )
                await interaction_btn.response.send_message(embed=success_embed, ephemeral=True)
                
                try:
                    user_notif_embed = discord.Embed(
                        title="📬 Mise à jour de votre signalement",
                        description=f"L'état de votre signalement d'utilisateur a été mis à jour :\n\n**{status_text}**",
                        color=status_color,
                        timestamp=datetime.datetime.utcnow()
                    )
                    user_notif_embed.add_field(
                        name="👤 Utilisateur signalé",
                        value=f"`{user}`",
                        inline=False
                    )
                    user_notif_embed.add_field(
                        name="📝 Motif",
                        value=f"{reason_emoji.get(reason.value, '❓')} {reason.name}",
                        inline=False
                    )
                    user_notif_embed.set_footer(text=f"Serveur: {interaction.guild.name}")
                    await interaction.user.send(embed=user_notif_embed)
                except discord.Forbidden:
                    pass

        view = StatusView()
        message_report = await reports_channel.send(embed=embed, view=view)
        
        try:
            dm_embed = discord.Embed(
                title="✅ Signalement envoyé avec succès",
                description="Votre signalement a été transmis aux modérateurs.",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            dm_embed.add_field(
                name="👤 Utilisateur signalé",
                value=f"`{user}`",
                inline=False
            )
            dm_embed.add_field(
                name="📝 Motif",
                value=f"{reason_emoji.get(reason.value, '❓')} {reason.name}",
                inline=False
            )
            dm_embed.add_field(
                name="📊 État actuel",
                value=STATUS_OPTIONS["waiting"][0],
                inline=False
            )
            dm_embed.set_footer(
                text=f"Serveur: {interaction.guild.name}",
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None
            )
            await interaction.user.send(embed=dm_embed)
            
            response_embed = discord.Embed(
                title="✅ Signalement envoyé",
                description="Votre signalement a été envoyé avec succès.\nUn message privé vous a été envoyé avec les détails.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=response_embed, ephemeral=True)
            
        except discord.Forbidden:
            response_embed = discord.Embed(
                title="✅ Signalement envoyé",
                description="Votre signalement a été envoyé avec succès.\n\n⚠️ **Note**: Je n'ai pas pu vous envoyer de message privé.\nActivez vos MPs pour recevoir les notifications de suivi.",
                color=discord.Color.gold()
            )
            await interaction.response.send_message(embed=response_embed, ephemeral=True)
        
        await asyncio.sleep(30)
        try:
            await interaction.delete_original_response()
        except (discord.NotFound, discord.HTTPException):
            pass

async def setup(bot):
    await bot.add_cog(ReportUser(bot))