"""Config & mirror API routes."""

from flask import Blueprint, jsonify, request

from backend.core import config
from backend.services import mirror

bp = Blueprint("config", __name__)


@bp.route("/api/config", methods=["GET"])
def get_config():
    return jsonify(config.get_app_config())


@bp.route("/api/config", methods=["POST"])
def save_config():
    config.save_app_config(request.json)
    return jsonify({"success": True})


@bp.route("/api/mirrors")
def get_mirrors():
    return jsonify(mirror.get_mirror_configs())


@bp.route("/api/mirrors/<name>", methods=["POST"])
def set_mirror(name):
    url = request.json.get("url", "")
    result = mirror.set_mirror_source(name, url)
    return jsonify({"result": result})
