import discord
from discord.ext import commands
from discord import app_commands
import datetime

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="serverinfo", description="📊 Affiche des informations sur le serveur")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild

        name = guild.name
        id = guild.id
        owner = guild.owner
        member_count = guild.member_count
        created_at = guild.created_at.strftime("%d/%m/%Y %H:%M:%S")

        roles = len(guild.roles)
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)

        embed = discord.Embed(
            title=f"📊 Informations sur {name}",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
        embed.add_field(name="Nom du serveur", value=name, inline=True)
        embed.add_field(name="ID du serveur", value=id, inline=True)
        embed.add_field(name="Propriétaire", value=owner, inline=True)
        embed.add_field(name="Membres", value=member_count, inline=True)
        embed.add_field(name="Créé le", value=created_at, inline=True)
        embed.add_field(name="Rôles", value=roles, inline=True)
        embed.add_field(name="Salons textuels", value=text_channels, inline=True)
        embed.add_field(name="Salons vocaux", value=voice_channels, inline=True)
        embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerInfo(bot))