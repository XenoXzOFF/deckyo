import discord
from discord.ext import commands
from discord import app_commands
import datetime

class Invite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="invite", description="🔗 Obtiens le lien d'invitation du bot")
    async def invite(self, interaction):
        embed = discord.Embed(
            title="🔗 Invitation du bot",
            description="[Clique ici pour inviter le bot à ton serveur!](https://discord.com/oauth2/authorize?client_id=1192768970466533426&permissions=8&integration_type=0&scope=bot+applications.commands)\n\nSi le lien ne marche pas : https://discord.com/oauth2/authorize?client_id=1192768970466533426&permissions=8&integration_type=0&scope=bot+applications.commands \n\nBesoin d'aide? /support sur ton serveur.",
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
    await bot.add_cog(Invite(bot))