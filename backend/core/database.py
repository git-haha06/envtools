"""SQLite database for persistent storage."""

import os
import sqlite3
import json
from contextlib import contextmanager

from backend import DATA_DIR

DB_DIR = os.path.join(os.path.expanduser("~"), ".envtools")
DB_PATH = os.path.join(DB_DIR, "envtools.db")
DEFS_JSON = os.path.join(DATA_DIR, "env_defs.json")


def _ensure_dir():
    os.makedirs(DB_DIR, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create all tables if they don't exist, then seed defaults."""
    _ensure_dir()
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS manual_envs (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                category TEXT NOT NULL,
                path TEXT NOT NULL,
                bin_path TEXT NOT NULL,
                version_command TEXT,
                version TEXT,
                add_to_path INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS app_config (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS custom_config_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                env_id TEXT NOT NULL,
                name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                UNIQUE(env_id, file_path)
            );

            CREATE TABLE IF NOT EXISTS env_definitions (
                env_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                category TEXT NOT NULL,
                scan_commands TEXT NOT NULL DEFAULT '[]',
                version_flag TEXT NOT NULL DEFAULT '',
                config_patterns TEXT NOT NULL DEFAULT '[]',
                service_commands TEXT NOT NULL DEFAULT '[]',
                status_check TEXT NOT NULL DEFAULT '{}'
            );
        """)

    with get_db() as db:
        cols = [row[1] for row in db.execute("PRAGMA table_info(env_definitions)").fetchall()]
        if "status_check" not in cols:
            db.execute("ALTER TABLE env_definitions ADD COLUMN status_check TEXT NOT NULL DEFAULT '{}'")

    _migrate_json_data()
    _seed_env_definitions()
    _migrate_status_check_format()
    _sync_env_definitions()


def _migrate_json_data():
    """One-time migration: import existing JSON files into SQLite."""
    _migrate_manual_envs()
    _migrate_app_config()


def _migrate_manual_envs():
    json_path = os.path.join(DB_DIR, "manual_envs.json")
    if not os.path.exists(json_path):
        return
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            envs = json.load(f)
        if not envs:
            return
        with get_db() as db:
            existing = db.execute("SELECT COUNT(*) FROM manual_envs").fetchone()[0]
            if existing > 0:
                return
            for env in envs:
                db.execute(
                    """INSERT OR IGNORE INTO manual_envs
                       (id, name, display_name, category, path, bin_path, version_command, version, add_to_path)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (env["id"], env["name"], env["display_name"], env["category"],
                     env["path"], env["bin_path"], env.get("version_command"),
                     env.get("version"), 1 if env.get("add_to_path") else 0),
                )
        os.rename(json_path, json_path + ".migrated")
    except Exception as e:
        print(f"[envtools] Migration of manual_envs.json failed: {e}")


def _migrate_app_config():
    json_path = os.path.join(DB_DIR, "config.json")
    if not os.path.exists(json_path):
        return
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        if not cfg:
            return
        with get_db() as db:
            existing = db.execute("SELECT COUNT(*) FROM app_config").fetchone()[0]
            if existing > 0:
                return
            for key, value in cfg.items():
                db.execute(
                    "INSERT OR IGNORE INTO app_config (key, value) VALUES (?, ?)",
                    (key, json.dumps(value) if not isinstance(value, str) else value),
                )
        os.rename(json_path, json_path + ".migrated")
    except Exception as e:
        print(f"[envtools] Migration of config.json failed: {e}")


def _migrate_status_check_format():
    """Migrate old status_check format (ports) to new format (port_detect)."""
    try:
        if not os.path.exists(DEFS_JSON):
            return
        with open(DEFS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        new_defs = {e["env_id"]: e.get("status_check", {}) for e in data.get("environments", [])}

        with get_db() as db:
            rows = db.execute(
                "SELECT env_id, status_check FROM env_definitions WHERE status_check != '{}'"
            ).fetchall()
            for r in rows:
                check = json.loads(r["status_check"])
                if "ports" in check and "port_detect" not in check:
                    new_check = new_defs.get(r["env_id"])
                    if new_check and "port_detect" in new_check:
                        db.execute(
                            "UPDATE env_definitions SET status_check = ? WHERE env_id = ?",
                            (json.dumps(new_check, ensure_ascii=False), r["env_id"]),
                        )
            print("[envtools] Migrated status_check format (ports -> port_detect).")
    except Exception as e:
        print(f"[envtools] status_check format migration: {e}")


def _sync_env_definitions():
    """Sync config_patterns, service_commands, scan_commands from env_defs.json
    into existing DB rows (preserves user customizations to other fields)."""
    if not os.path.exists(DEFS_JSON):
        return
    try:
        with open(DEFS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        defs_map = {e["env_id"]: e for e in data.get("environments", [])}

        with get_db() as db:
            rows = db.execute("SELECT env_id, scan_commands, config_patterns, service_commands FROM env_definitions").fetchall()
            updated = 0
            for r in rows:
                eid = r["env_id"]
                if eid not in defs_map:
                    continue
                src = defs_map[eid]
                new_scan = json.dumps(src.get("scan_commands", []), ensure_ascii=False)
                new_cfg = json.dumps(src.get("config_patterns", []), ensure_ascii=False)
                new_svc = json.dumps(src.get("service_commands", []), ensure_ascii=False)
                new_sc = json.dumps(src.get("status_check", {}), ensure_ascii=False)
                new_vf = src.get("version_flag", "")
                if (r["scan_commands"] != new_scan or r["config_patterns"] != new_cfg
                        or r["service_commands"] != new_svc):
                    db.execute(
                        """UPDATE env_definitions
                           SET scan_commands=?, config_patterns=?, service_commands=?,
                               status_check=?, version_flag=?
                           WHERE env_id=?""",
                        (new_scan, new_cfg, new_svc, new_sc, new_vf, eid),
                    )
                    updated += 1
            if updated:
                print(f"[envtools] Synced {updated} environment definitions from env_defs.json.")
    except Exception as e:
        print(f"[envtools] Sync env_definitions: {e}")


def _seed_env_definitions():
    """Seed env_definitions table from env_defs.json if empty."""
    if not os.path.exists(DEFS_JSON):
        print(f"[envtools] env_defs.json not found at {DEFS_JSON}, skipping seed.")
        return
    try:
        with get_db() as db:
            existing = db.execute("SELECT COUNT(*) FROM env_definitions").fetchone()[0]
            if existing > 0:
                return

        with open(DEFS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        envs = data.get("environments", [])
        if not envs:
            return

        with get_db() as db:
            for env in envs:
                db.execute(
                    """INSERT OR IGNORE INTO env_definitions
                       (env_id, display_name, category, scan_commands, version_flag, config_patterns, service_commands, status_check)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        env["env_id"],
                        env["display_name"],
                        env["category"],
                        json.dumps(env.get("scan_commands", []), ensure_ascii=False),
                        env.get("version_flag", ""),
                        json.dumps(env.get("config_patterns", []), ensure_ascii=False),
                        json.dumps(env.get("service_commands", []), ensure_ascii=False),
                        json.dumps(env.get("status_check", {}), ensure_ascii=False),
                    ),
                )
        print(f"[envtools] Seeded {len(envs)} environment definitions into database.")
    except Exception as e:
        print(f"[envtools] Seeding env_definitions failed: {e}")
