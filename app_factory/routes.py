"""Blueprints pour l'application Flask."""
import logging

from flask import Blueprint, render_template, request, jsonify

from services.chaturbate import fetch_rooms
from services.stream_resolver import get_direct_stream_url

logger = logging.getLogger(__name__)

main_bp = Blueprint("main", __name__)


@main_bp.route('/')
def index():
    gender = request.args.get("gender")
    tag = request.args.get("tag")
    logger.debug("Index request: gender=%s, tag=%s", gender, tag)
    videos = fetch_rooms(gender=gender, tag=tag)
    return render_template('video_gallery.html', videos=videos)


@main_bp.route('/get-download-url', methods=['POST'])
def get_download_url():
    data = request.json
    stream_url = data.get("stream_url")
    logger.info("Download URL requested for: %s", stream_url)

    try:
        download_url = get_direct_stream_url(stream_url)
        if download_url:
            return download_url
        logger.warning("No direct URL found for: %s", stream_url)
        return jsonify({"error": "No direct URL found"}), 404
    except Exception as e:
        logger.exception("Error resolving stream URL: %s", stream_url)
        return jsonify({"error": str(e)}), 500
