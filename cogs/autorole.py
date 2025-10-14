import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime

AUTOROLE_ID = int(os.getenv('AUTOROLE_ID'))
SUPPORT_GUILD_ID = int(os.getenv('SUPPORT_GUILD_ID'))

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Vérifier si c'est le serveur de support
        if member.guild.id != SUPPORT_GUILD_ID:
            return
        
        role = member.guild.get_role(AUTOROLE_ID)
        if role:
            try:
                await member.add_roles(role)
                print(f"✅ Rôle {role.name} ajouté à {member} sur le serveur de support.")
            except discord.Forbidden:
                print(f"⚠️ Impossible d'ajouter le rôle à {member}. Permissions insuffisantes.")
            except Exception as e:
                print(f"⚠️ Erreur lors de l'ajout du rôle à {member} : {e}")
        else:
            print(f"⚠️ Rôle introuvable : {AUTOROLE_ID}")

async def setup(bot):
    await bot.add_cog(AutoRole(bot))