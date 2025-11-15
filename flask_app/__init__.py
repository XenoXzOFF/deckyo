import os
import json
import uuid
import functools
import asyncio
from flask import Flask, request, jsonify, render_template, abort, redirect, url_for, flash, current_app, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import datetime
import requests
import discord

TRANSCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'transcripts')
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Modèle utilisateur pour la base de données."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='staff') # Roles: 'owner', 'staff'
    discord_id = db.Column(db.BigInteger, unique=True, nullable=True)
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiration = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def owner_required(f):
    """Décorateur pour restreindre l'accès aux 'owners'."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'owner':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def create_app(bot=None):
    """Crée et configure une instance de l'application Flask."""
    app = Flask(__name__, template_folder='.', static_folder='../img', static_url_path='/img')

    # Une clé secrète est nécessaire pour la sécurité des sessions et autres.
    # Il est recommandé de la définir via une variable d'environnement.
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'une-cle-secrete-par-defaut-pour-le-dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dashboard.db')
    # Ajout pour passer le bot aux routes
    app.config['BOT_INSTANCE'] = bot
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    API_SECRET_KEY = os.getenv('API_SECRET_KEY')

    db.init_app(app)

    # --- Configuration de Flask-Login ---
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login' # Redirige vers la page de connexion si non authentifié
    login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
    login_manager.login_message_category = "info"

    with app.app_context():
        db.create_all()
        # Gère le compte propriétaire au démarrage pour garantir la synchronisation
        owner_username = os.getenv('DASHBOARD_USERNAME', 'admin')
        owner_password = os.getenv('DASHBOARD_PASSWORD')
        owner = User.query.filter_by(role='owner').first()

        if owner:
            # Si le propriétaire existe, on met à jour son mot de passe si défini
            if owner_password:
                owner.set_password(owner_password)
                db.session.commit()
                print("🔑 Le mot de passe du compte propriétaire a été synchronisé.")
        elif owner_password:
            # Si le propriétaire n'existe pas et qu'un mot de passe est fourni, on le crée
            owner_discord_id_str = os.getenv('OWNER_IDS', '').split(',')[0]
            discord_id_to_set = None
            if owner_discord_id_str and owner_discord_id_str.isdigit():
                discord_id_to_set = int(owner_discord_id_str)
            
            new_owner = User(username=owner_username, role='owner', discord_id=discord_id_to_set)
            new_owner.set_password(owner_password)
            db.session.add(new_owner)
            db.session.commit()
            print("🎉 Compte propriétaire créé avec succès !")

    # Crée le dossier des transcripts s'il n'existe pas
    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/')
    def index():
        """Page d'accueil publique affichant les statistiques des tickets."""
        num_active = 0
        num_closed = 0
        discord_members_online = "N/A"
        discord_invite_url = "#"
        discord_server_id = "1333136013203214499" # Votre ID de serveur Discord

        try:
            # Utilise l'API widget de Discord pour obtenir les infos
            response = requests.get(f"https://discord.com/api/v9/guilds/{discord_server_id}/widget.json")
            response.raise_for_status() # Lève une exception pour les codes d'erreur HTTP
            widget_data = response.json()
            discord_members_online = widget_data.get('presence_count', 'N/A')
            discord_invite_url = widget_data.get('instant_invite', '#')
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des informations du widget Discord: {e}")
            # Les valeurs par défaut seront utilisées

        try:
            files = [f for f in os.listdir(TRANSCRIPTS_DIR) if f.endswith('.json')]
            bot = current_app.config.get('BOT_INSTANCE')

            for filename in files:
                is_active = False
                if bot:
                    try:
                        with open(os.path.join(TRANSCRIPTS_DIR, filename), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        channel_id = data.get('channel_id')
                        if channel_id and bot.get_channel(channel_id):
                            is_active = True
                    except (IOError, json.JSONDecodeError):
                        continue # Ignore les fichiers corrompus
                
                if is_active:
                    num_active += 1
                else:
                    num_closed += 1
        except OSError:
            # Le dossier n'existe pas encore, on ignore
            pass
        return render_template('public_index.html', 
                               active_tickets=num_active, 
                               closed_tickets=num_closed,
                               discord_members_online=discord_members_online,
                               discord_invite_url=discord_invite_url,
                               discord_server_id=discord_server_id)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()

            if not user or not user.check_password(password):
                flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")
                return render_template('login.html')
            
            login_user(user)
            flash("Connexion réussie !", "success")
            return redirect(url_for('dashboard'))

        return render_template('login.html')

    @app.route('/request_reset', methods=['GET', 'POST'])
    def request_password_reset():
        """Page pour demander une réinitialisation de mot de passe."""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            user = User.query.filter_by(username=username).first()

            if user and user.discord_id:
                code = f"{secrets.randbelow(10**8):08d}" # Génère un code à 8 chiffres
                user.reset_token = code
                user.reset_token_expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
                db.session.commit()
                bot = app.config.get('BOT_INSTANCE')

                async def send_reset_code():
                    try:
                        formatted_code = f"{code[:4]}-{code[4:]}"
                        discord_user = await bot.fetch_user(user.discord_id) # Tente de récupérer l'utilisateur
                        if discord_user:
                            embed = discord.Embed(
                                title="🔑 Réinitialisation de mot de passe",
                                description=f"Bonjour {user.username},\n\nVoici votre code à usage unique pour réinitialiser votre mot de passe. Ce code expirera dans 5 minutes.\n\n**Code :**\n```{formatted_code}```",
                                color=discord.Color.orange(),
                            )
                            await discord_user.send(embed=embed)
                    except Exception as e:
                        print(f"Erreur lors de l'envoi du code de réinitialisation à {user.username}: {e}")

                if bot:
                    asyncio.run_coroutine_threadsafe(send_reset_code(), bot.loop)
                    flash("Si un compte correspondant existe, un code a été envoyé par MP sur Discord. Veuillez le saisir ci-dessous.", "info")
                    return redirect(url_for('verify_token'))
                else:
                    flash("Le bot n'est pas connecté, impossible d'envoyer le code.", "danger")
            else:
                flash("Si un compte avec cet nom d'utilisateur et un ID Discord associé existe, un code de réinitialisation a été envoyé en message privé.", "info")
            
            return redirect(url_for('login'))

        return render_template('request_reset.html')

    @app.route('/verify_token', methods=['GET', 'POST'])
    def verify_token():
        """Page pour vérifier le code de réinitialisation."""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            token = request.form.get('token')
            user = User.query.filter_by(reset_token=token).first()

            if not user or user.reset_token_expiration < datetime.datetime.utcnow():
                flash("Le code est invalide ou a expiré.", "danger")
                return redirect(url_for('verify_token'))
            
            # Le token est valide, on redirige vers la page de définition du mot de passe
            session['reset_token'] = token
            return redirect(url_for('reset_password', token=token))

        return render_template('verify_token.html')

    @app.route('/reset_password', methods=['GET', 'POST'])
    def reset_password():
        """Page pour définir le nouveau mot de passe."""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        token = session.get('reset_token')
        if not token:
            flash("Aucune demande de réinitialisation active. Veuillez recommencer.", "warning")
            return redirect(url_for('request_password_reset'))

        user = User.query.filter_by(reset_token=token).first()
        if not user or user.reset_token_expiration < datetime.datetime.utcnow():
            flash("Votre session de réinitialisation est invalide ou a expiré. Veuillez recommencer.", "danger")
            return redirect(url_for('request_password_reset'))

        if request.method == 'POST':
            new_password = request.form.get('password')
            user.set_password(new_password)
            user.reset_token = None
            user.reset_token_expiration = None
            session.pop('reset_token', None) # Nettoie la session
            db.session.commit()
            flash("Votre mot de passe a été réinitialisé avec succès ! Vous pouvez maintenant vous connecter.", "success")
            return redirect(url_for('login'))
        
        return render_template('reset_password.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Affiche la liste de tous les transcripts."""
        active_tickets = []
        closed_tickets = []
        try:
            files = os.listdir(TRANSCRIPTS_DIR)
            # On ne garde que les fichiers .json et on les trie par date de modification
            transcript_files = [f for f in files if f.endswith('.json')]
            transcript_files.sort(
                key=lambda f: os.path.getmtime(os.path.join(TRANSCRIPTS_DIR, f)),
                reverse=True
            )
            
            for filename in transcript_files:
                try:
                    with open(os.path.join(TRANSCRIPTS_DIR, filename), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        ticket_info = {
                            'id': filename.replace('.json', ''),
                            'channel_name': data.get('channel_name', 'Inconnu'),
                            'date': data.get('messages', [{}])[0].get('timestamp', 'N/A'),
                            'creator_id': data.get('creator_id')
                        }

                        # Vérifie si le ticket est actif
                        is_active = False
                        if current_app.config.get('BOT_INSTANCE'):
                            channel_id = data.get('channel_id')
                            if channel_id and current_app.config.get('BOT_INSTANCE').get_channel(channel_id):
                                is_active = True
                        
                        if is_active:
                            active_tickets.append(ticket_info)
                        else:
                            closed_tickets.append(ticket_info)

                except (json.JSONDecodeError, IndexError):
                    # Ignore les fichiers corrompus ou vides
                    continue

        except OSError:
            flash("Impossible de lire le dossier des transcripts.", "danger")

        return render_template('dashboard.html', active_tickets=active_tickets, closed_tickets=closed_tickets)

    @app.route('/admin/staff', methods=['GET', 'POST'])
    @owner_required
    def manage_staff():
        """Page pour gérer les comptes staff."""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            discord_id_str = request.form.get('discord_id')

            if User.query.filter_by(username=username).first():
                flash("Ce nom d'utilisateur existe déjà.", "danger")
            elif not discord_id_str or not discord_id_str.isdigit():
                flash("L'ID Discord est invalide.", "danger")
            else:
                discord_id = int(discord_id_str)
                if User.query.filter_by(discord_id=discord_id).first():
                    flash("Cet ID Discord est déjà associé à un autre compte.", "danger")
                    return redirect(url_for('manage_staff'))

                new_staff = User(username=username, role='staff', discord_id=discord_id)
                new_staff.set_password(password)
                db.session.add(new_staff)
                db.session.commit()
                flash(f"Le compte staff '{username}' a été créé.", "success")
            return redirect(url_for('manage_staff'))

        staff_accounts = User.query.filter_by(role='staff').all()
        return render_template('staff_management.html', staff_accounts=staff_accounts)

    @app.route('/admin/staff/delete/<int:user_id>', methods=['POST'])
    @owner_required
    def delete_staff(user_id):
        """Supprime un compte staff."""
        user_to_delete = User.query.get_or_404(user_id)
        if user_to_delete.role == 'staff':
            db.session.delete(user_to_delete)
            db.session.commit()
            flash(f"Le compte '{user_to_delete.username}' a été supprimé.", "success")
        else:
            flash("Vous ne pouvez pas supprimer un compte propriétaire.", "danger")
        return redirect(url_for('manage_staff'))

    @app.route('/admin/staff/add_id/<int:user_id>', methods=['POST'])
    @owner_required
    def add_discord_id(user_id):
        """Ajoute un ID Discord à un compte staff existant."""
        user_to_update = User.query.get_or_404(user_id)
        discord_id_str = request.form.get('discord_id')

        if user_to_update.role == 'staff' and discord_id_str and discord_id_str.isdigit():
            discord_id = int(discord_id_str)
            if User.query.filter_by(discord_id=discord_id).first():
                flash("Cet ID Discord est déjà utilisé par un autre compte.", "danger")
            else:
                user_to_update.discord_id = discord_id
                db.session.commit()
                flash(f"L'ID Discord pour '{user_to_update.username}' a été mis à jour.", "success")
        else:
            flash("ID Discord invalide ou utilisateur incorrect.", "danger")
        
        return redirect(url_for('manage_staff'))

    @app.route('/api/transcripts/init', methods=['POST'])
    def handle_init_transcript():
        """Crée un fichier de transcript vide et retourne son ID."""
        if not API_SECRET_KEY or request.headers.get('X-API-Key') != API_SECRET_KEY:
            abort(401, description="Accès non autorisé.")

        data = request.json
        if not data:
            abort(400, description="Aucune donnée initiale reçue.")

        transcript_id = str(uuid.uuid4())
        file_path = os.path.join(TRANSCRIPTS_DIR, f"{transcript_id}.json")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except IOError as e:
            abort(500, description=f"Erreur lors de la création du fichier: {e}")

        return jsonify({"status": "success", "transcript_id": transcript_id}), 201

    @app.route('/api/transcripts', methods=['POST'])
    def handle_create_transcript():
        """Reçoit les données du transcript du bot et les sauvegarde (crée ou met à jour)."""
        # Sécurité : Vérifie la clé API
        if not API_SECRET_KEY or request.headers.get('X-API-Key') != API_SECRET_KEY:
            abort(401, description="Accès non autorisé.")

        data = request.json
        if not data:
            abort(400, description="Aucune donnée reçue.")

        # Vérifie si un ID est fourni pour une mise à jour
        transcript_id = data.get('transcript_id')
        if not transcript_id:
            # Si pas d'ID, on génère un nouveau (ne devrait plus arriver avec la nouvelle logique)
            transcript_id = str(uuid.uuid4())
        
        # Sécurité : Valider le nom du fichier pour éviter les attaques de type "Path Traversal"
        if not transcript_id.replace('-', '').isalnum():
            abort(400, "ID de transcript invalide.")

        file_path = os.path.join(TRANSCRIPTS_DIR, f"{transcript_id}.json")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except IOError as e:
            abort(500, description=f"Erreur lors de la sauvegarde du fichier: {e}")
        
        return jsonify({"status": "success", "transcript_id": transcript_id}), 201

    @app.route('/transcript/<transcript_id>')
    @login_required
    def view_transcript(transcript_id):
        """Affiche un transcript sauvegardé."""
        file_path = os.path.join(TRANSCRIPTS_DIR, f"{transcript_id}.json")

        if not os.path.exists(file_path):
            abort(404, description="Transcript non trouvé.")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            abort(500, description=f"Erreur lors de la lecture du transcript: {e}")

        # Vérifie si le salon du ticket est toujours actif
        is_channel_active = False
        bot = current_app.config.get('BOT_INSTANCE')
        if bot:
            channel_id = transcript_data.get('channel_id')
            # bot.get_channel() est une recherche rapide dans le cache
            if channel_id and bot.get_channel(channel_id):
                is_channel_active = True

        return render_template('transcript.html', transcript=transcript_data, transcript_id=transcript_id, is_channel_active=is_channel_active)

    @app.cli.command("reset-owner-password")
    def reset_owner_password():
        """Réinitialise le mot de passe de l'utilisateur propriétaire."""
        owner = User.query.filter_by(role='owner').first()
        if not owner:
            print("❌ Aucun utilisateur propriétaire trouvé. Créez-en un d'abord.")
            return

        new_password = os.getenv('DASHBOARD_PASSWORD')
        if not new_password:
            print("❌ La variable d'environnement DASHBOARD_PASSWORD n'est pas définie.")
            print("Veuillez la définir dans votre fichier .env avant d'exécuter cette commande.")
            return

        owner.set_password(new_password)
        db.session.commit()
        print(f"✅ Le mot de passe pour l'utilisateur '{owner.username}' a été réinitialisé avec succès !")

    return app
