import discord
from discord.ext import commands
from discord import app_commands
import platform
import psutil
import time
import datetime

class BotInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        self.command_usage = 0

        # Écouteur pour compter les commandes exécutées
        @bot.listen("on_app_command_completion")
        async def on_app_command_completion(interaction, command):
            self.command_usage += 1

    def format_uptime(self):
        """Retourne le temps de fonctionnement formaté."""
        uptime_seconds = int(time.time() - self.start_time)
        return str(datetime.timedelta(seconds=uptime_seconds))

    @app_commands.command(name="botinfo", description="Affiche les informations du bot")
    async def info_command(self, interaction: discord.Interaction):
        # Informations système
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
        python_version = platform.python_version()
        discord_version = discord.__version__

        # Informations bot
        latency = round(self.bot.latency * 1000)  # ms
        uptime = self.format_uptime()
        guild_count = len(self.bot.guilds)
        user_count = len(set(self.bot.get_all_members()))
        command_count = len(list(self.bot.tree.walk_commands()))
        command_usage = self.command_usage

        embed = discord.Embed(
            title="🤖 Informations du Bot",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.utcnow()
        )

        embed.add_field(name="📡 Latence", value=f"{latency} ms", inline=True)
        embed.add_field(name="⏱️ Uptime", value=uptime, inline=True)
        embed.add_field(name="🧠 OS", value=os_info, inline=False)
        embed.add_field(name="⚙️ CPU", value=f"{cpu_percent}%", inline=True)
        embed.add_field(name="💾 RAM", value=f"{memory.percent}%", inline=True)
        embed.add_field(name="🌐 Serveurs", value=f"{guild_count}", inline=True)
        embed.add_field(name="🧾 Commandes disponibles", value=f"{command_count}", inline=True)
        embed.add_field(name="📊 Utilisation des commandes", value=f"{command_usage}", inline=True)
        embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(BotInfo(bot))
