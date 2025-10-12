import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime

LOG_ERROR_CHANNEL_ID = int(os.getenv('LOG_ERROR_CHANNEL_ID'))

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_error_log(self, embed: discord.Embed):
        channel = self.bot.get_channel(LOG_ERROR_CHANNEL_ID)
        if not channel:
            print(f"⚠️ Salon de logs d'erreurs introuvable : {LOG_ERROR_CHANNEL_ID}")
            return
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        embed = discord.Embed(title="❗ Erreur de commande", color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Utilisateur", value=f"{ctx.author} ({ctx.author.id})", inline=False)
        embed.add_field(name="Commande", value=ctx.command.qualified_name if ctx.command else "N/A", inline=False)
        embed.add_field(name="Message", value=ctx.message.content, inline=False)
        embed.add_field(name="Erreur", value=str(error), inline=False)
        embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")

        await self.send_error_log(embed)

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        embed = discord.Embed(title="❗ Erreur de commande slash", color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Utilisateur", value=f"{interaction.user} ({interaction.user.id})", inline=False)
        embed.add_field(name="Commande", value=interaction.command.name if interaction.command else "N/A", inline=False)
        embed.add_field(name="Erreur", value=str(error), inline=False)
        embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")

        await self.send_error_log(embed)

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))