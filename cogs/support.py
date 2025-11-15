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
WEBAPP_URL = os.getenv('WEBAPP_URL') # URL locale pour les requêtes API (ex: http://127.0.0.1:13966)
PUBLIC_WEBAPP_URL = os.getenv('PUBLIC_WEBAPP_URL') # URL publique pour les liens dans Discord
API_SECRET_KEY = os.getenv('API_SECRET_KEY')

class CloseTicketView(View):
    def __init__(self, bot_cog, transcript_id: str = None):
        super().__init__(timeout=None)
        self.bot_cog = bot_cog
        self.transcript_id = transcript_id

        # Ajout du bouton pour accéder directement au dashboard
        if PUBLIC_WEBAPP_URL and self.transcript_id:
            dashboard_url = f"{PUBLIC_WEBAPP_URL}/transcript/{self.transcript_id}"
            self.add_item(discord.ui.Button(label="Accéder au Dashboard", style=discord.ButtonStyle.link, url=dashboard_url, emoji="🌐"))

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        await interaction.followup.send(f"Une erreur est survenue: {error}", ephemeral=True)

    @discord.ui.button(label="Fermer le ticket", style=discord.ButtonStyle.red, emoji="🔒", custom_id="support_ticket:close")
    async def close_ticket(self, interaction, button):
        await interaction.response.defer()
        await self.bot_cog.close_and_log_ticket(interaction)

