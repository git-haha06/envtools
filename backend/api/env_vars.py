"""Environment variables & PATH API routes."""

from flask import Blueprint, jsonify, request

from backend.services import env_vars

bp = Blueprint("env_vars", __name__)


@bp.route("/api/env-vars")
def get_env_vars():
    return jsonify(env_vars.get_env_vars())


@bp.route("/api/system-env-vars")
def get_system_env_vars():
    return jsonify(env_vars.get_system_env_vars())


@bp.route("/api/env-vars", methods=["POST"])
def set_env_var():
    data = request.json
    env_vars.set_env_var(data["name"], data["value"])
    return jsonify({"success": True})


@bp.route("/api/env-vars/<name>", methods=["DELETE"])
def remove_env_var(name):
    env_vars.remove_env_var(name)
    return jsonify({"success": True})


@bp.route("/api/path")
def get_path():
    raw = env_vars.get_path_entries()
    expanded = env_vars.get_expanded_path_entries()
    return jsonify({"entries": raw, "expanded": expanded})


@bp.route("/api/system-path")
def get_system_path():
    raw = env_vars.get_system_path_entries()
    expanded = env_vars.get_expanded_system_path_entries()
    return jsonify({"entries": raw, "expanded": expanded})


@bp.route("/api/path", methods=["POST"])
def add_path():
    path = request.json.get("path", "")
    result = env_vars.add_to_path(path)
    return jsonify({"success": True, **result})


@bp.route("/api/path", methods=["DELETE"])
def remove_path():
    path = request.json.get("path", "")
    env_vars.remove_from_path(path)
    return jsonify({"success": True})
