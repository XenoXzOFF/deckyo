import os
import asyncio
from flask import Flask, render_template, request, redirect, url_for, flash, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialisation des extensions (sans les lier à une app pour l'instant)
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(bot, dm_sender):
    """Crée et configure l'application Flask."""
    app = Flask(__name__)
    
    # Configuration de l'application
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'une-cle-secrete-par-defaut-a-changer')
    # Configurez le chemin de votre base de données
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Stocker l'instance du bot dans la configuration de l'application pour y accéder plus tard
    app.config['BOT'] = bot
    # Stocker la fonction d'envoi de DM pour éviter les imports circulaires
    app.config['DM_SENDER'] = dm_sender

    # Initialiser les extensions avec l'application
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login' # Redirige les utilisateurs non connectés vers la page de login

    # Importation des modèles et formulaires
    from .models import User
    from .forms import RequestResetForm

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Définition des Routes ---

    @app.route('/')
    def home():
        return "<h1>Le site web est en ligne !</h1>"

    @app.route('/request_reset', methods=['GET', 'POST'])
    def request_reset():
        form = RequestResetForm()
        if form.validate_on_submit():
            user = User.query.filter_by(discord_id=form.discord_id.data).first()
            if user:
                # Récupérer l'instance du bot depuis la config de l'app
                bot_instance = current_app.config['BOT']
                dm_sender_func = current_app.config['DM_SENDER']
                
                # Générer un token/code (pour cet exemple, un code simple)
                import random, string
                token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                # Vous devriez sauvegarder ce token dans la base de données avec une date d'expiration
                
                message_content = (
                    f"Bonjour {user.username},\n\n"
                    f"Pour réinitialiser votre mot de passe, utilisez le code suivant : **{token}**\n\n"
                    "Si vous n'avez pas demandé cette réinitialisation, ignorez ce message."
                )

                # C'est ici que Flask demande au bot d'envoyer le MP
                asyncio.run_coroutine_threadsafe(
                    dm_sender_func(int(user.discord_id), message_content),
                    bot_instance.loop
                )

                flash('Un code de réinitialisation vous a été envoyé par MP sur Discord.', 'info')
                return redirect(url_for('home')) # Rediriger vers une page de vérification du token
            else:
                flash('Aucun compte n\'est associé à cet ID Discord.', 'danger')
                
        return render_template('request_reset.html', title='Réinitialiser le mot de passe', form=form)

    return app