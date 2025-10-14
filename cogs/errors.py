import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime
import traceback
import sys

LOG_ERROR_CHANNEL_ID = int(os.getenv('LOG_ERROR_CHANNEL_ID'))

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Configurer le gestionnaire d'exceptions global
        self.old_excepthook = sys.excepthook
        sys.excepthook = self.handle_exception

    def cog_unload(self):
        # Restaurer l'ancien gestionnaire lors du déchargement
        sys.excepthook = self.old_excepthook

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Gestionnaire d'exceptions Python non gérées"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Ignorer KeyboardInterrupt
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Créer un embed pour l'erreur
        error_text = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # Limiter la taille de l'erreur pour Discord
        if len(error_text) > 4000:
            error_text = error_text[-4000:]
        
        embed = discord.Embed(
            title="🔴 Erreur Python Non Gérée",
            color=discord.Color.dark_red(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Type", value=str(exc_type.__name__), inline=False)
        embed.add_field(name="Traceback", value=f"```python\n{error_text}\n```", inline=False)
        embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")

        # Envoyer l'erreur de manière asynchrone
        self.bot.loop.create_task(self.send_error_log(embed))

        # Appeler le gestionnaire par défaut
        self.old_excepthook(exc_type, exc_value, exc_traceback)

    async def send_error_log(self, embed: discord.Embed):
        try:
            channel = self.bot.get_channel(LOG_ERROR_CHANNEL_ID)
            if not channel:
                print(f"⚠️ Salon de logs d'erreurs introuvable : {LOG_ERROR_CHANNEL_ID}")
                return
            await channel.send(embed=embed)
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi du log d'erreur : {e}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Gère les erreurs des commandes préfixées"""
        # Obtenir le traceback complet
        error_traceback = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        
        # Limiter la taille
        if len(error_traceback) > 1000:
            error_traceback = error_traceback[-1000:]

        embed = discord.Embed(
            title="❗ Erreur de commande",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Utilisateur", value=f"{ctx.author} ({ctx.author.id})", inline=False)
        embed.add_field(name="Commande", value=ctx.command.qualified_name if ctx.command else "N/A", inline=False)
        embed.add_field(name="Message", value=ctx.message.content[:1024], inline=False)
        embed.add_field(name="Erreur", value=str(error)[:1024], inline=False)
        embed.add_field(name="Traceback", value=f"```python\n{error_traceback}\n```", inline=False)
        embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")

        await self.send_error_log(embed)

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Gère les erreurs des commandes slash"""
        # Obtenir le traceback complet
        error_traceback = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        
        # Limiter la taille
        if len(error_traceback) > 1000:
            error_traceback = error_traceback[-1000:]

        embed = discord.Embed(
            title="❗ Erreur de commande slash",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Utilisateur", value=f"{interaction.user} ({interaction.user.id})", inline=False)
        embed.add_field(name="Commande", value=interaction.command.name if interaction.command else "N/A", inline=False)
        
        # Ajouter les paramètres si disponibles
        if interaction.namespace:
            params = ", ".join([f"{k}={v}" for k, v in interaction.namespace.__dict__.items()])
            if params:
                embed.add_field(name="Paramètres", value=params[:1024], inline=False)
        
        embed.add_field(name="Erreur", value=str(error)[:1024], inline=False)
        embed.add_field(name="Traceback", value=f"```python\n{error_traceback}\n```", inline=False)
        embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")

        await self.send_error_log(embed)

        # Répondre à l'utilisateur si pas encore répondu
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Une erreur s'est produite lors de l'exécution de la commande.", 
                    ephemeral=True
                )
        except:
            pass

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        """Gère les erreurs des événements (listeners)"""
        error_info = sys.exc_info()
        error_traceback = ''.join(traceback.format_exception(*error_info))
        
        # Limiter la taille
        if len(error_traceback) > 1000:
            error_traceback = error_traceback[-1000:]

        embed = discord.Embed(
            title="⚠️ Erreur d'événement",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Événement", value=event, inline=False)
        embed.add_field(name="Erreur", value=str(error_info[1])[:1024], inline=False)
        embed.add_field(name="Traceback", value=f"```python\n{error_traceback}\n```", inline=False)
        embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")

        await self.send_error_log(embed)

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))