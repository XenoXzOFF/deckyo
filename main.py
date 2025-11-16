import os
import threading
import logging
from dotenv import load_dotenv
import discord
from discord.ext import commands
from flask_app import create_app

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Charger les variables d'environnement
load_dotenv()

TOKEN = os.getenv('TOKEN')
OWNER_IDS = [int(id) for id in os.getenv('OWNER_IDS').split(',')]

# Configuration des Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Le préfixe est nécessaire pour `bot.process_commands`
bot = commands.Bot(command_prefix="-", intents=intents)

def run_flask_app(bot_instance):
    """Initialise et lance l'application Flask."""
    host = '0.0.0.0'
    port = int(os.getenv('PORT', 13966))
    flask_app = create_app(bot=bot_instance, dm_sender=send_dm_to_user)
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    flask_app.run(host=host, port=port, debug=False)

async def send_dm_to_user(user_id: int, message: str) -> bool:
    """Récupère un utilisateur par son ID et lui envoie un message privé."""
    try:
        user = await bot.fetch_user(user_id)
        if user:
            await user.send(message)
            logging.info(f"Message envoyé avec succès à l'utilisateur {user_id}.")
            return True
    except discord.errors.Forbidden:
        logging.warning(f"Impossible d'envoyer un MP à {user_id}. Il a probablement bloqué les MP.")
    except discord.errors.NotFound:
        logging.error(f"Impossible d'envoyer un MP : utilisateur {user_id} non trouvé.")
    except Exception as e:
        logging.error(f"Erreur inattendue lors de l'envoi du MP à {user_id}: {e}")
    return False

@bot.event
async def on_ready():
    """Événement déclenché lorsque le bot est prêt."""
    logging.info(f"Connecté en tant que {bot.user}")
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                logging.info(f"Module chargé : {filename}")
            except Exception as e:
                logging.error(f"Erreur lors du chargement de {filename} : {e}")
    try:
        synced = await bot.tree.sync()
        logging.info(f"{len(synced)} commandes slash synchronisées !")
    except Exception as e:
        logging.error(f"Erreur de synchronisation des commandes slash : {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    # Garder process_commands si vous avez des commandes textuelles
    await bot.process_commands(message)

if __name__ == "__main__":
    logging.info("🚀 Démarrage du site web...")
    flask_thread = threading.Thread(target=run_flask_app, args=(bot,))
    flask_thread.daemon = True
    flask_thread.start()
    
    logging.info("🤖 Démarrage du bot Discord...")
    bot.run(TOKEN)
