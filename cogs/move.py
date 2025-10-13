import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import os
import datetime

# Déplace les membres entre les salons vocaux
# Utilisable uniquement par les personnes avec la permission "Déplacer les membres" ainsi que par les OWNER_IDS

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]

class Move(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="move", description="Déplace les membres entre les salons vocaux")
    @app_commands.describe(
        source_channel="Le salon vocal source",
        target_channel="Le salon vocal cible"
    )
    async def move(self, interaction: discord.Interaction, source_channel: discord.VoiceChannel, target_channel: discord.VoiceChannel):
        # Vérifie si l'utilisateur a la permission de déplacer les membres
        if not interaction.user.guild_permissions.move_members and interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message("Vous n'avez pas la permission de déplacer des membres.", ephemeral=True)
            return

        # Vérifie si le bot a la permission de déplacer les membres
        if not interaction.guild.me.guild_permissions.move_members:
            await interaction.response.send_message("Je n'ai pas la permission de déplacer des membres.", ephemeral=True)
            return

        # Vérifie si le salon source et le salon cible sont différents
        if source_channel.id == target_channel.id:
            await interaction.response.send_message("Le salon source et le salon cible doivent être différents.", ephemeral=True)
            return

        # Récupère les membres dans le salon source
        members_to_move = source_channel.members

        if not members_to_move:
            await interaction.response.send_message("Il n'y a aucun membre à déplacer dans le salon source.", ephemeral=True)
            return

        # Déplace les membres vers le salon cible
        for member in members_to_move:
            try:
                await member.move_to(target_channel)
            except Exception as e:
                await interaction.response.send_message(f"Impossible de déplacer {member.display_name}: {e}", ephemeral=True)
                return

        await interaction.response.send_message(f"Déplacé {len(members_to_move)} membre(s) de {source_channel.name} à {target_channel.name}.", ephemeral=True)
        return
        # Déplace les membres vers le salon cible
        for member in members_to_move:
            try:
                await member.move_to(target_channel)
            except Exception as e:
                await interaction.response.send_message(f"Impossible de déplacer {member.display_name}: {e}", ephemeral=True)
                return
        await interaction.response.send_message(f"Déplacé {len(members_to_move)} membre(s) de {source_channel.name} à {target_channel.name}.", ephemeral=True)
        return

async def setup(bot):
    await bot.add_cog(Move(bot))