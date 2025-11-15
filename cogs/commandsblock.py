import discord
from discord.ext import commands
from discord import app_commands
import os

COMMANDS_CHANNEL_ID = int(os.getenv("COMMANDS_CHANNEL_ID"))
OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]
SUPPORT_GUILD_ID = int(os.getenv("SUPPORT_GUILD_ID"))

class CommandsBlock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.tree.interaction_check = self.interaction_check

    async def interaction_check(self, interaction):
        """Check global pour toutes les commandes slash"""
        if interaction.user.id in OWNER_IDS:
            return True

        # Si la commande est utilisée sur le serveur de support
        if interaction.guild and interaction.guild.id == SUPPORT_GUILD_ID:
            # Et si le salon n'est pas le salon de commandes autorisé
            if interaction.channel_id != COMMANDS_CHANNEL_ID:
                # Alors on bloque la commande
                await interaction.response.send_message(
                    f"🚫 Sur ce serveur, les commandes ne peuvent être utilisées que dans le salon <#{COMMANDS_CHANNEL_ID}>.",
                    ephemeral=True
                )
                return False

        # Pour tous les autres cas (autres serveurs, MPs), on autorise la commande.
        return True

    def cog_unload(self):
        """Nettoyer le check global lors du déchargement du cog"""
        self.bot.tree.interaction_check = None

async def setup(bot):
    await bot.add_cog(CommandsBlock(bot))