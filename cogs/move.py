import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import os
import datetime

# Déplace les membres entre les salons vocaux
# Utilisable uniquement par les personnes avec la permission "Déplacer les membres" ainsi que par les OWNER_IDS
# J'aimerais déplacer un membre en particulier en choisissant le salon de destination
# Les OWNER_IDS peuvent déplacer n'importe qui et nimporte où
# Je ne veux plus le source channel, juste le membre et le destination channel

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]
MOVE_COOLDOWN = 10  # secondes

class Move(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_move_time = None
        self.move_lock = asyncio.Lock()

    @app_commands.command(name="move", description="Déplace un membre vers un autre salon vocal")
    @app_commands.describe(member="Le membre à déplacer", destination="Le salon vocal de destination")
    async def move(self, interaction: discord.Interaction, member: discord.Member, destination: discord.VoiceChannel):
        if not interaction.user.guild_permissions.move_members and interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message("🚫 Tu n'as pas la permission de déplacer des membres.", ephemeral=True)
            return

        if member.voice is None:
            await interaction.response.send_message(f"⚠️ {member.mention} n'est pas dans un salon vocal.", ephemeral=True)
            return

        if member.voice.channel == destination:
            await interaction.response.send_message(f"⚠️ {member.mention} est déjà dans {destination.mention}.", ephemeral=True)
            return

        async with self.move_lock:
            now = datetime.datetime.utcnow()
            if self.last_move_time and (now - self.last_move_time).total_seconds() < MOVE_COOLDOWN:
                wait_time = MOVE_COOLDOWN - (now - self.last_move_time).total_seconds()
                await interaction.response.send_message(f"⏳ Veuillez attendre {wait_time:.1f} secondes avant de déplacer à nouveau.", ephemeral=True)
                return

            try:
                await member.move_to(destination)
                self.last_move_time = now
                await interaction.response.send_message(f"✅ {member.mention} a été déplacé vers {destination.mention}.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ Impossible de déplacer {member.mention}: {str(e)}", ephemeral=True)
                return
            await asyncio.sleep(MOVE_COOLDOWN)
            self.last_move_time = None

async def setup(bot):
    await bot.add_cog(Move(bot))