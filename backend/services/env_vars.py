import os
import platform
import re
import subprocess

IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"


def _expand_vars(value: str) -> str:
    """Expand %VARIABLE% references using both os.environ and the Windows
    Registry (user + system env vars) so that even freshly-set variables
    like %JAVA_HOME% are resolved correctly."""
    if not IS_WINDOWS or "%" not in value:
        return os.path.expandvars(value)

    def _replacer(m):
        name = m.group(1)
        val = os.environ.get(name)
        if val is not None:
            return val
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
            v, _ = winreg.QueryValueEx(key, name)
            winreg.CloseKey(key)
            return str(v)
        except OSError:
            pass
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
            )
            v, _ = winreg.QueryValueEx(key, name)
            winreg.CloseKey(key)
            return str(v)
        except OSError:
            pass
        return m.group(0)

    return re.sub(r"%([^%]+)%", _replacer, value)


def _broadcast_env_change():
    """Notify the system that environment variables changed.

    Refreshes the current process env immediately, then sends
    WM_SETTINGCHANGE in a background thread so it doesn't block the
    API response.
    """
    _refresh_process_env()

    if IS_WINDOWS:
        import threading

        def _send():
            try:
                import ctypes
                from ctypes import wintypes
                HWND_BROADCAST = 0xFFFF
                WM_SETTINGCHANGE = 0x001A
                SMTO_ABORTIFHUNG = 0x0002
                result = wintypes.DWORD()
                ctypes.windll.user32.SendMessageTimeoutW(
                    HWND_BROADCAST, WM_SETTINGCHANGE, 0,
                    "Environment", SMTO_ABORTIFHUNG, 5000,
                    ctypes.byref(result),
                )
            except Exception:
                pass

        threading.Thread(target=_send, daemon=True).start()


def _refresh_process_env():
    """Reload PATH and user env vars into the current process so that
    shutil.which / subprocess pick up changes immediately."""
    if IS_WINDOWS:
        try:
            import winreg

            # Refresh non-PATH user env vars first (so %JAVA_HOME% etc.
            # are available when we expand PATH entries below)
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        if name.upper() != "PATH":
                            os.environ[name] = str(value)
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except OSError:
                pass

            # Also load system env vars (JAVA_HOME may be system-level)
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                )
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        if name.upper() != "PATH" and name not in os.environ:
                            os.environ[name] = str(value)
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except OSError:
                pass

            # Now build PATH with expanded %VAR% references
            parts = []
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                )
                sys_path, _ = winreg.QueryValueEx(key, "Path")
                winreg.CloseKey(key)
                parts.append(str(sys_path))
            except OSError:
                pass
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
                usr_path, _ = winreg.QueryValueEx(key, "Path")
                winreg.CloseKey(key)
                parts.append(str(usr_path))
            except OSError:
                pass
            if parts:
                raw_merged = ";".join(parts)
                os.environ["PATH"] = _expand_vars(raw_merged)
        except Exception:
            pass


# ─── Windows ─────────────────────────────────────────────

def _win_get_user_env_vars() -> dict[str, str]:
    import winreg
    result = {}
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
        i = 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, i)
                result[name] = str(value)
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
    except OSError:
        pass
    return result


def _win_set_user_env_var(name: str, value: str):
    import winreg
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Environment")
    winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
    winreg.CloseKey(key)
    _broadcast_env_change()


def _win_remove_user_env_var(name: str):
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_WRITE)
        winreg.DeleteValue(key, name)
        winreg.CloseKey(key)
        _broadcast_env_change()
    except OSError:
        pass


def _win_get_path_entries() -> list[str]:
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
        value, _ = winreg.QueryValueEx(key, "Path")
        winreg.CloseKey(key)
        return [p for p in str(value).split(";") if p.strip()]
    except OSError:
        return os.environ.get("PATH", "").split(";")


