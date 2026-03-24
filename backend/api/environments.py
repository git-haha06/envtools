"""Environment scanning, manual envs, status, definitions, commands API routes."""

import json
import traceback

from flask import Blueprint, jsonify, request

from backend.core.database import get_db, _seed_env_definitions
from backend.services import scanner, manual_env, service_cmd, status_check

bp = Blueprint("environments", __name__)


# ─── Scan ────────────────────────────────────────────────

@bp.route("/api/scan")
def scan():
    return jsonify(scanner.scan_all_environments())


@bp.route("/api/system-info")
def system_info():
    return jsonify(scanner.get_system_info())


# ─── Manual Envs ─────────────────────────────────────────

@bp.route("/api/manual-envs")
def get_manual_envs():
    return jsonify(manual_env.get_manual_envs())


@bp.route("/api/manual-envs", methods=["POST"])
def add_manual_env():
    try:
        env = manual_env.add_manual_env(request.json)
        return jsonify(env)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/api/manual-envs/<path:env_id>", methods=["DELETE"])
def remove_manual_env(env_id):
    try:
        manual_env.remove_manual_env(env_id)
        return jsonify({"success": True})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@bp.route("/api/manual-envs/<path:env_id>/refresh", methods=["POST"])
def refresh_manual_env(env_id):
    version = manual_env.refresh_manual_env_version(env_id)
    return jsonify({"version": version})


# ─── Service Commands ────────────────────────────────────

@bp.route("/api/commands/<env_id>")
def get_commands(env_id):
    return jsonify(service_cmd.get_commands(env_id))


@bp.route("/api/run-command", methods=["POST"])
def run_command():
    data = request.json
    result = service_cmd.run_command(
        cmd=data["cmd"],
        cwd=data.get("cwd"),
        bin_path=data.get("bin_path"),
        env_path=data.get("env_path"),
        background=data.get("background", False),
    )
    return jsonify(result)


# ─── Status Check ────────────────────────────────────────

@bp.route("/api/env-status")
def env_status_all():
    env_ids = request.args.get("ids", "")
    id_list = [x.strip() for x in env_ids.split(",") if x.strip()] if env_ids else None
    return jsonify(status_check.check_all_status(id_list))


@bp.route("/api/env-status/<env_id>")
def env_status(env_id):
    env_path = request.args.get("env_path") or None
    return jsonify(status_check.check_env_status(env_id, env_path))


# ─── Environment Definitions ────────────────────────────

@bp.route("/api/env-defs")
def get_env_defs():
    with get_db() as db:
        rows = db.execute("SELECT * FROM env_definitions ORDER BY rowid").fetchall()
    result = []
    for r in rows:
        result.append({
            "env_id": r["env_id"],
            "display_name": r["display_name"],
            "category": r["category"],
            "scan_commands": json.loads(r["scan_commands"]),
            "version_flag": r["version_flag"],
            "config_patterns": json.loads(r["config_patterns"]),
            "service_commands": json.loads(r["service_commands"]),
            "status_check": json.loads(r["status_check"]),
        })
    return jsonify(result)


@bp.route("/api/env-defs", methods=["POST"])
def upsert_env_def():
    data = request.json
    env_id = data["env_id"]
    with get_db() as db:
        db.execute(
            """INSERT INTO env_definitions
               (env_id, display_name, category, scan_commands, version_flag, config_patterns, service_commands, status_check)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(env_id) DO UPDATE SET
               display_name=excluded.display_name, category=excluded.category,
               scan_commands=excluded.scan_commands, version_flag=excluded.version_flag,
               config_patterns=excluded.config_patterns, service_commands=excluded.service_commands,
               status_check=excluded.status_check""",
            (
                env_id,
                data["display_name"],
                data["category"],
                json.dumps(data.get("scan_commands", []), ensure_ascii=False),
                data.get("version_flag", ""),
                json.dumps(data.get("config_patterns", []), ensure_ascii=False),
                json.dumps(data.get("service_commands", []), ensure_ascii=False),
                json.dumps(data.get("status_check", {}), ensure_ascii=False),
            ),
        )
    return jsonify({"success": True})


@bp.route("/api/env-defs/<env_id>", methods=["DELETE"])
def delete_env_def(env_id):
    with get_db() as db:
        db.execute("DELETE FROM env_definitions WHERE env_id = ?", (env_id,))
    return jsonify({"success": True})


@bp.route("/api/env-defs/reset", methods=["POST"])
def reset_env_defs():
    with get_db() as db:
        db.execute("DELETE FROM env_definitions")
    _seed_env_definitions()
    return jsonify({"success": True})
