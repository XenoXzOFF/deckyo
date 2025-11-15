import os
import threading
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from flask_app import create_app

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer les variables d'environnement
TOKEN = os.getenv('TOKEN')
OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

PREFIX = os.getenv('PREFIX')

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

def run_flask_app(bot_instance):
    """Initialise et lance l'application Flask."""
    # Utiliser '0.0.0.0' est crucial pour que l'application soit accessible
    # depuis l'extérieur de son conteneur.
    host = '0.0.0.0'
    # Le port est souvent fourni par l'hébergeur via une variable d'environnement.
    port = int(os.getenv('PORT', 13966))
    flask_app = create_app(bot=bot_instance)
    flask_app.run(host=host, port=port, debug=False)

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

if __name__ == "__main__":
    # Lance le site web dans un thread séparé
    print("🚀 Démarrage du site web...")
    flask_thread = threading.Thread(target=run_flask_app, args=(bot,))
    flask_thread.daemon = True
    flask_thread.start()
    
    print("🤖 Démarrage du bot Discord...")
    bot.run(TOKEN)
