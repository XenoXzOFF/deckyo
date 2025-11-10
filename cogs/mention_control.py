import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import datetime

log_channel_id = int(os.getenv('LOG_CHANNEL_ID'))

class MentionControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings_file = "mention_control_settings.json"
        self.settings = self.load_settings()

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        return {}

    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def get_guild_settings(self, guild_id):
        guild_id_str = str(guild_id)
        if guild_id_str not in self.settings:
            self.settings[guild_id_str] = {
                "enabled": False,
                "allowed_roles": [],
                "bypass_roles": [],
                "allowed_channels": [],
                "config": {
                    "delete_message": True,
                    "warn_in_dm": True,
                    "action": "none",
                    "timeout_duration_minutes": 10
                }
            }
        return self.settings[guild_id_str]

    mentionconfig = app_commands.Group(name="mentionconfig", description="Configure le système de contrôle des mentions.", default_permissions=discord.Permissions(administrator=True))
    mentionrole = app_commands.Group(name="mentionrole", description="Gère les rôles pour le contrôle des mentions.", default_permissions=discord.Permissions(administrator=True))
    mentionchannel = app_commands.Group(name="mentionchannel", description="Gère les salons pour le contrôle des mentions.", default_permissions=discord.Permissions(administrator=True))

    @mentionconfig.command(name="enable", description="Active le contrôle des mentions sur ce serveur.")
    @app_commands.checks.has_permissions(administrator=True)
    async def mentionconfig_enable(self, interaction: discord.Interaction):
        settings = self.get_guild_settings(interaction.guild.id)
        settings["enabled"] = True
        self.save_settings()
        await interaction.response.send_message("✅ Le contrôle des mentions a été activé.", ephemeral=True)

    @mentionconfig.command(name="disable", description="Désactive le contrôle des mentions sur ce serveur.")
    @app_commands.checks.has_permissions(administrator=True)
    async def mentionconfig_disable(self, interaction: discord.Interaction):
        settings = self.get_guild_settings(interaction.guild.id)
        settings["enabled"] = False
        self.save_settings()
        await interaction.response.send_message("❌ Le contrôle des mentions a été désactivé.", ephemeral=True)

    @mentionconfig.command(name="action", description="Définit l'action à effectuer lors d'une mention non autorisée.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.choices(action=[
        app_commands.Choice(name="Aucune action", value="none"),
        app_commands.Choice(name="Timeout", value="timeout"),
        app_commands.Choice(name="Kick", value="kick"),
        app_commands.Choice(name="Ban", value="ban"),
    ])
    async def mentionconfig_action(self, interaction: discord.Interaction, action: app_commands.Choice[str]):
        settings = self.get_guild_settings(interaction.guild.id)
        settings["config"]["action"] = action.value
        self.save_settings()
        await interaction.response.send_message(f"L'action en cas de mention non autorisée est maintenant : **{action.name}**.", ephemeral=True)

    @mentionconfig.command(name="timeout_duration", description="Définit la durée du timeout en minutes.")
    @app_commands.checks.has_permissions(administrator=True)
    async def mentionconfig_timeout_duration(self, interaction: discord.Interaction, minutes: app_commands.Range[int, 1, None]):
        settings = self.get_guild_settings(interaction.guild.id)
        settings["config"]["timeout_duration_minutes"] = minutes
        self.save_settings()
        await interaction.response.send_message(f"La durée du timeout est maintenant de **{minutes}** minute(s).", ephemeral=True)

    @mentionconfig.command(name="delete_message", description="Choisir si le message de mention doit être supprimé.")
    @app_commands.checks.has_permissions(administrator=True)
    async def mentionconfig_delete_message(self, interaction: discord.Interaction, delete: bool):
        settings = self.get_guild_settings(interaction.guild.id)
        settings["config"]["delete_message"] = delete
        self.save_settings()
        await interaction.response.send_message(f"La suppression du message est maintenant **{'activée' if delete else 'désactivée'}**.", ephemeral=True)

    @mentionconfig.command(name="warn_user", description="Choisir si un avertissement doit être envoyé en MP.")
    @app_commands.checks.has_permissions(administrator=True)
    async def mentionconfig_warn_user(self, interaction: discord.Interaction, warn: bool):
        settings = self.get_guild_settings(interaction.guild.id)
        settings["config"]["warn_in_dm"] = warn
        self.save_settings()
        await interaction.response.send_message(f"L'avertissement en MP est maintenant **{'activé' if warn else 'désactivé'}**.", ephemeral=True)

    @mentionconfig.command(name="show", description="Affiche la configuration actuelle du contrôle des mentions.")
    @app_commands.checks.has_permissions(administrator=True)
    async def mentionconfig_show(self, interaction: discord.Interaction):
        settings = self.get_guild_settings(interaction.guild.id)
        
        embed = discord.Embed(title="Configuration du Contrôle des Mentions", color=discord.Color.blue(), timestamp=datetime.datetime.utcnow())
        embed.set_footer(text=f"Serveur : {interaction.guild.name}")

        embed.add_field(name="Statut", value="✅ Activé" if settings['enabled'] else "❌ Désactivé", inline=False)

        allowed_roles = [f"<@&{r}>" for r in settings['allowed_roles']] or ["Aucun"]
        bypass_roles = [f"<@&{r}>" for r in settings['bypass_roles']] or ["Aucun"]
        allowed_channels = [f"<#{c}>" for c in settings['allowed_channels']] or ["Aucun"]

        embed.add_field(name="Rôles mentionnables", value=", ".join(allowed_roles), inline=False)
        embed.add_field(name="Rôles de Bypass", value=", ".join(bypass_roles), inline=False)
        embed.add_field(name="Salons autorisés", value=", ".join(allowed_channels), inline=False)

        config = settings['config']
        embed.add_field(name="Action", value=config['action'], inline=True)
        if config['action'] == 'timeout':
            embed.add_field(name="Durée Timeout", value=f"{config['timeout_duration_minutes']} min", inline=True)
        embed.add_field(name="Supprimer le message", value="Oui" if config['delete_message'] else "Non", inline=True)
        embed.add_field(name="Avertir en MP", value="Oui" if config['warn_in_dm'] else "Non", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @mentionrole.command(name="add", description="Ajoute un rôle à une liste de contrôle.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.choices(type=[
        app_commands.Choice(name="Rôle mentionnable", value="allowed_roles"),
        app_commands.Choice(name="Rôle de Bypass", value="bypass_roles"),
    ])
    async def mentionrole_add(self, interaction: discord.Interaction, type: app_commands.Choice[str], role: discord.Role):
        settings = self.get_guild_settings(interaction.guild.id)
        if role.id not in settings[type.value]:
            settings[type.value].append(role.id)
            self.save_settings()
            await interaction.response.send_message(f"Le rôle {role.mention} a été ajouté à la liste `{type.name}`.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Le rôle {role.mention} est déjà dans la liste `{type.name}`.", ephemeral=True)

    @mentionrole.command(name="remove", description="Retire un rôle d'une liste de contrôle.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.choices(type=[
        app_commands.Choice(name="Rôle mentionnable", value="allowed_roles"),
        app_commands.Choice(name="Rôle de Bypass", value="bypass_roles"),
    ])
    async def mentionrole_remove(self, interaction: discord.Interaction, type: app_commands.Choice[str], role: discord.Role):
        settings = self.get_guild_settings(interaction.guild.id)
        if role.id in settings[type.value]:
            settings[type.value].remove(role.id)
            self.save_settings()
            await interaction.response.send_message(f"Le rôle {role.mention} a été retiré de la liste `{type.name}`.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Le rôle {role.mention} n'est pas dans la liste `{type.name}`.", ephemeral=True)

    @mentionrole.command(name="list", description="Affiche les rôles configurés.")
    @app_commands.checks.has_permissions(administrator=True)
    async def mentionrole_list(self, interaction: discord.Interaction):
        settings = self.get_guild_settings(interaction.guild.id)
        allowed = [f"<@&{r}>" for r in settings['allowed_roles']] or ["Aucun"]
        bypass = [f"<@&{r}>" for r in settings['bypass_roles']] or ["Aucun"]
        embed = discord.Embed(title="Rôles configurés", color=discord.Color.blue())
        embed.add_field(name="Rôles mentionnables", value="\n".join(allowed), inline=False)
        embed.add_field(name="Rôles de Bypass", value="\n".join(bypass), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @mentionchannel.command(name="add", description="Ajoute un salon où les mentions sont autorisées.")
    @app_commands.checks.has_permissions(administrator=True)
    async def mentionchannel_add(self, interaction: discord.Interaction, channel: discord.TextChannel):
        settings = self.get_guild_settings(interaction.guild.id)
        if channel.id not in settings['allowed_channels']:
            settings['allowed_channels'].append(channel.id)
            self.save_settings()
            await interaction.response.send_message(f"Le salon {channel.mention} a été ajouté aux salons autorisés.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Le salon {channel.mention} est déjà autorisé.", ephemeral=True)

    @mentionchannel.command(name="remove", description="Retire un salon des salons autorisés.")
    @app_commands.checks.has_permissions(administrator=True)
    async def mentionchannel_remove(self, interaction: discord.Interaction, channel: discord.TextChannel):
        settings = self.get_guild_settings(interaction.guild.id)
        if channel.id in settings['allowed_channels']:
            settings['allowed_channels'].remove(channel.id)
            self.save_settings()
            await interaction.response.send_message(f"Le salon {channel.mention} a été retiré des salons autorisés.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Le salon {channel.mention} n'est pas dans la liste des salons autorisés.", ephemeral=True)

    @mentionchannel.command(name="list", description="Affiche les salons où les mentions sont autorisées.")
    @app_commands.checks.has_permissions(administrator=True)
    async def mentionchannel_list(self, interaction: discord.Interaction):
        settings = self.get_guild_settings(interaction.guild.id)
        channels = [f"<#{c}>" for c in settings['allowed_channels']] or ["Aucun"]
        embed = discord.Embed(title="Salons autorisés pour les mentions", description="\n".join(channels), color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        settings = self.get_guild_settings(message.guild.id)
        if not settings["enabled"]:
            return

        if message.author.guild_permissions.administrator:
            return

        if any(role.id in settings["bypass_roles"] for role in message.author.roles):
            return

        if settings["allowed_channels"] and message.channel.id in settings["allowed_channels"]:
            return

        mentioned_protected_roles = [role for role in message.role_mentions if role.id in settings["allowed_roles"]]
        if not mentioned_protected_roles:
            return

        author = message.author
        guild = message.guild
        config = settings["config"]
        log_channel = self.bot.get_channel(log_channel_id)
        
        mentioned_roles_str = ", ".join([r.name for r in mentioned_protected_roles])
        reason = f"Mention non autorisée du rôle: {mentioned_roles_str}"

        if config["delete_message"]:
            try:
                await message.delete()
            except discord.Forbidden:
                if log_channel:
                    await log_channel.send(f"⚠️ Impossible de supprimer le message de {author.mention} dans {message.channel.mention} (permissions manquantes).")
            except discord.NotFound:
                pass

        dm_sent = False
        if config["warn_in_dm"]:
            try:
                embed_dm = discord.Embed(
                    title="🚫 Mention non autorisée",
                    description=f"Vous avez mentionné un ou plusieurs rôles protégés (`{mentioned_roles_str}`) dans le salon {message.channel.mention} du serveur **{guild.name}**.",
                    color=discord.Color.orange(),
                    timestamp=datetime.datetime.utcnow()
                )
                action_text = "Aucune action automatique n'a été prise, mais cela a été enregistré."
                if config["action"] != "none":
                    action_text = f"L'action suivante a été appliquée : **{config['action'].capitalize()}**."
                embed_dm.add_field(name="Conséquence", value=action_text)
                embed_dm.set_footer(text="Veuillez respecter les règles du serveur.")
                await author.send(embed=embed_dm)
                dm_sent = True
            except discord.Forbidden:
                pass

        action_taken = "Aucune"
        action_details = ""

        if config["action"] == "timeout":
            duration = datetime.timedelta(minutes=config["timeout_duration_minutes"])
            try:
                await author.timeout(duration, reason=reason)
                action_taken = "Timeout"
                action_details = f"Durée: {config['timeout_duration_minutes']} minutes"
                if dm_sent:
                    try:
                        await author.send(f"Vous avez été exclu temporairement pour **{config['timeout_duration_minutes']} minutes**.")
                    except discord.Forbidden:
                        pass
            except discord.Forbidden:
                action_taken = "Timeout (Échec)"
                action_details = "Permissions manquantes pour timeout."
            except discord.HTTPException as e:
                action_taken = "Timeout (Échec)"
                action_details = f"Erreur HTTP: {e}"

        elif config["action"] == "kick":
            try:
                await guild.kick(author, reason=reason)
                action_taken = "Kick"
            except discord.Forbidden:
                action_taken = "Kick (Échec)"
                action_details = "Permissions manquantes pour kick."
            except discord.HTTPException as e:
                action_taken = "Kick (Échec)"
                action_details = f"Erreur HTTP: {e}"

        elif config["action"] == "ban":
            try:
                await guild.ban(author, reason=reason, delete_message_days=0)
                action_taken = "Ban"
            except discord.Forbidden:
                action_taken = "Ban (Échec)"
                action_details = "Permissions manquantes pour ban."
            except discord.HTTPException as e:
                action_taken = "Ban (Échec)"
                action_details = f"Erreur HTTP: {e}"

        if log_channel:
            embed_log = discord.Embed(
                title="🚨 Mention non autorisée détectée",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed_log.set_author(name=guild.name, icon_url=guild.icon.url if guild.icon else None)
            embed_log.add_field(name="Utilisateur", value=f"{author.mention} ({author.id})", inline=False)
            embed_log.add_field(name="Salon", value=message.channel.mention, inline=False)
            embed_log.add_field(name="Rôles mentionnés", value=mentioned_roles_str, inline=False)
            
            if message.content:
                embed_log.add_field(name="Message", value=f"```{discord.utils.escape_markdown(message.content[:1000])}```", inline=False)

            embed_log.add_field(name="Action prise", value=action_taken, inline=True)
            if action_details:
                embed_log.add_field(name="Détails de l'action", value=action_details, inline=True)
            
            embed_log.add_field(name="Message supprimé", value="Oui" if config["delete_message"] else "Non", inline=True)
            embed_log.add_field(name="MP envoyé", value="Oui" if dm_sent else "Non (ou échec)", inline=True)

            await log_channel.send(embed=embed_log)

async def setup(bot):
    await bot.add_cog(MentionControl(bot))