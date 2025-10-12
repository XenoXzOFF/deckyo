import discord
from discord.ext import commands
from discord import app_commands
import platform
import datetime

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.datetime.utcnow()  
        self.slash_usage = {}  
        bot.add_listener(self.on_interaction, 'on_interaction')

    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.command:  
            name = interaction.command.name
            if name in self.slash_usage:
                self.slash_usage[name] += 1
            else:
                self.slash_usage[name] = 1

    @app_commands.command(name="info", description="Affiche des informations sur le bot")
    async def info(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)

        system = platform.system()
        release = platform.release()

        now = datetime.datetime.utcnow()
        delta = now - self.start_time
        uptime_str = str(delta).split('.')[0]  

        commands_list = [cmd.name for cmd in self.bot.tree.walk_commands()]
        commands_count = len(commands_list)

        usage_list = [f"{cmd.name}: {self.slash_usage.get(cmd.name, 0)}" for cmd in self.bot.tree.walk_commands()]

        embed = discord.Embed(
            title=f"ℹ️ Informations sur {self.bot.user.name}",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Latency", value=f"`{latency} ms`", inline=True)
        embed.add_field(name="OS", value=f"`{system} {release}`", inline=True)
        embed.add_field(name="Uptime", value=uptime_str, inline=False)
        embed.add_field(name=f"Commandes actives ({commands_count})", value=", ".join(commands_list) or "`Aucune`", inline=False)
        embed.add_field(name="Utilisation des commandes", value="\n".join(usage_list) or "`Aucune`", inline=False)
        embed.set_footer(text=f"{self.bot.user.name} fait par XenoXzOFF")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Info(bot))
