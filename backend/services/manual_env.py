import os
import re
import subprocess

from backend.core.database import get_db


def _extract_version(text: str) -> str | None:
    for word in text.split():
        trimmed = word.lstrip("vV")
        parts = trimmed.split(".")
        if len(parts) >= 2 and parts[0].isdigit():
            return trimmed
    m = re.search(r"(\d+\.\d+[\.\d\-\w]*)", text)
    if m:
        return m.group(1).rstrip(".")
    return None


def _detect_version(bin_path: str, version_command: str) -> str | None:
    parts = version_command.split()
    if not parts:
        return None
    exe_name = parts[0]
    args = parts[1:]
    exe_path = os.path.join(bin_path, exe_name)
    exe_str = exe_path if os.path.exists(exe_path) else exe_name
    try:
        result = subprocess.run(
            [exe_str] + args, capture_output=True, text=True,
            cwd=bin_path, timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        combined = f"{result.stdout.strip()} {result.stderr.strip()}"
        return _extract_version(combined)
    except Exception:
        return None


def _row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "display_name": row["display_name"],
        "category": row["category"],
        "path": row["path"],
        "bin_path": row["bin_path"],
        "version_command": row["version_command"],
        "version": row["version"],
        "add_to_path": bool(row["add_to_path"]),
    }


def get_manual_envs() -> list[dict]:
    with get_db() as db:
        rows = db.execute("SELECT * FROM manual_envs ORDER BY rowid").fetchall()
        return [_row_to_dict(r) for r in rows]


def add_manual_env(request: dict) -> dict:
    base_path = request["path"]
    if not os.path.exists(base_path):
        raise ValueError(f"Path does not exist: {base_path}")

    bin_subdir = request.get("bin_subdir", "")
    if bin_subdir:
        bin_path = os.path.join(base_path, bin_subdir)
    else:
        from . import env_vars
        resolved = env_vars.resolve_bin_path(base_path)
        bin_path = resolved["path"]

    version_command = request.get("version_command")
    version = None
    if version_command:
        version = _detect_version(bin_path, version_command)

    env_id = f"manual_{request['name'].lower().replace(' ', '_')}"

    with get_db() as db:
        existing = db.execute("SELECT id FROM manual_envs WHERE id = ?", (env_id,)).fetchone()
        if existing:
            raise ValueError(f"Environment with name '{request['name']}' already exists")

        add_to_path = request.get("add_to_path", False)
        db.execute(
            """INSERT INTO manual_envs
               (id, name, display_name, category, path, bin_path, version_command, version, add_to_path)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (env_id, request["name"], request["display_name"], request["category"],
             base_path, bin_path, version_command, version, 1 if add_to_path else 0),
        )

    if add_to_path and os.path.isdir(bin_path):
        from . import env_vars
        env_vars.add_to_path(bin_path)

    return {
        "id": env_id,
        "name": request["name"],
        "display_name": request["display_name"],
        "category": request["category"],
        "path": base_path,
        "bin_path": bin_path,
        "version_command": version_command,
        "version": version,
        "add_to_path": add_to_path,
    }


def remove_manual_env(env_id: str):
    bin_path_to_remove = None
    with get_db() as db:
        row = db.execute("SELECT * FROM manual_envs WHERE id = ?", (env_id,)).fetchone()
        if row and row["add_to_path"]:
            bin_path_to_remove = row["bin_path"]
        db.execute("DELETE FROM manual_envs WHERE id = ?", (env_id,))

    if bin_path_to_remove:
        from . import env_vars
        try:
            env_vars.remove_from_path(bin_path_to_remove)
        except Exception:
            pass


def refresh_manual_env_version(env_id: str) -> str | None:
    with get_db() as db:
        row = db.execute("SELECT * FROM manual_envs WHERE id = ?", (env_id,)).fetchone()
        if not row or not row["version_command"]:
            return None
        new_version = _detect_version(row["bin_path"], row["version_command"])
        db.execute("UPDATE manual_envs SET version = ? WHERE id = ?", (new_version, env_id))
        return new_version
