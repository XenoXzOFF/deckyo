import os
from flask import Flask

def create_app():
    """Crée et configure une instance de l'application Flask."""
    app = Flask(__name__)

    # Une clé secrète est nécessaire pour la sécurité des sessions et autres.
    # Il est recommandé de la définir via une variable d'environnement.
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'une-cle-secrete-par-defaut-pour-le-dev')

    @app.route('/')
    def index():
        return "<h1>Le bot est en ligne et le site web fonctionne !</h1>"

    # Ici, vous pourrez ajouter vos "blueprints" pour organiser vos routes.
    return app