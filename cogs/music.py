import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import yt_dlp as youtube_dl
from collections import deque

# Configuration pour youtube_dl
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class MusicQueue:
    def __init__(self):
        self.queue = deque()
        self.current = None
        self.loop = False
        self.volume = 0.5

    def add(self, song):
        self.queue.append(song)

    def next(self):
        if self.loop and self.current:
            return self.current
        if self.queue:
            self.current = self.queue.popleft()
            return self.current
        return None

    def clear(self):
        self.queue.clear()
        self.current = None

    def is_empty(self):
        return len(self.queue) == 0

# Dictionnaire pour stocker les queues par serveur
music_queues = {}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_queue(self, guild_id):
        if guild_id not in music_queues:
            music_queues[guild_id] = MusicQueue()
        return music_queues[guild_id]

    async def play_next(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        
        if queue.is_empty() and not queue.loop:
            await ctx.send("🎵 La file d'attente est terminée!")
            return

        song = queue.next()
        if song:
            player = await YTDLSource.from_url(song, loop=self.bot.loop, stream=True)
            player.volume = queue.volume
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
            
            embed = discord.Embed(
                title="🎵 Lecture en cours",
                description=f"**{player.title}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)

    @app_commands.command(name="play", description="Joue une musique depuis YouTube")
    async def play(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        
        if not interaction.user.voice:
            await interaction.followup.send("❌ Vous devez être dans un salon vocal!")
            return

        channel = interaction.user.voice.channel
        
        if not interaction.guild.voice_client:
            await channel.connect()
        elif interaction.guild.voice_client.channel != channel:
            await interaction.guild.voice_client.move_to(channel)

        queue = self.get_queue(interaction.guild.id)
        
        try:
            # Ajouter à la queue
            queue.add(url)
            
            embed = discord.Embed(
                title="✅ Ajouté à la file d'attente",
                description=f"Position: {len(queue.queue)}",
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed)
            
            # Si rien ne joue, commencer la lecture
            if not interaction.guild.voice_client.is_playing():
                await self.play_next(interaction)
                
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur: {str(e)}")

    @app_commands.command(name="pause", description="Met en pause la musique")
    async def pause(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.pause()
            await interaction.response.send_message("⏸️ Musique mise en pause")
        else:
            await interaction.response.send_message("❌ Aucune musique en cours de lecture")

    @app_commands.command(name="resume", description="Reprend la musique")
    async def resume(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
            interaction.guild.voice_client.resume()
            await interaction.response.send_message("▶️ Musique reprise")
        else:
            await interaction.response.send_message("❌ La musique n'est pas en pause")

    @app_commands.command(name="skip", description="Passe à la musique suivante")
    async def skip(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()
            await interaction.response.send_message("⏭️ Musique passée")
        else:
            await interaction.response.send_message("❌ Aucune musique en cours de lecture")

    @app_commands.command(name="stop", description="Arrête la musique et vide la file d'attente")
    async def stop(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)
        queue.clear()
        
        if interaction.guild.voice_client:
            interaction.guild.voice_client.stop()
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("⏹️ Musique arrêtée et déconnecté")
        else:
            await interaction.response.send_message("❌ Le bot n'est pas connecté")

    @app_commands.command(name="queue", description="Affiche la file d'attente")
    async def queue_command(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)
        
        if queue.is_empty() and not queue.current:
            await interaction.response.send_message("❌ La file d'attente est vide")
            return

        embed = discord.Embed(
            title="🎵 File d'attente musicale",
            color=discord.Color.purple()
        )
        
        if queue.current:
            embed.add_field(name="En cours", value=f"🎵 {queue.current}", inline=False)
        
        if not queue.is_empty():
            queue_list = "\n".join([f"{i+1}. {song}" for i, song in enumerate(list(queue.queue)[:10])])
            embed.add_field(name="Prochaines musiques", value=queue_list, inline=False)
            
            if len(queue.queue) > 10:
                embed.set_footer(text=f"Et {len(queue.queue) - 10} musiques de plus...")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="loop", description="Active/désactive la répétition")
    async def loop(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)
        queue.loop = not queue.loop
        
        status = "activée 🔁" if queue.loop else "désactivée"
        await interaction.response.send_message(f"Répétition {status}")

    @app_commands.command(name="volume", description="Ajuste le volume (0-100)")
    async def volume(self, interaction: discord.Interaction, niveau: int):
        if not 0 <= niveau <= 100:
            await interaction.response.send_message("❌ Le volume doit être entre 0 et 100")
            return

        queue = self.get_queue(interaction.guild.id)
        queue.volume = niveau / 100

        if interaction.guild.voice_client and interaction.guild.voice_client.source:
            interaction.guild.voice_client.source.volume = queue.volume

        await interaction.response.send_message(f"🔊 Volume réglé à {niveau}%")

async def setup(bot):
    await bot.add_cog(Music(bot))