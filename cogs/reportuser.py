import discord
from discord import app_commands
from discord.ext import commands
import os
import datetime
import asyncio

USER_REPORST_CHANNEL_ID = int(os.getenv('USER_REPORST_CHANNEL_ID'))
OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]
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

        reports_channel = self.bot.get_channel(USER_REPORST_CHANNEL_ID)
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

        class StatusView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)  
                
            @discord.ui.button(
                label="En cours de traitement",
                style=discord.ButtonStyle.secondary,
                custom_id="status_pending_user",
                emoji="🔄"
            )
            async def pending(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                await self.update_status(interaction_btn, "pending")

            @discord.ui.button(
                label="Traité",
                style=discord.ButtonStyle.success,
                custom_id="status_resolved_user",
                emoji="✅"
            )
            async def resolved(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                await self.update_status(interaction_btn, "resolved")

            @discord.ui.button(
                label="Non pris en compte",
                style=discord.ButtonStyle.danger,
                custom_id="status_dismissed_user",
                emoji="❌"
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