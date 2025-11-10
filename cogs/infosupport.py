import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime

INFO_SUPPORT_CHANNEL_ID = int(os.getenv('INFO_SUPPORT_CHANNEL_ID'))

class InfoSupport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_infosupport_message(self):
        channel = self.bot.get_channel(INFO_SUPPORT_CHANNEL_ID)
        if not channel:
            print(f"⚠️ Salon des informations de support introuvable : {INFO_SUPPORT_CHANNEL_ID}")
            return

        try:
            async for message in channel.history(limit=100):
                await message.delete()
        except discord.Forbidden:
            print(f"⚠️ Permissions insuffisantes pour supprimer les messages dans le salon {channel.name}.")
        except Exception as e:
            print(f"⚠️ Erreur lors de la suppression des messages dans le salon {channel.name} : {e}")


        infosupport_text = (
            "Besoin d'aide avec moi ?\n\n"
            "1. Allez dans le serveur où vous avez besoin d'aide.\n"
            "2. Allez dans nimporte quel salon.\n"
            "3. Faites la commande /support avec le bot <@!1192768970466533426>.\n"
            "4. Expliquez votre problème au support.\n"
            "5. Suivez les consignes du support.\n\n"
            "Restez toujours poli et respectueux envers le support !"
        )

        embed = discord.Embed(title="Aide avec le support", description=infosupport_text, color=discord.Color.blue(), timestamp=datetime.datetime.utcnow())
        embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")
        message = await channel.send(embed=embed)
        await message.add_reaction("✅")
        print(f"✅ Message des support envoyé dans le salon {channel.name}.")

async def setup(bot):
    cog = InfoSupport(bot)
    await bot.add_cog(cog)
    await cog.send_infosupport_message()