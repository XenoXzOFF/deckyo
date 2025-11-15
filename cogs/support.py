import discord
from discord.ext import commands
from discord import app_commands
import datetime
import os
from discord.ui import Button, View
import asyncio
import requests
import json

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]
SUPPORT_GUILD_ID = int(os.getenv('SUPPORT_GUILD_ID'))
TICKET_CATEGORY_ID = int(os.getenv('TICKET_CATEGORY_ID'))
SUPPORT_LOG_CHANNEL_ID = int(os.getenv('SUPPORT_LOG_CHANNEL_ID'))
STAFF_ROLE_ID = int(os.getenv('STAFF_ROLE_ID'))
WEBAPP_URL = os.getenv('WEBAPP_URL')
API_SECRET_KEY = os.getenv('API_SECRET_KEY')

class CloseTicketView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Fermer le ticket", style=discord.ButtonStyle.red, emoji="🔒")
    async def close_ticket(self, interaction, button):
        await self.close_and_log_ticket(interaction)

    @discord.ui.button(label="Transcript", style=discord.ButtonStyle.gray, emoji="📝")
    async def create_transcript(self, interaction, button):
        await self.generate_transcript(interaction)
    
    async def generate_transcript(self, interaction):
        channel = interaction.channel
        await interaction.response.defer(ephemeral=True, thinking=True)
        messages_data = []
        async for message in channel.history(limit=None, oldest_first=True):
            messages_data.append({
                "author_name": str(message.author),
                "author_avatar": str(message.author.display_avatar.url),
                "content": message.content,
                "timestamp": message.created_at.isoformat(),
                "embeds": [embed.to_dict() for embed in message.embeds],
                "attachments": [att.url for att in message.attachments]
            })

        try:
            user_id = int(channel.name.split('-')[1])
        except (IndexError, ValueError):
            user_id = None

        transcript_data = {
            "guild_id": interaction.guild.id,
            "channel_id": channel.id,
            "channel_name": channel.name,
            "creator_id": user_id,
            "closer_id": interaction.user.id,
            "messages": messages_data
        }

        headers = {
            "X-API-Key": API_SECRET_KEY,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(f"{WEBAPP_URL}/api/transcripts", headers=headers, data=json.dumps(transcript_data))
            response.raise_for_status()
            response_data = response.json()
            transcript_url = f"{WEBAPP_URL}/transcript/{response_data['transcript_id']}"
        except requests.exceptions.RequestException as e:
            await interaction.followup.send(f"❌ Erreur lors de l'envoi du transcript au site web : {e}", ephemeral=True)
            return None

        # Envoi dans le salon de log
        log_channel = interaction.guild.get_channel(SUPPORT_LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="📝 Transcript Sauvegardé",
                description=f"Le transcript pour le ticket `{channel.name}` a été sauvegardé.\n\n**Voir le transcript en ligne**",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.utcnow()
            )
            await log_channel.send(embed=log_embed)
        
        await interaction.followup.send(f"✅ Transcript sauvegardé avec succès ! URL : {transcript_url}", ephemeral=True)
        return transcript_url

    async def close_and_log_ticket(self, interaction):
        channel = interaction.channel
        log_channel = interaction.guild.get_channel(SUPPORT_LOG_CHANNEL_ID)
        
        try:
            user_id = int(channel.name.split('-')[1])
            user = await self.bot.fetch_user(user_id)
        except (IndexError, ValueError, discord.NotFound):
            user = None
        
        transcript_url = await self.generate_transcript(interaction)
        
        try:
            if user:
                close_embed = discord.Embed(
                    title="🔒 Ticket fermé",
                    description=(
                        f"Ton ticket a été fermé par {interaction.user.mention}\n"
                        "Si tu as encore besoin d'aide, n'hésite pas à ouvrir un nouveau ticket!\n\n"
                        f"Tu peux consulter l'historique de la conversation ici." if transcript_url else ""
                    ),
                    color=discord.Color.red(),
                    timestamp=datetime.datetime.utcnow()
                )
                close_embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)

                try:
                    await user.send(embed=close_embed)
                except discord.Forbidden:
                    await interaction.followup.send(
                        "⚠️ Impossible d'envoyer un message à l'utilisateur (MPs fermés)"
                    )

            await channel.delete()
            
            if log_channel:
                log_embed = discord.Embed(
                    title="🔒 Ticket fermé",
                    description=(
                        f"**Ticket:** {channel.name}\n"
                        f"**Fermé par:** {interaction.user.mention}\n"
                        f"**Utilisateur:** {user.mention if user else 'Non trouvé'}"
                    ),
                    color=discord.Color.red(),
                    timestamp=datetime.datetime.utcnow()
                )
                if transcript_url:
                    log_embed.description += f"\n\n**Voir le transcript en ligne**"
                await log_channel.send(embed=log_embed)
                
        except discord.Forbidden:
            # La réponse est déjà deferred, on utilise followup
            await interaction.followup.send("Je n'ai pas la permission de fermer ce ticket.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Une erreur est survenue lors de la fermeture du ticket: {str(e)}", ephemeral=True)

