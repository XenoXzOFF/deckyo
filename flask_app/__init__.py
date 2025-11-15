import os
import json
import uuid
from flask import Flask, request, jsonify, render_template, abort

TRANSCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'transcripts')

def create_app():
    """Crée et configure une instance de l'application Flask."""
    app = Flask(__name__, template_folder='templates')

    # Une clé secrète est nécessaire pour la sécurité des sessions et autres.
    # Il est recommandé de la définir via une variable d'environnement.
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'une-cle-secrete-par-defaut-pour-le-dev')
    API_SECRET_KEY = os.getenv('API_SECRET_KEY')

    # Crée le dossier des transcripts s'il n'existe pas
    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

    @app.route('/')
    def index():
        return "<h1>Le bot est en ligne et le site web fonctionne !</h1>"

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

        return render_template('transcript.html', transcript=transcript_data)

    return app