"""Package install/uninstall API routes."""

from flask import Blueprint, jsonify, request

from backend.services import installer

bp = Blueprint("packages", __name__)


@bp.route("/api/packages")
def get_packages():
    return jsonify(installer.load_manifests())


@bp.route("/api/install", methods=["POST"])
def install():
    data = request.json
    result = installer.install_package(
        data["package_name"],
        data["version"],
        data.get("use_mirror", False),
        data.get("install_dir"),
    )
    return jsonify(result)


@bp.route("/api/uninstall", methods=["POST"])
def uninstall():
    installer.uninstall_package(request.json["install_path"])
    return jsonify({"success": True})
