from flask import Flask, render_template, request, jsonify
import asyncio
from yt_dlp import YoutubeDL
from services.chaturbate import fetch_rooms
from storage.models import db


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///settings.db'
db.init_app(app)

# Crée les tables
with app.app_context():
    db.create_all()


@app.route('/')
def index():

    # DEBUG
    user_agent = request.headers.get('User-Agent')
    print(f"User-Agent: {user_agent}")
    # /DEBUG

    gender = request.args.get("gender")  # Récupère ?gender=f ou ?gender=m
    tag = request.args.get("tag")  # Récupère ?tag=xxx
    print(f"tag = {tag}, gender = {gender}")
    videos = asyncio.run(fetch_rooms(gender=gender, tag=tag))
    return render_template('video_gallery.html', videos=videos)

@app.route('/get-download-url', methods=['POST'])
def get_download_url():
    data = request.json
    stream_url = data.get("stream_url")

    try:
        ydl_opts = {
            'format': '1',  # Choisir la meilleure qualité disponible
        }
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(stream_url, download=False)
            download_url = info_dict.get("url", None)  # Récupérer l'URL directe
            print(f"Download URL : {download_url}")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return download_url


if __name__ == '__main__':

    app.run(host='127.0.0.1', port=5001, debug=True)
