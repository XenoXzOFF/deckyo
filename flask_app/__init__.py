import os
import json
import uuid
import functools
import asyncio
from flask import Flask, request, jsonify, render_template, abort, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import discord

TRANSCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'transcripts')
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Modèle utilisateur pour la base de données."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='staff') # Roles: 'owner', 'staff'

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
    app = Flask(__name__, template_folder='.')

    # Une clé secrète est nécessaire pour la sécurité des sessions et autres.
    # Il est recommandé de la définir via une variable d'environnement.
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'une-cle-secrete-par-defaut-pour-le-dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dashboard.db')
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
        # Crée l'utilisateur owner s'il n'existe pas
        if not User.query.filter_by(role='owner').first():
            owner_user = os.getenv('DASHBOARD_USERNAME', 'admin')
            owner_pass = os.getenv('DASHBOARD_PASSWORD')
            if owner_pass:
                new_owner = User(username=owner_user, role='owner')
                new_owner.set_password(owner_pass)
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
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

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

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Affiche la liste de tous les transcripts."""
        try:
            files = os.listdir(TRANSCRIPTS_DIR)
            # On ne garde que les fichiers .json et on les trie par date de modification
            transcript_files = [f for f in files if f.endswith('.json')]
            transcript_files.sort(
                key=lambda f: os.path.getmtime(os.path.join(TRANSCRIPTS_DIR, f)),
                reverse=True
            )
            
            transcripts_info = []
            for filename in transcript_files:
                try:
                    with open(os.path.join(TRANSCRIPTS_DIR, filename), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        transcripts_info.append({
                            'id': filename.replace('.json', ''),
                            'channel_name': data.get('channel_name', 'Inconnu'),
                            'date': data.get('messages', [{}])[0].get('timestamp', 'N/A')
                        })
                except (json.JSONDecodeError, IndexError):
                    # Ignore les fichiers corrompus ou vides
                    continue

        except OSError:
            transcripts_info = []
            flash("Impossible de lire le dossier des transcripts.", "danger")

        return render_template('dashboard.html', transcripts=transcripts_info)

    @app.route('/admin/staff', methods=['GET', 'POST'])
    @login_required
    @owner_required
    def manage_staff():
        """Page pour gérer les comptes staff."""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            if User.query.filter_by(username=username).first():
                flash("Ce nom d'utilisateur existe déjà.", "danger")
            else:
                new_staff = User(username=username, role='staff')
                new_staff.set_password(password)
                db.session.add(new_staff)
                db.session.commit()
                flash(f"Le compte staff '{username}' a été créé.", "success")
            return redirect(url_for('manage_staff'))

        staff_accounts = User.query.filter_by(role='staff').all()
        return render_template('staff_management.html', staff_accounts=staff_accounts)

    @app.route('/admin/staff/delete/<int:user_id>', methods=['POST'])
    @login_required
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

    @app.route('/api/transcripts', methods=['POST'])
    def handle_create_transcript():
        """Reçoit les données du transcript du bot et les sauvegarde."""
        # Sécurité : Vérifie la clé API
        if not API_SECRET_KEY or request.headers.get('X-API-Key') != API_SECRET_KEY:
            abort(401, description="Accès non autorisé.")

        data = request.json
        if not data:
            abort(400, description="Aucune donnée reçue.")

        # Génère un ID unique pour le transcript
        transcript_id = str(uuid.uuid4())
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

        return render_template('transcript.html', transcript=transcript_data, transcript_id=transcript_id)

    @app.route('/transcript/<transcript_id>/send_message', methods=['POST'])
    @login_required
    def send_ticket_message(transcript_id):
        """Envoie un message dans un ticket depuis le web."""
        if not bot:
            flash("Le bot n'est pas connecté, impossible d'envoyer le message.", "danger")
            return redirect(url_for('view_transcript', transcript_id=transcript_id))

        message_content = request.form.get('message')
        if not message_content:
            flash("Le message ne peut pas être vide.", "warning")
            return redirect(url_for('view_transcript', transcript_id=transcript_id))

        file_path = os.path.join(TRANSCRIPTS_DIR, f"{transcript_id}.json")
        if not os.path.exists(file_path):
            abort(404)

        with open(file_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
        
        channel_id = transcript_data.get('channel_id')
        if not channel_id:
            flash("ID du salon introuvable dans le transcript.", "danger")
            return redirect(url_for('view_transcript', transcript_id=transcript_id))

        async def send_message():
            channel = bot.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    description=message_content,
                    color=discord.Color.blurple(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_author(name=f"Réponse de {current_user.username} (Staff)", icon_url=bot.user.display_avatar.url)
                await channel.send(embed=embed)

        asyncio.run_coroutine_threadsafe(send_message(), bot.loop)
        flash("Message envoyé avec succès !", "success")
        return redirect(url_for('view_transcript', transcript_id=transcript_id))

    return app