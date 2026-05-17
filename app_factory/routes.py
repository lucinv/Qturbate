"""Blueprints pour l'application Flask."""
from flask import Blueprint, render_template, request, jsonify
from services.chaturbate import fetch_rooms
from services.stream_resolver import get_direct_stream_url

main_bp = Blueprint("main", __name__)


@main_bp.route('/')
def index():
    gender = request.args.get("gender")
    tag = request.args.get("tag")
    videos = fetch_rooms(gender=gender, tag=tag)
    return render_template('video_gallery.html', videos=videos)


@main_bp.route('/get-download-url', methods=['POST'])
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
