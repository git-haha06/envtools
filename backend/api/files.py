"""Config file discovery & editing API routes."""

from flask import Blueprint, jsonify, request

from backend.services import config_files

bp = Blueprint("files", __name__)


@bp.route("/api/config-files")
def discover_config_files():
    env_id = request.args.get("env_id", "")
    env_path = request.args.get("env_path", "") or None
    files = config_files.discover_config_files(env_id, env_path)
    return jsonify(files)


@bp.route("/api/config-files/read")
def read_config_file():
    path = request.args.get("path", "")
    try:
        content = config_files.read_config_file(path)
        return jsonify({"content": content})
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404


@bp.route("/api/config-files/save", methods=["POST"])
def save_config_file():
    data = request.json
    try:
        config_files.save_config_file(data["path"], data["content"])
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/custom-config-files", methods=["POST"])
def add_custom_config_file():
    data = request.json
    result = config_files.add_custom_config_file(data["env_id"], data["file_path"])
    return jsonify(result)


@bp.route("/api/custom-config-files", methods=["DELETE"])
def remove_custom_config_file():
    data = request.json
    config_files.remove_custom_config_file(data["env_id"], data["file_path"])
    return jsonify({"success": True})
