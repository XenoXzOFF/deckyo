import discord
from discord import app_commands
from discord.ext import commands
import os
import datetime
import asyncio

SUGGESTIONS_CHANNEL_ID = int(os.getenv('SUGGESTIONS_CHANNEL_ID'))
OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]
STATUS_OPTIONS = {
    "waiting": ("⏳ En attente", discord.Color.greyple()),
    "pending": ("🔄 En cours d'examen", discord.Color.orange()),
    "approved": ("✅ Approuvée", discord.Color.green()),
    "rejected": ("❌ Rejetée", discord.Color.red()),
    "implemented": ("🎉 Implémentée", discord.Color.purple())
}

class Suggestion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.votes = {}

    @app_commands.command(name="suggest", description="Propose une suggestion pour améliorer le bot")
    @app_commands.describe(
        suggestion="Description détaillée de votre suggestion (obligatoire)",
        image="Image ou capture d'écran pour illustrer (optionnel)"
    )
    async def suggest(
        self, 
        interaction: discord.Interaction, 
        suggestion: str,
        image: discord.Attachment = None
    ):
        if not suggestion or len(suggestion.strip()) == 0:
            error_embed = discord.Embed(
                title="🚫 Erreur",
                description="La description de la suggestion ne peut pas être vide.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        suggestions_channel = self.bot.get_channel(SUGGESTIONS_CHANNEL_ID)
        if not suggestions_channel:
            error_embed = discord.Embed(
                title="⚠️ Erreur de configuration",
                description="Le salon de suggestions est introuvable.\nVeuillez contacter un administrateur.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        if image and not image.content_type.startswith('image/'):
            error_embed = discord.Embed(
                title="🚫 Erreur",
                description="Le fichier fourni n'est pas une image valide.\nFormats acceptés: PNG, JPG, JPEG, GIF, WEBP",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="💡 Nouvelle suggestion",
            description=suggestion,
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(
            name="👤 Proposé par", 
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
            name="📊 Votes", 
            value="👍 0 | 👎 0", 
            inline=False
        )
        embed.add_field(
            name="📋 État", 
            value=STATUS_OPTIONS["waiting"][0], 
            inline=False
        )
        
        embed.set_footer(
            text=f"Suggestion de {interaction.user}",
            icon_url=interaction.user.display_avatar.url
        )
        
        if image:
            embed.set_image(url=image.url)
            embed.add_field(
                name="📎 Pièce jointe",
                value=f"[Voir l'image]({image.url})",
                inline=False
            )

        class SuggestionView(discord.ui.View):
            def __init__(self, cog):
                super().__init__(timeout=None)
                self.cog = cog
                
            @discord.ui.button(
                label="Pour",
                style=discord.ButtonStyle.success,
                custom_id="vote_upvote",
                emoji="👍"
            )
            async def upvote(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                await self.handle_vote(interaction_btn, "upvote")

            @discord.ui.button(
                label="Contre",
                style=discord.ButtonStyle.danger,
                custom_id="vote_downvote",
                emoji="👎"
            )
            async def downvote(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                await self.handle_vote(interaction_btn, "downvote")

            @discord.ui.button(
                label="En cours d'examen",
                style=discord.ButtonStyle.secondary,
                custom_id="status_pending",
                emoji="🔄",
                row=1
            )
            async def pending(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                await self.update_status(interaction_btn, "pending")

            @discord.ui.button(
                label="Approuvée",
                style=discord.ButtonStyle.success,
                custom_id="status_approved",
                emoji="✅",
                row=1
            )
            async def approved(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                await self.update_status(interaction_btn, "approved")

            @discord.ui.button(
                label="Rejetée",
                style=discord.ButtonStyle.danger,
                custom_id="status_rejected",
                emoji="❌",
                row=1
            )
            async def rejected(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                await self.update_status(interaction_btn, "rejected")

            @discord.ui.button(
                label="Implémentée",
                style=discord.ButtonStyle.primary,
                custom_id="status_implemented",
                emoji="🎉",
                row=1
            )
            async def implemented(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                await self.update_status(interaction_btn, "implemented")

            async def handle_vote(self, interaction_btn: discord.Interaction, vote_type: str):
                message_id = interaction_btn.message.id
                user_id = interaction_btn.user.id
                
                if message_id not in self.cog.votes:
                    self.cog.votes[message_id] = {"upvotes": set(), "downvotes": set()}
                
                votes = self.cog.votes[message_id]
                
                if vote_type == "upvote":
                    if user_id in votes["upvotes"]:
                        votes["upvotes"].remove(user_id)
                        action = "retiré votre vote positif"
                    else:
                        votes["downvotes"].discard(user_id)
                        votes["upvotes"].add(user_id)
                        action = "voté pour cette suggestion"
                else:  # downvote
                    if user_id in votes["downvotes"]:
                        votes["downvotes"].remove(user_id)
                        action = "retiré votre vote négatif"
                    else:
                        votes["upvotes"].discard(user_id)
                        votes["downvotes"].add(user_id)
                        action = "voté contre cette suggestion"
                
                upvote_count = len(votes["upvotes"])
                downvote_count = len(votes["downvotes"])
                
                embed.set_field_at(3, name="📊 Votes", value=f"👍 {upvote_count} | 👎 {downvote_count}", inline=False)
                
                await message_suggestion.edit(embed=embed)
                
                vote_embed = discord.Embed(
                    title="✅ Vote enregistré",
                    description=f"Vous avez {action} !",
                    color=discord.Color.green()
                )
                await interaction_btn.response.send_message(embed=vote_embed, ephemeral=True)

            async def update_status(self, interaction_btn: discord.Interaction, status_key: str):
                if interaction_btn.user.id not in OWNER_IDS:
                    error_embed = discord.Embed(
                        title="🚫 Permission refusée",
                        description="Vous n'avez pas la permission de modifier l'état des suggestions.",
                        color=discord.Color.red()
                    )
                    await interaction_btn.response.send_message(embed=error_embed, ephemeral=True)
                    return

                status_text, status_color = STATUS_OPTIONS[status_key]
                embed.color = status_color
                embed.set_field_at(4, name="📋 État", value=status_text, inline=False)
                
                embed.set_footer(
                    text=f"Suggestion de {interaction.user} • Mis à jour par {interaction_btn.user}",
                    icon_url=interaction.user.display_avatar.url
                )
                
                await message_suggestion.edit(embed=embed)
                
                success_embed = discord.Embed(
                    title="✅ Statut mis à jour",
                    description=f"La suggestion a été marquée comme : **{status_text}**",
                    color=status_color
                )
                await interaction_btn.response.send_message(embed=success_embed, ephemeral=True)
                
                try:
                    user_notif_embed = discord.Embed(
                        title="📬 Mise à jour de votre suggestion",
                        description=f"L'état de votre suggestion a été mis à jour :\n\n**{status_text}**",
                        color=status_color,
                        timestamp=datetime.datetime.utcnow()
                    )
                    user_notif_embed.add_field(
                        name="💡 Votre suggestion",
                        value=suggestion[:1024],
                        inline=False
                    )
                    user_notif_embed.set_footer(text=f"Serveur: {interaction.guild.name}")
                    await interaction.user.send(embed=user_notif_embed)
                except discord.Forbidden:
                    pass

        view = SuggestionView(self)
        message_suggestion = await suggestions_channel.send(embed=embed, view=view)
        
        self.votes[message_suggestion.id] = {"upvotes": set(), "downvotes": set()}
        
        try:
            dm_embed = discord.Embed(
                title="✅ Suggestion envoyée avec succès",
                description="Votre suggestion a été transmise à l'équipe de développement.\nLa communauté pourra voter pour ou contre votre idée !",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            dm_embed.add_field(
                name="💡 Votre suggestion",
                value=suggestion[:1024],
                inline=False
            )
            dm_embed.add_field(
                name="📋 État actuel",
                value=STATUS_OPTIONS["waiting"][0],
                inline=False
            )
            dm_embed.set_footer(
                text=f"Serveur: {interaction.guild.name}",
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None
            )
            await interaction.user.send(embed=dm_embed)
            
            response_embed = discord.Embed(
                title="✅ Suggestion envoyée",
                description="Votre suggestion a été envoyée avec succès.\nUn message privé vous a été envoyé avec les détails.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=response_embed, ephemeral=True)
            
        except discord.Forbidden:
            response_embed = discord.Embed(
                title="✅ Suggestion envoyée",
                description="Votre suggestion a été envoyée avec succès.\n\n⚠️ **Note**: Je n'ai pas pu vous envoyer de message privé.\nActivez vos MPs pour recevoir les notifications de suivi.",
                color=discord.Color.gold()
            )
            await interaction.response.send_message(embed=response_embed, ephemeral=True)
        
        await asyncio.sleep(30)
        try:
            await interaction.delete_original_response()
        except (discord.NotFound, discord.HTTPException):
            pass

async def setup(bot):
    await bot.add_cog(Suggestion(bot))