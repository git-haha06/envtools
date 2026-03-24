"""Check running status and listening ports for environments.

Port detection strategy:
  1. Read config files discovered for the environment
  2. Use regex patterns from port_detect to extract actual port numbers
  3. Fall back to default ports if pattern not found

Performance:
  - Process check (tasklist/ps) runs once for all environments
  - Port checks run in parallel via ThreadPoolExecutor
  - Socket timeout reduced to 0.3s for fast failure on closed ports
"""

import json
import os
import platform
import re
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.core.database import get_db

IS_WINDOWS = platform.system() == "Windows"

_config_file_cache: dict[str, str] = {}


def _get_status_checks() -> dict[str, dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT env_id, status_check FROM env_definitions WHERE status_check != '{}'"
        ).fetchall()
    result = {}
    for r in rows:
        try:
            check = json.loads(r["status_check"])
            if check:
                result[r["env_id"]] = check
        except (json.JSONDecodeError, TypeError):
            pass
    return result


def _check_port(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.3):
            return True
    except (OSError, ConnectionRefusedError, TimeoutError):
        return False


def _check_ports_parallel(ports: list[tuple[int, str]]) -> list[dict]:
    """Check multiple ports in parallel. ports: [(port_num, label), ...]"""
    if not ports:
        return []

    results = {}
    with ThreadPoolExecutor(max_workers=min(len(ports), 8)) as pool:
        futures = {
            pool.submit(_check_port, port): (port, label)
            for port, label in ports
        }
        for future in as_completed(futures):
            port, label = futures[future]
            try:
                is_open = future.result()
            except Exception:
                is_open = False
            results[port] = {"port": port, "label": label, "open": is_open}

    return [results[port] for port, _ in ports if port in results]


def _read_config_contents(env_id: str, env_path: str | None) -> str:
    cache_key = f"{env_id}:{env_path or ''}"
    if cache_key in _config_file_cache:
        return _config_file_cache[cache_key]

    from . import config_files
    files = config_files.discover_config_files(env_id, env_path)
    combined = ""
    for f in files:
        if f.get("exists") and os.path.isfile(f["path"]):
            try:
                with open(f["path"], "r", encoding="utf-8", errors="replace") as fh:
                    combined += fh.read() + "\n"
            except Exception:
                pass
    _config_file_cache[cache_key] = combined
    return combined


def _strip_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped.startswith(";") or stripped.startswith("//"):
            continue
        lines.append(line)
    return "\n".join(lines)


def _extract_ports(port_detect: list[dict], config_content: str) -> list[tuple[int, str]]:
    """Extract port numbers from config content. Returns [(port, label), ...]"""
    results = []
    seen = set()
    clean = _strip_comments(config_content) if config_content else ""

    for pd in port_detect:
        label = pd.get("label", "")
        default_port = pd.get("default", 0)
        pattern = pd.get("pattern", "")
        port_num = default_port

        if pattern and clean:
            try:
                m = re.search(pattern, clean, re.MULTILINE)
                if m and m.group(1):
                    extracted = int(m.group(1))
                    if 1 <= extracted <= 65535:
                        port_num = extracted
            except (re.error, ValueError, IndexError):
                pass

        if port_num and port_num not in seen:
            seen.add(port_num)
            results.append((port_num, label))

    return results


def _find_process(process_names: list[str]) -> dict | None:
    if not process_names:
        return None
    try:
        if IS_WINDOWS:
            output = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True, text=True, timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            ).stdout
            lower_names = {n.lower() for n in process_names}
            lower_names |= {n.lower() + ".exe" for n in process_names}
            for line in output.strip().splitlines():
                parts = line.replace('"', '').split(',')
                if len(parts) >= 2:
                    pname = parts[0].strip()
                    if pname.lower() in lower_names:
                        try:
                            return {"pid": int(parts[1].strip()), "name": pname}
                        except ValueError:
                            return {"pid": 0, "name": pname}
        else:
            output = subprocess.run(
                ["ps", "-eo", "pid,comm"],
                capture_output=True, text=True, timeout=10,
            ).stdout
            lower_names = {n.lower() for n in process_names}
            for line in output.strip().splitlines()[1:]:
                parts = line.strip().split(None, 1)
                if len(parts) == 2:
                    pname = parts[1].strip()
                    if pname.lower() in lower_names or os.path.basename(pname).lower() in lower_names:
                        try:
                            return {"pid": int(parts[0]), "name": pname}
                        except ValueError:
                            return {"pid": 0, "name": pname}
    except Exception:
        pass
    return None


