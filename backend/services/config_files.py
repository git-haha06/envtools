"""Discover and edit configuration files for detected/manual environments."""

import glob
import json
import os
import platform

from backend.core.database import get_db

IS_WINDOWS = platform.system() == "Windows"
HOME = os.path.expanduser("~")
APPDATA = os.environ.get("APPDATA", os.path.join(HOME, "AppData", "Roaming"))


def _get_config_patterns(env_id: str) -> list[dict]:
    """Read config patterns for an env_id from the database."""
    with get_db() as db:
        row = db.execute(
            "SELECT config_patterns FROM env_definitions WHERE env_id = ?",
            (env_id,),
        ).fetchone()
    if not row:
        return []
    try:
        return json.loads(row["config_patterns"])
    except (json.JSONDecodeError, TypeError):
        return []


_BIN_SUFFIXES = {"bin", "sbin", "cmd", "scripts"}


def _resolve_root(env_path: str | None) -> str | None:
    """Derive the installation root from an executable directory.

    If env_path ends with a common binary subdirectory like 'bin',
    the root is the parent. Otherwise root == env_path.
    """
    if not env_path:
        return None
    basename = os.path.basename(env_path.rstrip("\\/")).lower()
    if basename in _BIN_SUFFIXES:
        return os.path.dirname(env_path)
    return env_path


def _expand(pattern: str, env_path: str | None) -> list[str]:
    """Expand a search pattern into real file paths."""
    s = pattern.replace("{home}", HOME).replace("{appdata}", APPDATA)

    root = _resolve_root(env_path)
    if env_path:
        s = s.replace("{path}", env_path)
    if root:
        s = s.replace("{root}", root)

    if "{path}" in s or "{root}" in s:
        return []

    if "*" in s:
        return glob.glob(s)
    return [s]


def discover_config_files(env_id: str, env_path: str | None = None) -> list[dict]:
    """Return list of config files found for an environment.

    Each result: {"name": display_name, "path": absolute_path, "exists": bool, "custom": bool}
    """
    patterns = _get_config_patterns(env_id)
    results = []
    seen_paths = set()

    for pat in patterns:
        if not pat.get("search"):
            continue
        for search in pat["search"]:
            candidates = _expand(search, env_path)
            for fpath in candidates:
                fpath = os.path.normpath(fpath)
                if fpath in seen_paths:
                    continue
                seen_paths.add(fpath)
                if os.path.isfile(fpath):
                    results.append({
                        "name": pat["name"],
                        "path": fpath,
                        "exists": True,
                        "custom": False,
                    })

    if env_path and os.path.isdir(env_path):
        config_extensions = {".ini", ".cfg", ".conf", ".cnf", ".toml", ".yaml", ".yml", ".json", ".xml", ".properties"}
        config_names = {"config", "settings", ".env"}
        try:
            for fname in os.listdir(env_path):
                fpath = os.path.normpath(os.path.join(env_path, fname))
                if fpath in seen_paths:
                    continue
                _, ext = os.path.splitext(fname)
                name_lower = fname.lower()
                if ext.lower() in config_extensions or name_lower in config_names:
                    if os.path.isfile(fpath):
                        seen_paths.add(fpath)
                        results.append({
                            "name": fname,
                            "path": fpath,
                            "exists": True,
                            "custom": False,
                        })
        except PermissionError:
            pass

    if env_path:
        parent = os.path.dirname(env_path)
        if parent and os.path.isdir(parent) and parent != env_path:
            config_extensions = {".ini", ".cfg", ".conf", ".cnf"}
            try:
                for fname in os.listdir(parent):
                    fpath = os.path.normpath(os.path.join(parent, fname))
                    if fpath in seen_paths:
                        continue
                    _, ext = os.path.splitext(fname)
                    if ext.lower() in config_extensions and os.path.isfile(fpath):
                        seen_paths.add(fpath)
                        results.append({
                            "name": f"../{fname}",
                            "path": fpath,
                            "exists": True,
                            "custom": False,
                        })
            except PermissionError:
                pass

    with get_db() as db:
        rows = db.execute(
            "SELECT name, file_path FROM custom_config_files WHERE env_id = ? ORDER BY id",
            (env_id,),
        ).fetchall()
        for row in rows:
            fpath = os.path.normpath(row["file_path"])
            if fpath in seen_paths:
                continue
            seen_paths.add(fpath)
            results.append({
                "name": row["name"],
                "path": fpath,
                "exists": os.path.isfile(fpath),
                "custom": True,
            })

    return results


def add_custom_config_file(env_id: str, file_path: str) -> dict:
    """Persist a user-added config file path for an environment."""
    file_path = os.path.normpath(file_path)
    fname = os.path.basename(file_path) or file_path
    with get_db() as db:
        db.execute(
            "INSERT OR IGNORE INTO custom_config_files (env_id, name, file_path) VALUES (?, ?, ?)",
            (env_id, fname, file_path),
        )
    return {"name": fname, "path": file_path, "exists": os.path.isfile(file_path), "custom": True}


def remove_custom_config_file(env_id: str, file_path: str):
    """Remove a user-added config file path for an environment."""
    file_path = os.path.normpath(file_path)
    with get_db() as db:
        db.execute(
            "DELETE FROM custom_config_files WHERE env_id = ? AND file_path = ?",
            (env_id, file_path),
        )


def read_config_file(file_path: str) -> str:
    """Read a config file and return its content."""
    file_path = os.path.normpath(file_path)
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def save_config_file(file_path: str, content: str):
    """Save content to a config file. Creates parent dirs if needed."""
    file_path = os.path.normpath(file_path)
    parent = os.path.dirname(file_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
