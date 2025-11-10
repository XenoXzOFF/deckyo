import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]
log_channel_id = int(os.getenv('LOG_CHANNEL_ID'))

class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="kick",
        description="👢 Expulse un utilisateur du serveur (modérateurs uniquement)"
    )
    @app_commands.describe(
        utilisateur="L'utilisateur à expulser",
        raison="La raison de l'expulsion"
    )
    async def kick(
        self,
        interaction: discord.Interaction,
        utilisateur: discord.Member,
        raison: str
    ):
        if interaction.user.id not in OWNER_IDS and not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message(
                "🚫 Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True
            )
            return

        guild = interaction.guild
        if not guild:
            await interaction.response.send_message(
                "🚫 Cette commande doit être utilisée dans un serveur.", ephemeral=True
            )
            return

        if utilisateur == interaction.user:
            await interaction.response.send_message(
                "🚫 Tu ne peux pas t'expulser toi-même.", ephemeral=True
            )
            return

        if utilisateur == guild.owner:
            await interaction.response.send_message(
                "🚫 Tu ne peux pas expulser le propriétaire du serveur.", ephemeral=True
            )
            return

        if not guild.me.guild_permissions.kick_members:
            await interaction.response.send_message(
                "🚫 Je n'ai pas la permission d'expulser des membres.", ephemeral=True
            )
            return

        if utilisateur.top_role >= interaction.user.top_role and interaction.user != guild.owner:
            await interaction.response.send_message(
                "🚫 Tu ne peux pas expulser cet utilisateur car son rôle est supérieur ou égal au tien.", ephemeral=True
            )
            return

        if utilisateur.top_role >= guild.me.top_role:
            await interaction.response.send_message(
                "🚫 Je ne peux pas expulser cet utilisateur car son rôle est supérieur ou égal au mien.", ephemeral=True
            )
            return

        full_reason = f"Expulsé par {interaction.user} | Raison: {raison}"

        try:
            embed_dm = discord.Embed(
                title="👢 Vous avez été expulsé",
                description=f"Vous avez été expulsé du serveur **{guild.name}**.\n\n**Raison :** {raison}",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.utcnow()
            )
            embed_dm.set_footer(text="Vous pouvez rejoindre le serveur à nouveau si vous avez une invitation.")
            await utilisateur.send(embed=embed_dm)
        except discord.Forbidden:
            pass

        await guild.kick(utilisateur, reason=full_reason)

        embed = discord.Embed(
            title="👢 Utilisateur expulsé",
            description=f"{utilisateur.mention} a été expulsé du serveur ✅",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Raison", value=raison)
        embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Kick(bot))