def _win_add_to_path(new_path: str):
    import winreg
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Environment")
    try:
        current, _ = winreg.QueryValueEx(key, "Path")
        current = str(current)
    except OSError:
        current = ""
    paths = [p for p in current.split(";") if p.strip()]
    new_expanded = _expand_vars(new_path).lower().rstrip("\\/")
    for p in paths:
        if _expand_vars(p).lower().rstrip("\\/") == new_expanded:
            winreg.CloseKey(key)
            return
    paths.append(new_path)
    winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, ";".join(paths))
    winreg.CloseKey(key)
    _broadcast_env_change()


def _win_remove_from_path(path_to_remove: str):
    import winreg
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Environment")
    try:
        current, _ = winreg.QueryValueEx(key, "Path")
        current = str(current)
    except OSError:
        winreg.CloseKey(key)
        return
    remove_expanded = _expand_vars(path_to_remove).lower().rstrip("\\/")
    paths = [
        p for p in current.split(";")
        if p.strip() and _expand_vars(p).lower().rstrip("\\/") != remove_expanded
    ]
    winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, ";".join(paths))
    winreg.CloseKey(key)
    _broadcast_env_change()


# ─── macOS / Linux ───────────────────────────────────────

def _unix_get_user_env_vars() -> dict[str, str]:
    return dict(os.environ)


def _unix_set_user_env_var(name: str, value: str):
    profile = _get_profile_path()
    os.environ[name] = value
    _update_profile(profile, name, value)


def _unix_remove_user_env_var(name: str):
    profile = _get_profile_path()
    os.environ.pop(name, None)
    _remove_from_profile(profile, name)


def _unix_add_to_path(new_path: str):
    path = os.environ.get("PATH", "")
    paths = path.split(":")
    if new_path not in paths:
        paths.append(new_path)
        os.environ["PATH"] = ":".join(paths)
    profile = _get_profile_path()
    _update_profile(profile, "PATH", f"$PATH:{new_path}")


def _unix_remove_from_path(path_to_remove: str):
    path = os.environ.get("PATH", "")
    paths = [p for p in path.split(":") if p != path_to_remove]
    os.environ["PATH"] = ":".join(paths)


def _get_profile_path() -> str:
    home = os.path.expanduser("~")
    if IS_MACOS:
        return os.path.join(home, ".zprofile")
    return os.path.join(home, ".bashrc")


def _update_profile(path: str, name: str, value: str):
    lines = []
    marker = f"export {name}="
    if os.path.exists(path):
        with open(path, "r") as f:
            lines = f.readlines()
    new_lines = [ln for ln in lines if marker not in ln]
    new_lines.append(f'export {name}="{value}"\n')
    with open(path, "w") as f:
        f.writelines(new_lines)


def _remove_from_profile(path: str, name: str):
    marker = f"export {name}="
    if not os.path.exists(path):
        return
    with open(path, "r") as f:
        lines = f.readlines()
    new_lines = [ln for ln in lines if marker not in ln]
    with open(path, "w") as f:
        f.writelines(new_lines)


def refresh_process_env():
    """Public wrapper: reload system+user env vars into current process."""
    _refresh_process_env()


# ─── Windows system-level (read-only) ────────────────────

def _win_get_system_env_vars() -> dict[str, str]:
    import winreg
    result = {}
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        )
        i = 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, i)
                result[name] = str(value)
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
    except OSError:
        pass
    return result


def _win_get_system_path_entries() -> list[str]:
    import winreg
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        )
        value, _ = winreg.QueryValueEx(key, "Path")
        winreg.CloseKey(key)
        return [p for p in str(value).split(";") if p.strip()]
    except OSError:
        return []


def _win_get_merged_path_entries() -> list[str]:
    """Return system PATH + user PATH combined (for in_path checks)."""
    return _win_get_system_path_entries() + _win_get_path_entries()


# ─── Public API ──────────────────────────────────────────

