"""Service control commands for environments."""

import json
import os
import platform
import subprocess

from backend.core.database import get_db

IS_WINDOWS = platform.system() == "Windows"


def get_commands(env_id: str) -> list[dict]:
    """Return command definitions for an environment from the database."""
    with get_db() as db:
        row = db.execute(
            "SELECT service_commands FROM env_definitions WHERE env_id = ?",
            (env_id,),
        ).fetchone()
    if not row:
        return []
    try:
        return json.loads(row["service_commands"])
    except (json.JSONDecodeError, TypeError):
        return []


_BIN_SUFFIXES = {"bin", "sbin", "cmd", "scripts"}


def _resolve_root(path: str | None) -> str | None:
    if not path:
        return None
    basename = os.path.basename(path.rstrip("\\/")).lower()
    if basename in _BIN_SUFFIXES:
        return os.path.dirname(path)
    return path


def _expand_template(cmd: str, bin_path: str | None, env_path: str | None) -> str:
    """Replace template variables in a command string.

    Supported variables:
      {bin_path} — the environment's executable directory
      {env_path} — the environment's root install directory
      {root}     — installation root (parent of bin/ if applicable)
    """
    result = cmd
    if bin_path:
        result = result.replace("{bin_path}", bin_path)
    if env_path:
        result = result.replace("{env_path}", env_path)
    root = _resolve_root(bin_path or env_path)
    if root:
        result = result.replace("{root}", root)
    return result


def run_command(
    cmd: str,
    cwd: str | None = None,
    bin_path: str | None = None,
    env_path: str | None = None,
    background: bool = False,
) -> dict:
    """Execute a command with the env's bin_path prepended to PATH.

    Template variables {bin_path} and {env_path} in cmd are expanded.
    Returns {"exit_code": int, "stdout": str, "stderr": str}
    """
    cmd = _expand_template(cmd, bin_path, env_path)

    env = dict(os.environ)
    if bin_path:
        sep = ";" if IS_WINDOWS else ":"
        env["PATH"] = bin_path + sep + env.get("PATH", "")

    work_dir = cwd or bin_path or None

    creation_flags = 0
    if IS_WINDOWS:
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    if background:
        try:
            if IS_WINDOWS:
                subprocess.Popen(
                    cmd, shell=True, cwd=work_dir, env=env,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW,
                )
            else:
                subprocess.Popen(
                    cmd, shell=True, cwd=work_dir, env=env,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
            return {"exit_code": 0, "stdout": "Process started in background.\n", "stderr": ""}
        except Exception as e:
            return {"exit_code": 1, "stdout": "", "stderr": str(e)}

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=30, cwd=work_dir, env=env,
            creationflags=creation_flags,
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "stdout": "", "stderr": "Command timed out (30s)"}
    except Exception as e:
        return {"exit_code": -1, "stdout": "", "stderr": str(e)}
