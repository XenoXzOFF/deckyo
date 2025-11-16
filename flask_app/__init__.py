import os
import asyncio
from flask import Flask, render_template, request, redirect, url_for, flash, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()

def create_app(bot, dm_sender):
    """Crée et configure l'application Flask."""
    # Chemin absolu pour le dossier des templates. C'est la solution infaillible.
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(base_dir, 'templates')
    app = Flask(__name__, template_folder=template_dir)
    
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'une-cle-secrete-a-changer-absolument')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    app.config['BOT'] = bot
    app.config['DM_SENDER'] = dm_sender

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'
    login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."

    from .models import User
    from .forms import RequestResetForm, RegistrationForm, LoginForm

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/')
    def home():
        return redirect(url_for('dashboard'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html', title='Tableau de bord')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        form = RegistrationForm()
        if form.validate_on_submit():
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user = User(username=form.username.data, discord_id=form.discord_id.data, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            flash('Votre compte a été créé ! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html', title='Inscription', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Échec de la connexion. Vérifiez nom d\'utilisateur et mot de passe.', 'danger')
        return render_template('login.html', title='Connexion', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/request_reset', methods=['GET', 'POST'])
    def request_reset():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        form = RequestResetForm()
        if form.validate_on_submit():
            user = User.query.filter_by(discord_id=form.discord_id.data).first()
            if user:
                bot_instance = current_app.config['BOT']
                dm_sender_func = current_app.config['DM_SENDER']
                
                import random, string
                token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                
                message_content = (
                    f"Bonjour {user.username},\n\n"
                    f"Voici votre code pour réinitialiser votre mot de passe : **{token}**\n\n"
                    "Si vous n'avez pas demandé cette réinitialisation, ignorez ce message."
                )

                asyncio.run_coroutine_threadsafe(
                    dm_sender_func(int(user.discord_id), message_content),
                    bot_instance.loop
                )

                flash('Un code de réinitialisation vous a été envoyé par MP sur Discord.', 'info')
                return redirect(url_for('login'))
            else:
                flash('Aucun compte n\'est associé à cet ID Discord.', 'danger')
        return render_template('request_reset.html', title='Réinitialiser le mot de passe', form=form)

    with app.app_context():
        db_file = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if not os.path.exists(db_file):
            db.create_all()
            logging.info(f"Base de données '{db_file}' créée avec les tables.")

    return app