def get_env_vars() -> dict[str, str]:
    if IS_WINDOWS:
        return _win_get_user_env_vars()
    return _unix_get_user_env_vars()


def get_system_env_vars() -> dict[str, str]:
    if IS_WINDOWS:
        return _win_get_system_env_vars()
    return dict(os.environ)


def set_env_var(name: str, value: str):
    if IS_WINDOWS:
        _win_set_user_env_var(name, value)
    else:
        _unix_set_user_env_var(name, value)


def remove_env_var(name: str):
    if IS_WINDOWS:
        _win_remove_user_env_var(name)
    else:
        _unix_remove_user_env_var(name)


def get_path_entries() -> list[str]:
    """Return raw user PATH entries (for UI display, may contain %VAR%)."""
    if IS_WINDOWS:
        return _win_get_path_entries()
    path = os.environ.get("PATH", "")
    return [p for p in path.split(":") if p.strip()]


def get_system_path_entries() -> list[str]:
    """Return raw system PATH entries (for UI display, may contain %VAR%)."""
    if IS_WINDOWS:
        return _win_get_system_path_entries()
    return []


def get_merged_path_entries() -> list[str]:
    """Return raw PATH entries (system + user), may contain %VAR%."""
    if IS_WINDOWS:
        return _win_get_merged_path_entries()
    path = os.environ.get("PATH", "")
    return [p for p in path.split(":") if p.strip()]


def get_expanded_path_entries() -> list[str]:
    """Return expanded user PATH entries (for internal comparison)."""
    return [_expand_vars(p) for p in get_path_entries()]


def get_expanded_system_path_entries() -> list[str]:
    """Return expanded system PATH entries (for internal comparison)."""
    return [_expand_vars(p) for p in get_system_path_entries()]


def get_expanded_merged_path_entries() -> list[str]:
    """Return all PATH entries expanded (for scanning/comparison)."""
    return [_expand_vars(p) for p in get_merged_path_entries()]


_BIN_SUBDIRS = ["bin", "sbin", "Scripts", "cmd"]
_EXE_EXTENSIONS = {".exe", ".bat", ".cmd", ".com", ".ps1", ".sh", ""}


def _has_executables(directory: str) -> bool:
    """Check if a directory contains any executable files."""
    if not os.path.isdir(directory):
        return False
    try:
        for f in os.listdir(directory):
            _, ext = os.path.splitext(f)
            if ext.lower() in _EXE_EXTENSIONS and os.path.isfile(os.path.join(directory, f)):
                return True
    except PermissionError:
        pass
    return False


def resolve_bin_path(path: str) -> dict:
    """Resolve the actual bin directory for a given path.

    Expands %VAR% references, then checks if the path itself contains
    executables. If not, checks for bin/ subdirectory.

    Returns: {"path": actual_path, "adjusted": bool, "original": original_path}
    """
    path = path.rstrip("\\/")
    expanded = _expand_vars(path).rstrip("\\/")

    if _has_executables(expanded):
        return {"path": path, "adjusted": False, "original": path}

    for subdir in _BIN_SUBDIRS:
        candidate = os.path.join(expanded, subdir)
        if os.path.isdir(candidate) and _has_executables(candidate):
            actual = os.path.join(path, subdir)
            return {"path": actual, "adjusted": True, "original": path}

    return {"path": path, "adjusted": False, "original": path}


def add_to_path(path: str) -> dict:
    """Add path to user PATH. Auto-detects bin subdirectory.

    Returns: {"path": actual_added_path, "adjusted": bool}
    """
    resolved = resolve_bin_path(path)
    actual_path = resolved["path"]
    if IS_WINDOWS:
        _win_add_to_path(actual_path)
    else:
        _unix_add_to_path(actual_path)
    return resolved


def remove_from_path(path: str):
    if IS_WINDOWS:
        _win_remove_from_path(path)
    else:
        _unix_remove_from_path(path)
