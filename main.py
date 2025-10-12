import os
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks

# Charger les variables d'environnement
load_dotenv()

# Récupérer les variables d'environnement
TOKEN = os.getenv('TOKEN')
OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

PREFIX = os.getenv('PREFIX')

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Connecté comme {bot.user}")

    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"🔹 Module chargé : {filename}")
            except Exception as e:
                print(f"⚠️ Erreur lors du chargement de {filename} : {e}")

    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commandes slash synchronisées !")
    except Exception as e:
        print(f"⚠️ Erreur de synchronisation des commandes slash : {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.lower().startswith("salut"):
        await message.channel.send(f"Salut {message.author.mention} 👋")

    await bot.process_commands(message)

bot.run(TOKEN)
