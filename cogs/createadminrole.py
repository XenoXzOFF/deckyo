import discord
from discord.ext import commands
from discord import app_commands
import datetime
import os
import asyncio

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]


class CreateAdminRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="createadminrole",
        description="🛠️ Crée un rôle administrateur et le place en haut de la liste (développeurs uniquement)"
    )
    @app_commands.describe(
        role_name="Le nom du rôle à créer (par défaut: Admin)",
        color="La couleur du rôle en hexadécimal (par défaut: #FF0000)"
    )
    async def createadminrole(
        self,
        interaction: discord.Interaction,
        role_name: str = "Admin",
        color: str = "#FF0000"
    ):
        """Crée un rôle avec les permissions administrateur et le place en haut de la liste des rôles"""
        if interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message(
                "🚫 Tu n’as pas la permission d’utiliser cette commande.", ephemeral=True
            )
            return

        guild = interaction.guild
        if not guild:
            await interaction.response.send_message(
                "🚫 Cette commande doit être utilisée dans un serveur.", ephemeral=True
            )
            return

        existing_role = discord.utils.get(guild.roles, name=role_name)
        if existing_role:
            await interaction.response.send_message(
                f"⚠️ Le rôle `{role_name}` existe déjà.", ephemeral=True
            )
            return

        try:
            color_value = int(color.lstrip('#'), 16)
            new_role = await guild.create_role(
                name=role_name,
                permissions=discord.Permissions(administrator=True),
                color=discord.Color(color_value),
                reason="Rôle administrateur créé via la commande createadminrole"
            )

            await new_role.edit(position=len(guild.roles) - 1)

            embed = discord.Embed(
                title="🛠️ Rôle Administrateur Créé",
                description=f"Le rôle `{role_name}` a été créé avec succès et placé en haut de la liste des rôles ✅",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)
            await asyncio.sleep(5)
            try:
                await interaction.delete_original_response()
            except Exception: pass
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur de création",
                description=f"Impossible de créer le rôle `{role_name}`.\n**Erreur :** {e}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
            await interaction.response.send_message(embed=embed)
            await asyncio.sleep(5)
            try:
                await interaction.delete_original_response()
            except Exception: pass

async def setup(bot):
    await bot.add_cog(CreateAdminRole(bot))