def check_env_status(env_id: str, env_path: str | None = None) -> dict:
    checks = _get_status_checks()
    check = checks.get(env_id)
    if not check:
        return {"env_id": env_id, "running": None, "pid": None, "ports": []}

    proc_names = check.get("process_names", [])
    port_detect = check.get("port_detect", [])

    proc = _find_process(proc_names)
    running = proc is not None

    config_content = ""
    if port_detect:
        config_content = _read_config_contents(env_id, env_path)

    port_tuples = _extract_ports(port_detect, config_content)
    port_results = _check_ports_parallel(port_tuples)

    for pr in port_results:
        if pr["open"] and not running:
            running = True

    return {
        "env_id": env_id,
        "running": running,
        "pid": proc["pid"] if proc else None,
        "ports": port_results,
    }


def _batch_find_processes(all_names: set[str]) -> dict[str, int]:
    result = {}
    try:
        if IS_WINDOWS:
            output = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True, text=True, timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            ).stdout
            for line in output.strip().splitlines():
                parts = line.replace('"', '').split(',')
                if len(parts) >= 2:
                    pname = parts[0].strip().lower()
                    if pname in all_names:
                        try:
                            result[pname] = int(parts[1].strip())
                        except ValueError:
                            result[pname] = 0
        else:
            output = subprocess.run(
                ["ps", "-eo", "pid,comm"],
                capture_output=True, text=True, timeout=10,
            ).stdout
            for line in output.strip().splitlines()[1:]:
                parts = line.strip().split(None, 1)
                if len(parts) == 2:
                    pname = parts[1].strip().lower()
                    basename = os.path.basename(pname).lower()
                    for n in (pname, basename):
                        if n in all_names:
                            try:
                                result[n] = int(parts[0])
                            except ValueError:
                                result[n] = 0
    except Exception:
        pass
    return result


def check_all_status(env_ids: list[str] | None = None) -> list[dict]:
    """Check status for all environments. Optimized: single tasklist + parallel port checks."""
    global _config_file_cache
    _config_file_cache = {}

    checks = _get_status_checks()
    if env_ids:
        ids_to_check = [eid for eid in env_ids if eid in checks]
    else:
        ids_to_check = list(checks.keys())

    if not ids_to_check:
        return []

    all_process_names = set()
    for eid in ids_to_check:
        for n in checks[eid].get("process_names", []):
            all_process_names.add(n.lower())
            if IS_WINDOWS:
                all_process_names.add(n.lower() + ".exe")

    running_procs = _batch_find_processes(all_process_names)

    env_port_map: dict[str, list[tuple[int, str]]] = {}
    all_ports_to_check: list[tuple[int, str]] = []
    all_ports_set: set[int] = set()

    for eid in ids_to_check:
        check = checks[eid]
        port_detect = check.get("port_detect", [])
        if not port_detect:
            env_port_map[eid] = []
            continue

        config_content = _read_config_contents(eid, None)
        port_tuples = _extract_ports(port_detect, config_content)
        env_port_map[eid] = port_tuples
        for port, label in port_tuples:
            if port not in all_ports_set:
                all_ports_set.add(port)
                all_ports_to_check.append((port, label))

    port_open_map: dict[int, bool] = {}
    if all_ports_to_check:
        with ThreadPoolExecutor(max_workers=min(len(all_ports_to_check), 16)) as pool:
            futures = {
                pool.submit(_check_port, port): port
                for port, _ in all_ports_to_check
            }
            for future in as_completed(futures):
                port = futures[future]
                try:
                    port_open_map[port] = future.result()
                except Exception:
                    port_open_map[port] = False

    results = []
    for eid in ids_to_check:
        check = checks[eid]
        proc_names = check.get("process_names", [])

        pid = None
        proc_running = False
        for n in proc_names:
            for variant in (n.lower(), n.lower() + ".exe" if IS_WINDOWS else n.lower()):
                if variant in running_procs:
                    pid = running_procs[variant]
                    proc_running = True
                    break
            if proc_running:
                break

        port_results = []
        for port, label in env_port_map.get(eid, []):
            is_open = port_open_map.get(port, False)
            port_results.append({"port": port, "label": label, "open": is_open})
            if is_open and not proc_running:
                proc_running = True

        results.append({
            "env_id": eid,
            "running": proc_running,
            "pid": pid,
            "ports": port_results,
        })

    _config_file_cache = {}
    return results
