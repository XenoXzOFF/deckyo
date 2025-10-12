import discord
from discord.ext import commands, tasks
from discord import app_commands
import itertools
import asyncio
import os

OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]

ACTIVITY_CHOICES = [
    app_commands.Choice(name="Joue", value="play"),
    app_commands.Choice(name="Regarde", value="watch"),
    app_commands.Choice(name="Écoute", value="listen"),
    app_commands.Choice(name="Stream", value="stream")
]

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status_messages = None 
        self.change_status_loop.start()
        self.temp_status_task = None
        self.is_temp_status = False
        self.update_status_info()

    def count_lines_of_code(self):
        total_lines = 0
        for root, dirs, files in os.walk(os.path.dirname(os.path.dirname(__file__))):
            for file in files:
                if file.endswith('.py'):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            lines = [line for line in f.readlines() if line.strip() and not line.strip().startswith('#')]
                            total_lines += len(lines)
                    except Exception as e:
                        print(f"Erreur lors de la lecture de {file}: {e}")
        return total_lines

    def count_commands(self):
        command_count = 0
        for command in self.bot.tree.walk_commands():
            command_count += 1
        return command_count

    def update_status_info(self):
        lines = self.count_lines_of_code()
        commands = self.count_commands()
        guilds = len(self.bot.guilds)
        
        self.status_messages = itertools.cycle([
            f"+ {commands} commandes disponibles ⚡",
            f"{lines} lignes de code 💻",
            f"{guilds} serveurs 🌐",
            "besoin d'aide? /support 📬",
            "les développeurs! 👀",
            "fait par XenoXzOFF ❤️",
            "pour vous servir! 🤖",
            "invitez-moi! /invite ➕",
            "info: /info ℹ️"
        ])

    @tasks.loop(seconds=20)  
    async def change_status_loop(self):
        if not self.is_temp_status and not self.temp_status_task:  
            if not self.status_messages:
                self.update_status_info()
            await self.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name=next(self.status_messages)
                )
            )

    @app_commands.command(
        name="setstatus",
        description="Changer le statut du bot temporairement avec type et durée"
    )
    @app_commands.describe(
        status="Le message du statut",
        duration="Durée en secondes (0 ou négatif = permanent)",
        activity_type="Type d'activité",
        stream_channel="Nom de la chaîne si type Stream"
    )
    @app_commands.choices(activity_type=ACTIVITY_CHOICES)
    async def set_status(
        self,
        interaction: discord.Interaction,
        status: str,
        duration: int,
        activity_type: app_commands.Choice[str],
        stream_channel: str = None
    ):
        if interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message(
                "🚫 Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True
            )
            return

        self.change_status_loop.stop()
        
        type_mapping = {
            "play": discord.ActivityType.playing,
            "watch": discord.ActivityType.watching,
            "listen": discord.ActivityType.listening,
            "stream": discord.ActivityType.streaming
        }

        activity_type_enum = type_mapping[activity_type.value]

        if activity_type_enum == discord.ActivityType.streaming:
            if not stream_channel:
                await interaction.response.send_message(
                    "⚠️ Vous devez fournir le nom de la chaîne pour Stream.", ephemeral=True
                )
                return
            stream_url = f"https://twitch.tv/{stream_channel}"
            activity = discord.Streaming(name=status, url=stream_url)
        else:
            activity = discord.Activity(type=activity_type_enum, name=status)

        self.is_temp_status = True
        await self.bot.change_presence(activity=activity)

        await interaction.response.send_message(
            f"✅ Statut changé pour `{status}` ({activity_type.name})"
            + (f" pendant {duration} secondes." if duration > 0 else " de façon permanente."),
            ephemeral=True
        )

        if duration > 0:
            if self.temp_status_task:
                self.temp_status_task.cancel()
            self.temp_status_task = self.bot.loop.create_task(self.reset_after(duration))
        else:
            if self.temp_status_task:
                self.temp_status_task.cancel()
                self.temp_status_task = None

    async def reset_after(self, duration):
        try:
            await asyncio.sleep(duration)
            self.is_temp_status = False
            self.change_status_loop.start()
        except asyncio.CancelledError:
            pass

    @app_commands.command(
        name="resetstatus",
        description="Réinitialise le statut et reprend celui d'origine"
    )
    async def reset_status(self, interaction: discord.Interaction):
        if interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message(
                "🚫 Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True
            )
            return

        self.is_temp_status = False
        if self.temp_status_task:
            self.temp_status_task.cancel()
            self.temp_status_task = None
        
        self.change_status_loop.restart()

        await interaction.response.send_message(
            "♻️ Le statut du bot a été réinitialisé.", ephemeral=True
        )

    @app_commands.command(
        name="updatestatus",
        description="Met à jour les informations du statut"
    )
    @app_commands.check(lambda interaction: interaction.user.id in OWNER_IDS)
    async def update_status(self, interaction: discord.Interaction):
        self.update_status_info()
        await interaction.response.send_message(
            "✅ Les informations du statut ont été mises à jour!", 
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Status(bot))
