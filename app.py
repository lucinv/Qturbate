from flask import Flask, render_template, request, jsonify
from services.chaturbate import fetch_rooms
from storage.models import db
from services.stream_resolver import get_direct_stream_url


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///settings.db'
db.init_app(app)

with app.app_context():
    db.create_all()


@app.route('/')
def index():
    gender = request.args.get("gender")
    tag = request.args.get("tag")
    videos = fetch_rooms(gender=gender, tag=tag)
    return render_template('video_gallery.html', videos=videos)


@app.route('/get-download-url', methods=['POST'])
def get_download_url():
    data = request.json
    stream_url = data.get("stream_url")

    try:
        download_url = get_direct_stream_url(stream_url)
        if download_url:
            return download_url
        return jsonify({"error": "No direct URL found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)
