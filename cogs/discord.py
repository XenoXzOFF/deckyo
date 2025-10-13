import discord
from discord.ext import commands
from discord import app_commands
import datetime

class InviteDiscord(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="discord", description="🔗 Obtiens le lien du serveur discord")
    async def InviteDiscord(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔗 Serveur discord",
            description="[Clique ici pour rejoindre le serveur discord!](https://discord.gg/h4zqdGYs)\n\nSi le lien ne marche pas : https://discord.gg/h4zqdGYs \n\nBesoin d'aide? /support sur ton serveur.",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)
        
        try:
            await interaction.user.send(embed=embed)
            await interaction.response.send_message("📨 Je t'ai envoyé le lien d'invitation en MP!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Je ne peux pas t'envoyer de MP. Vérifie que tes MPs sont activés!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(InviteDiscord(bot))