class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Ajoute la vue persistante pour qu'elle fonctionne après un redémarrage.
        # On passe transcript_id=None car il sera déterminé au moment de l'interaction.
        self.bot.add_view(CloseTicketView(self, transcript_id=None))

    async def generate_and_save_transcript(self, interaction: discord.Interaction):
        """Génère le contenu du transcript et l'envoie au site web pour sauvegarde ou mise à jour."""
        channel = interaction.channel
        
        # Vérification de la configuration
        if not WEBAPP_URL or not API_SECRET_KEY or not PUBLIC_WEBAPP_URL:
            await interaction.followup.send(
                "❌ **Erreur de configuration du bot !**\n"
                "Une ou plusieurs variables d'environnement (WEBAPP_URL, PUBLIC_WEBAPP_URL, API_SECRET_KEY) ne sont pas définies.\n"
                "Le transcript ne peut pas être sauvegardé. Veuillez contacter un administrateur.",
                ephemeral=True
            )
            return None

        # Récupération de l'historique
        messages_data = []
        async for message in channel.history(limit=None, oldest_first=True):
            messages_data.append({
                "author_name": str(message.author),
                "author_avatar": str(message.author.display_avatar.url),
                "content": message.content,
                "timestamp": message.created_at.isoformat(),
                # On ne sauvegarde que les embeds qui ne sont pas générés par le bot lui-même pour la clarté
                "embeds": [embed.to_dict() for embed in message.embeds if embed.author.name != self.bot.user.name],
                "attachments": [att.url for att in message.attachments]
            })

        # Récupération de l'ID de l'utilisateur
        try:
            user_id = int(channel.name.split('-')[1])
        except (IndexError, ValueError):
            user_id = None

        # Récupération de l'ID du transcript depuis le topic
        transcript_id = None
        if channel.topic and channel.topic.startswith("transcript-id:"):
            transcript_id = channel.topic.split(":")[1].strip()

        if not transcript_id:
            await interaction.followup.send("❌ Erreur : Impossible de trouver l'ID du transcript dans le sujet de ce salon.", ephemeral=True)
            return None

        # Préparation des données
        transcript_data = {
            "transcript_id": transcript_id, # On inclut l'ID pour la mise à jour
            "guild_id": interaction.guild.id,
            "channel_id": channel.id,
            "channel_name": channel.name,
            "creator_id": user_id,
            "closer_id": interaction.user.id,
            "messages": messages_data
        }

        headers = {"X-API-Key": API_SECRET_KEY, "Content-Type": "application/json"}
        
        # Envoi de la requête de mise à jour au site web
        try:
            # On utilise une seule route qui gère la création/mise à jour
            response = requests.post(f"{WEBAPP_URL}/api/transcripts", headers=headers, data=json.dumps(transcript_data), timeout=10)
            response.raise_for_status()
            
            # On utilise l'URL publique pour le lien
            transcript_url = f"{PUBLIC_WEBAPP_URL}/transcript/{transcript_id}"
            return transcript_url
        except requests.exceptions.RequestException as e:
            await interaction.followup.send(f"❌ Erreur lors de l'envoi du transcript au site web : {e}", ephemeral=True)
            return None

    async def close_and_log_ticket(self, interaction: discord.Interaction):
        """Génère le transcript, ferme le ticket et envoie les logs."""
        channel = interaction.channel
        log_channel = interaction.guild.get_channel(SUPPORT_LOG_CHANNEL_ID)
        
        try:
            user_id = int(channel.name.split('-')[1])
            user = await self.bot.fetch_user(user_id)
        except (IndexError, ValueError, discord.NotFound):
            user = None
        
        # On génère le transcript final avant de fermer
        transcript_url = await self.generate_and_save_transcript(interaction)
        if not transcript_url:
            # Si la génération du transcript échoue, on s'arrête pour ne pas perdre l'historique
            await interaction.followup.send("❌ La fermeture a été annulée car la sauvegarde du transcript a échoué.", ephemeral=True)
            return
        
        # Envoi du message privé à l'utilisateur
        if user:
            try:
                close_embed = discord.Embed(
                    title="🔒 Ticket fermé",
                    description=(
                        f"Ton ticket a été fermé par {interaction.user.mention}.\n"
                        "Si tu as encore besoin d'aide, n'hésite pas à ouvrir un nouveau ticket !\n\n"
                        "Tu peux consulter l'historique de la conversation ici."
                    ),
                    url=transcript_url,
                    color=discord.Color.red(),
                    timestamp=datetime.datetime.utcnow()
                )
                close_embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
                await user.send(embed=close_embed)
            except discord.Forbidden:
                pass # L'utilisateur a les MPs fermés, on continue

        # Suppression du salon
        await channel.delete(reason=f"Ticket fermé par {interaction.user.name}")
        
        # Envoi du log de fermeture
        if log_channel:
            log_embed = discord.Embed(
                title="🔒 Ticket fermé",
                description=(
                    f"**Ticket:** `{channel.name}`\n"
                    f"**Fermé par:** {interaction.user.mention}\n"
                    f"**Utilisateur:** {user.mention if user else 'Non trouvé'}"
                ),
                url=transcript_url,
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            await log_channel.send(embed=log_embed)

    async def cog_load(self):
        """Ajoute dynamiquement le bouton du dashboard aux vues existantes au démarrage."""
        view = CloseTicketView(self, transcript_id=None)
        # Pour chaque message avec cette vue, on met à jour le bouton
        async for guild in self.bot.fetch_guilds():
            # Cette partie est une optimisation, si vous avez beaucoup de messages,
            # il faudrait une méthode plus ciblée pour retrouver les messages de ticket.
            # Pour l'instant, cette approche simple devrait fonctionner.
            pass

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

        # Création du transcript initial vide sur le site web
        initial_transcript_data = {
            "guild_id": guild.id,
            "channel_name": f"ticket-{interaction.user.id}",
            "creator_id": interaction.user.id,
            "messages": []
        }
        headers = {"X-API-Key": API_SECRET_KEY, "Content-Type": "application/json"}
        transcript_id = None
        try:
            response = requests.post(f"{WEBAPP_URL}/api/transcripts/init", headers=headers, data=json.dumps(initial_transcript_data), timeout=10)
            response.raise_for_status()
            transcript_id = response.json().get('transcript_id')
        except requests.exceptions.RequestException as e:
            await interaction.response.send_message(f"❌ Impossible de créer le transcript initial sur le site web : {e}", ephemeral=True)
            return

        if not transcript_id:
            await interaction.response.send_message("❌ Erreur lors de la récupération de l'ID du transcript depuis le site web.", ephemeral=True)
            return

        channel_topic = f"Ticket pour {interaction.user.name} | transcript-id:{transcript_id}"

        ticket_channel = await category.create_text_channel(
            name=f"ticket-{interaction.user.id}",
            overwrites=overwrites,
            topic=channel_topic,
            reason=f"Ticket créé par {interaction.user}"
        )

        # Mise à jour du transcript avec l'ID du salon
        update_data = {"transcript_id": transcript_id, "channel_id": ticket_channel.id}
        requests.post(f"{WEBAPP_URL}/api/transcripts", headers=headers, data=json.dumps(update_data), timeout=10) # Update with channel_id

        embed = discord.Embed(
            title="🎫 Ticket de support",
            description=(
                f"{interaction.user.mention} a besoin d'aide sur son serveur!\n\n"
                "**Pour discuter avec l'utilisateur, envoyez simplement un message dans ce salon.**\n\n"
                "Pour fermer le ticket, cliquez sur le bouton ci-dessous."                
            ),
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)

        view = CloseTicketView(self, transcript_id=transcript_id)
        
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
                    "Merci d'avoir ouvert un ticket de support. Un membre du staff va vous répondre dès que possible dans le salon qui vient d'être créé."
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
    async def on_message(self, message: discord.Message):
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
    cog = Support(bot)
    await bot.add_cog(cog)