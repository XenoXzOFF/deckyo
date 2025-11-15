import os
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks

from webapp import create_app
import threading
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
app = create_app()

def run_flask_app():
    # Le port est extrait de l'URL pour éviter les conflits
    port = int(os.getenv('WEBAPP_URL').split(':')[-1])
    # Utilise l'IP 0.0.0.0 pour être accessible depuis l'extérieur
    app.run(host='0.0.0.0', port=port, debug=False)

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
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.daemon = True
    flask_thread.start()
    print("🚀 Site web démarré...")
    bot.run(TOKEN)
