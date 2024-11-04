from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import asyncio
from yt_dlp import YoutubeDL
from services.chaturbate import fetch_rooms
from models import db


app = Flask(__name__)
CORS(app)  # Permet les requêtes CORS
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///settings.db'
db.init_app(app)

# Crée les tables
with app.app_context():
    db.create_all()


@app.route('/')
def index():
    videos = asyncio.run(fetch_rooms())
    
    return render_template('video_gallery.html', videos=videos)

@app.route('/get-download-url', methods=['POST'])
def get_download_url():
    data = request.json
    stream_url = data.get("stream_url")

    # Utilisation de yt-dlp pour obtenir le lien de téléchargement direct
    try:
        ydl_opts = {
            'format': '1',  # Choisir la meilleure qualité disponible
        }
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(stream_url, download=False)
            download_url = info_dict.get("url", None)  # Récupérer l'URL directe
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return download_url


if __name__ == '__main__':
    app.run(debug=True)

