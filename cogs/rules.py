import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime

RULES_CHANNEL_ID = int(os.getenv('RULES_CHANNEL_ID'))

class Rules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(RULES_CHANNEL_ID)
        if channel:
            rules_message = (
                "Bienvenue sur le serveur ! Avant de commencer, merci de lire les règles suivantes :\n\n"
                "1. Respectez tous les membres du serveur.\n"
                "2. Pas de spam ou de publicité non autorisée.\n"
                "3. Utilisez les salons appropriés pour vos discussions.\n"
                "4. Pas de contenu NSFW ou inapproprié.\n"
                "5. Suivez les instructions du staff.\n\n"
                "En rejoignant le serveur, vous acceptez de respecter ces règles. Amusez-vous bien ! 🎉"
            )
            try:
                await member.send(rules_message)
            except discord.Forbidden:
                print(f"⚠️ Impossible d'envoyer un message à {member}.")
        else:
            print(f"⚠️ Salon des règles introuvable : {RULES_CHANNEL_ID}")

async def setup(bot):
    await bot.add_cog(Rules(bot))