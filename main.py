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
    flask_app = create_app(bot=bot_instance, dm_sender=send_dm_to_user)
    flask_app.run(host=host, port=port, debug=False)

async def send_dm_to_user(user_id: int, message: str):
    """
    Récupère un utilisateur par son ID et lui envoie un message privé.
    Cette fonction est asynchrone et doit être appelée depuis la boucle d'événements du bot.
    """
    try:
        # bot.fetch_user() est plus fiable que bot.get_user() car il fait un appel API
        # si l'utilisateur n'est pas dans le cache.
        user = await bot.fetch_user(user_id)
        if user:
            await user.send(message)
            print(f"✅ Message de réinitialisation envoyé à l'utilisateur {user_id}.")
            return True
    except discord.errors.Forbidden:
        print(f"⚠️ Erreur : Impossible d'envoyer un MP à l'utilisateur {user_id}. Il a peut-être bloqué les MP du serveur.")
    except Exception as e:
        print(f"⚠️ Une erreur inattendue est survenue lors de l'envoi du MP à {user_id}: {e}")
    return False

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