class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="support",
        description="🎫 Ouvre un ticket de support"
    )
    async def ticket(self, interaction):
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Erreur de permission",
                description="Tu dois être administrateur du serveur pour utiliser cette commande.",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        guild = self.bot.get_guild(SUPPORT_GUILD_ID)
        if not guild:
            await interaction.response.send_message(
                "🚫 Le serveur de support est introuvable.", ephemeral=True
            )
            return

        category = guild.get_channel(TICKET_CATEGORY_ID)
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message(
                "🚫 La catégorie de tickets est introuvable.", ephemeral=True
            )
            return

        log_channel = guild.get_channel(SUPPORT_LOG_CHANNEL_ID)
        if not log_channel or not isinstance(log_channel, discord.TextChannel):
            await interaction.response.send_message(
                "🚫 Le salon de log des tickets est introuvable.", ephemeral=True
            )
            return

        staff_role = guild.get_role(STAFF_ROLE_ID)
        if not staff_role:
            await interaction.response.send_message(
                "🚫 Le rôle du staff est introuvable.", ephemeral=True
            )
            return

        existing_ticket = discord.utils.get(
            category.channels,
            name=f"ticket-{interaction.user.id}"
        )
        if existing_ticket:
            await interaction.response.send_message(
                f"⚠️ Tu as déjà un ticket ouvert!", ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            staff_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        ticket_channel = await category.create_text_channel(
            name=f"ticket-{interaction.user.id}",
            overwrites=overwrites,
            reason=f"Ticket créé par {interaction.user} via la commande /ticket"
        )

        embed = discord.Embed(
            title="🎫 Ticket de support",
            description=(
                f"Bonjour,\n\n"
                "{interaction.user.mention} a besoin d'aide sur son serveur!\n"
                "Pour discuter avec l'utilisateur, envoie simplement un message dans ce salon.\n\n"
                "Pour fermer le ticket, clique sur le bouton ci-dessous."
                
            ),
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
        
        command_guild = interaction.guild
        if command_guild:
            try:
                invite_channel = next(
                    (channel for channel in command_guild.text_channels 
                     if channel.permissions_for(command_guild.me).create_instant_invite),
                    None
                )
                
                invite_url = "❌ Impossible de créer une invitation"
                if invite_channel:
                    invite = await invite_channel.create_invite(max_age=3600)
                    invite_url = invite.url

                guild_info = (
                    f"📋 **Informations du serveur:**\n"
                    f"Nom: {command_guild.name}\n"
                    f"Propriétaire: {command_guild.owner.mention if command_guild.owner else 'Non trouvé'}\n"
                    f"Membres: {command_guild.member_count}\n"
                    f"Invitation: {invite_url}"
                )
            except discord.Forbidden:
                guild_info = "❌ Impossible de récupérer les informations du serveur"
        else:
            guild_info = "❌ Cette commande doit être utilisée dans un serveur"

        embed = discord.Embed(
            title="🎫 Ticket de support",
            description=(
                "Bonjour,\n\n"
                f"{interaction.user.mention} a besoin d'aide sur son serveur!\n"
                "Pour discuter avec l'utilisateur, envoie simplement un message dans ce salon.\n\n"
                f"{guild_info}\n\n"  
                "Pour fermer le ticket, clique sur le bouton ci-dessous.\n\n"
                "Ce ticket est enregistré."
            ),
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
        if command_guild.icon:
            embed.set_thumbnail(url=command_guild.icon.url)

        view = CloseTicketView(self.bot)
        
        await ticket_channel.send(embed=embed, view=view)
        await interaction.response.send_message(
            f"✅ Ton ticket a été créé!", ephemeral=True
        )
        log_embed = discord.Embed(
            title="🎫 Nouveau ticket créé",
            description=(
                f"**Utilisateur :** {interaction.user} ({interaction.user.id})\n"
                f"**Salon :** {ticket_channel.mention}\n"
                f"**Heure :** {datetime.datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')}"
            ),
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        log_embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
        await log_channel.send(embed=log_embed)
        try:
            dm_embed = discord.Embed(
                title="🎫 Ticket de support ouvert",
                description=(
                    f"Bonjour {interaction.user.mention},\n\n"
                "Merci d'avoir ouvert un ticket de support. Un membre du staff va te répondre dès que possible.\n"
                "Pour discuter avec le staff, envoie simplement un message dans ce salon.\n\n"
                "Pour fermer le ticket, clique sur le bouton ci-dessous.\n\n"
                "Ce ticket est enregistré."
                ),
                color=discord.Color.blue(),
                timestamp=datetime.datetime.utcnow()
            )
            dm_embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.user.send(embed=dm_embed)
        except discord.Forbidden:
            await ticket_channel.send(
                f"⚠️ {interaction.user.mention}, je n'ai pas pu t'envoyer de message en MP. "
                "Assure-toi que tes messages privés sont ouverts."
            )
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if isinstance(message.channel, discord.DMChannel):
            guild = self.bot.get_guild(SUPPORT_GUILD_ID)
            if not guild:
                return

            category = guild.get_channel(TICKET_CATEGORY_ID)
            if not category or not isinstance(category, discord.CategoryChannel):
                return

            ticket_channel = discord.utils.get(
                category.text_channels,
                name=f"ticket-{message.author.id}"
            )
            
            if not ticket_channel:
                await message.channel.send(
                    "🚫 Tu n'as pas de ticket ouvert. Utilise la commande /ticket pour en ouvrir un."
                )
                return

            embed = discord.Embed(
                title=f"💬 Message de {message.author}",
                description=message.content if message.content else "_ _",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_author(
                name=message.author.name,
                icon_url=message.author.display_avatar.url
            )
            embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")

            await ticket_channel.send(embed=embed)

            for attachment in message.attachments:
                await ticket_channel.send(attachment.url)

            await message.add_reaction("✅")

        elif isinstance(message.channel, discord.TextChannel):
            if message.channel.category and message.channel.category.id == TICKET_CATEGORY_ID:
                try:
                    user_id = int(message.channel.name.split('-')[1])
                    user = await self.bot.fetch_user(user_id)
                except (IndexError, ValueError, discord.NotFound):
                    await message.channel.send(
                        "🚫 Impossible de trouver l'utilisateur associé à ce ticket."
                    )
                    return

                try:
                    dm_embed = discord.Embed(
                        title="💬 Nouveau message dans ton ticket de support",
                        description=message.content if message.content else "_ _",
                        color=discord.Color.blue(),
                        timestamp=datetime.datetime.utcnow()
                    )
                    dm_embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")
                    await user.send(embed=dm_embed)

                    for attachment in message.attachments:
                        await user.send(attachment.url)

                except discord.Forbidden:
                    await message.channel.send(
                        f"⚠️ {message.author.mention}, je n'ai pas pu envoyer le message en MP à l'utilisateur."
                    )
                await message.add_reaction("✅")

async def setup(bot):
    await bot.add_cog(Support(bot))