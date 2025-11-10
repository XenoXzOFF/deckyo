import discord
from discord.ext import commands
from discord import app_commands
import datetime
import io
import html
import os
from discord.ui import Button, View
import asyncio

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]
SUPPORT_GUILD_ID = int(os.getenv('SUPPORT_GUILD_ID'))
TICKET_CATEGORY_ID = int(os.getenv('TICKET_CATEGORY_ID'))
SUPPORT_LOG_CHANNEL_ID = int(os.getenv('SUPPORT_LOG_CHANNEL_ID'))
STAFF_ROLE_ID = int(os.getenv('STAFF_ROLE_ID'))

class CloseTicketView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Fermer le ticket", style=discord.ButtonStyle.red, emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        await self.close_and_log_ticket(interaction)

    @discord.ui.button(label="Transcript", style=discord.ButtonStyle.gray, emoji="📝")
    async def create_transcript(self, interaction: discord.Interaction, button: Button):
        await self.generate_transcript(interaction)

    async def generate_transcript(self, interaction: discord.Interaction):
        channel = interaction.channel
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Transcript {channel.name}</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
                
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Inter', sans-serif;
                    background: #313338;
                    color: #dcddde;
                    line-height: 1.5;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 2rem;
                }}
                
                .header {{
                    background: #2b2d31;
                    padding: 2rem;
                    border-radius: 8px;
                    margin-bottom: 2rem;
                    text-align: center;
                    border: 1px solid #1e1f22;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                
                .header h1 {{
                    color: #ffffff;
                    font-size: 2rem;
                    margin-bottom: 1rem;
                }}
                
                .message {{
                    padding: 1rem;
                    margin: 1rem 0;
                    background: #2b2d31;
                    border-radius: 8px;
                    border: 1px solid #1e1f22;
                    transition: background 0.2s;
                }}
                
                .message:hover {{
                    background: #2e3035;
                }}
                
                .author {{
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    margin-bottom: 0.5rem;
                }}
                
                .author-avatar {{
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    object-fit: cover;
                }}
                
                .message-header {{
                    display: flex;
                    align-items: baseline;
                    gap: 0.5rem;
                }}
                
                .author-name {{
                    color: #fff;
                    font-weight: 500;
                }}
                
                .timestamp {{
                    color: #a3a6aa;
                    font-size: 0.8rem;
                }}
                
                .content {{
                    color: #dcddde;
                    margin: 0.5rem 0 0.5rem 3.25rem;
                    word-wrap: break-word;
                }}
                
                .embed {{
                    margin: 0.5rem 0 0.5rem 3.25rem;
                    padding: 0.75rem;
                    background: rgba(0,0,0,0.3);
                    border-radius: 4px;
                    border-left: 4px solid;
                }}
                
                .embed-title {{
                    color: #ffffff;
                    font-size: 1rem;
                    font-weight: 600;
                    margin-bottom: 0.5rem;
                }}
                
                .embed-description {{
                    color: #dcddde;
                }}
                
                .embed-field {{
                    margin: 0.5rem 0;
                }}
                
                .embed-field-name {{
                    color: #ffffff;
                    font-weight: 600;
                    margin-bottom: 0.25rem;
                }}
                
                .attachments {{
                    margin: 0.5rem 0 0.5rem 3.25rem;
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 0.75rem;
                }}
                
                .attachment {{
                    background: rgba(0,0,0,0.2);
                    padding: 0.5rem;
                    border-radius: 4px;
                }}
                
                .attachment img {{
                    max-width: 100%;
                    border-radius: 4px;
                }}
                
                .reactions {{
                    margin: 0.5rem 0 0 3.25rem;
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.5rem;
                }}
                
                .reaction {{
                    background: rgba(0,0,0,0.2);
                    padding: 0.25rem 0.5rem;
                    border-radius: 4px;
                    display: flex;
                    align-items: center;
                    gap: 0.25rem;
                    font-size: 0.9rem;
                }}
                
                .emoji {{
                    height: 1.25rem;
                    vertical-align: middle;
                    margin: 0 0.1rem;
                }}
                
                a {{
                    color: #00a8fc;
                    text-decoration: none;
                }}
                
                a:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎫 Transcript: {channel.name}</h1>
                <p>Généré le {datetime.datetime.utcnow().strftime('%d/%m/%Y à %H:%M:%S')}</p>
            </div>
        """

        async for message in channel.history(limit=None, oldest_first=True):
            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            
            content = message.content
            if content:
                for emoji in message.guild.emojis:
                    emoji_tag = f"<:{emoji.name}:{emoji.id}>"
                    if emoji_tag in content:
                        content = content.replace(emoji_tag, f'<img class="emoji" src="{emoji.url}" alt="{emoji.name}">')
                    emoji_tag = f"<a:{emoji.name}:{emoji.id}>"
                    if emoji_tag in content:
                        content = content.replace(emoji_tag, f'<img class="emoji" src="{emoji.url}" alt="{emoji.name}">')
                
                content = html.escape(content).replace('\n', '<br>')
            else:
                content = ""

            embeds_html = ""
            for embed in message.embeds:
                embed_color = f"#{hex(embed.color.value)[2:].zfill(6)}" if embed.color else "#2f3136"
                embeds_html += f"""
                <div class="embed" style="border-color: {embed_color}">
                """
                if embed.author:
                    author_icon = f'<img src="{embed.author.icon_url}" class="author-avatar" alt="Author Icon">' if embed.author.icon_url else ''
                    embeds_html += f'<div class="embed-author">{author_icon}{html.escape(embed.author.name)}</div>'
                if embed.title:
                    embeds_html += f'<div class="embed-title">{html.escape(embed.title)}</div>'
                if embed.description:
                    embeds_html += f'<div class="embed-description">{html.escape(embed.description)}</div>'
                for field in embed.fields:
                    embeds_html += f"""
                    <div class="embed-field">
                        <div class="embed-field-name">{html.escape(field.name)}</div>
                        <div class="embed-field-value">{html.escape(field.value)}</div>
                    </div>
                    """
                if embed.footer:
                    footer_icon = f'<img src="{embed.footer.icon_url}" height="20" alt="Footer Icon">' if embed.footer.icon_url else ''
                    embeds_html += f'<div class="embed-footer">{footer_icon}{html.escape(embed.footer.text)}</div>'
                embeds_html += "</div>"

            attachments_html = ""
            if message.attachments:
                attachments_html = '<div class="attachments">'
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith('image/'):
                        attachments_html += f'''
                        <div class="attachment">
                            <img src="{attachment.url}" alt="Image">
                        </div>
                        '''
                    else:
                        attachments_html += f'''
                        <div class="attachment">
                            <a href="{attachment.url}" target="_blank">{html.escape(attachment.filename)}</a>
                        </div>
                        '''
                attachments_html += '</div>'

            reactions_html = ""
            if message.reactions:
                reactions_html = '<div class="reactions">'
                for reaction in message.reactions:
                    emoji = reaction.emoji
                    emoji_html = ""
                    if isinstance(emoji, str):  
                        emoji_html = emoji
                    else:  
                        emoji_html = f'<img class="emoji" src="{emoji.url}" alt="{emoji.name}">'
                    reactions_html += f"""
                    <div class="reaction">
                        {emoji_html}
                        <span>{reaction.count}</span>
                    </div>
                    """
                reactions_html += '</div>'


            html_content += f"""
            <div class="message">
                <div class="author">
                    <img src="{message.author.display_avatar.url}" class="author-avatar" alt="Avatar">
                    {html.escape(str(message.author))}
                </div>
                <div class="timestamp">{timestamp}</div>
                <div class="content">{content}</div>
                {embeds_html}
                {attachments_html}
                {reactions_html}
            </div>
            """

        html_content += """
        </body>
        </html>
        """

        transcript_file = discord.File(
            io.StringIO(html_content),
            filename=f"transcript-{channel.name}.html"
        )

        log_channel = interaction.guild.get_channel(SUPPORT_LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(
                f"📝 Transcript du ticket {channel.name}:",
                file=transcript_file
            )
            await interaction.response.send_message("✅ Transcript HTML envoyé dans les logs!", ephemeral=True)

    async def close_and_log_ticket(self, interaction: discord.Interaction):
        channel = interaction.channel
        log_channel = interaction.guild.get_channel(SUPPORT_LOG_CHANNEL_ID)
        
        try:
            user_id = int(channel.name.split('-')[1])
            user = await self.bot.fetch_user(user_id)
        except (IndexError, ValueError, discord.NotFound):
            user = None
        
        await self.generate_transcript(interaction)
        
        try:
            if user:
                close_embed = discord.Embed(
                    title="🔒 Ticket fermé",
                    description=(
                        f"Ton ticket a été fermé par {interaction.user.mention}\n"
                        "Si tu as encore besoin d'aide, n'hésite pas à ouvrir un nouveau ticket!"
                    ),
                    color=discord.Color.red(),
                    timestamp=datetime.datetime.utcnow()
                )
                close_embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)

                try:
                    await user.send(embed=close_embed)
                except discord.Forbidden:
                    await interaction.channel.send(
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
                await log_channel.send(embed=log_embed)
                
        except discord.Forbidden:
            await interaction.response.send_message(
                "Je n'ai pas la permission de fermer ce ticket.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"Une erreur est survenue lors de la fermeture du ticket: {str(e)}",
                ephemeral=True
            )

class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="support",
        description="🎫 Ouvre un ticket de support"
    )
    async def ticket(self, interaction: discord.Interaction):
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
    await bot.add_cog(Support(bot))