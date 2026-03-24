import json
import os
import platform
import re
import shutil
import subprocess
import socket

from backend.core.database import get_db

_BIN_SUBDIRS = ("bin", "sbin", "Scripts", "cmd")


def _get_scan_targets() -> list[dict]:
    """Read scan targets from env_definitions table."""
    with get_db() as db:
        rows = db.execute(
            "SELECT env_id, display_name, category, scan_commands, version_flag "
            "FROM env_definitions WHERE scan_commands != '[]' ORDER BY rowid"
        ).fetchall()
    targets = []
    for r in rows:
        cmds = json.loads(r["scan_commands"])
        if not cmds:
            continue
        targets.append({
            "id": r["env_id"],
            "display_name": r["display_name"],
            "category": r["category"],
            "commands": cmds,
            "version_flag": r["version_flag"],
        })
    return targets


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


def _build_extended_path() -> str:
    """Build an extended PATH string with %VAR% expanded and bin
    subdirectories included, so executables under root-level entries
    are discoverable by shutil.which()."""
    from . import env_vars
    expanded = env_vars.get_expanded_merged_path_entries()
    extra = []
    for p in expanded:
        for subdir in _BIN_SUBDIRS:
            candidate = os.path.join(p, subdir)
            if os.path.isdir(candidate):
                extra.append(candidate)
    sep = ";" if platform.system() == "Windows" else ":"
    return sep.join(expanded + extra)


def _try_get_version(cmd: str, flag: str, search_path: str) -> tuple[str, str] | None:
    try:
        exe_path = shutil.which(cmd, path=search_path)
        if not exe_path:
            return None
        args = [exe_path] + flag.split() if flag else [exe_path]
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        combined = f"{result.stdout.strip()} {result.stderr.strip()}"
        version = _extract_version(combined)
        if not version:
            return None
        path = os.path.dirname(exe_path)
        return version, path
    except Exception:
        return None


def scan_all_environments() -> list[dict]:
    from . import env_vars
    env_vars.refresh_process_env()

    merged_paths = {p.lower().rstrip("\\/") for p in env_vars.get_expanded_merged_path_entries()}
    user_paths = {p.lower().rstrip("\\/") for p in env_vars.get_expanded_path_entries()}

    extended_path = _build_extended_path()

    targets = _get_scan_targets()
    results = []
    for target in targets:
        for cmd in target["commands"]:
            info = _try_get_version(cmd, target["version_flag"], extended_path)
            if info:
                version, path = info
                path_lower = (path or "").lower().rstrip("\\/")
                parent_lower = os.path.dirname(path_lower).rstrip("\\/") if path_lower else ""
                in_user_path = path_lower in user_paths or parent_lower in user_paths
                in_system_path = (
                    (path_lower in merged_paths or parent_lower in merged_paths)
                    and not in_user_path
                )
                results.append({
                    "id": target["id"],
                    "name": cmd,
                    "display_name": target["display_name"],
                    "version": version,
                    "path": path,
                    "category": target["category"],
                    "in_path": True,
                    "in_user_path": in_user_path,
                    "in_system_path": in_system_path,
                    "icon": None,
                })
                break
    return results


def get_system_info() -> dict:
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "arch": platform.machine(),
        "hostname": socket.gethostname(),
        "home_dir": os.path.expanduser("~"),
    }
