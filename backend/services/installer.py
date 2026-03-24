import os
import platform
import shutil
import subprocess
import zipfile
import tarfile
import toml
import requests

from backend import PROJECT_DIR

IS_WINDOWS = platform.system() == "Windows"
REGISTRY_DIR = os.path.join(PROJECT_DIR, "registry")


def load_manifests() -> list[dict]:
    manifests = []
    if not os.path.isdir(REGISTRY_DIR):
        return manifests
    for fname in os.listdir(REGISTRY_DIR):
        if fname.endswith(".toml"):
            try:
                with open(os.path.join(REGISTRY_DIR, fname), "r", encoding="utf-8") as f:
                    manifests.append(toml.load(f))
            except Exception as e:
                print(f"Failed to load {fname}: {e}")
    return manifests


def _get_download_url(manifest: dict, version: str, use_mirror: bool) -> str | None:
    arch = platform.machine().lower()
    if IS_WINDOWS:
        os_key = "windows"
    elif platform.system() == "Darwin":
        os_key = "macos" if "arm" in arch or "aarch" in arch else "macos_x64"
    else:
        os_key = "linux"

    sources = manifest.get("sources", {})
    source_dict = sources.get("mirror", {}) if use_mirror else sources.get("official", {})
    if not source_dict:
        source_dict = sources.get("official", {})

    template = source_dict.get(os_key)
    if not template and os_key == "macos_x64":
        template = source_dict.get("macos")
    if not template:
        return None
    return template.replace("{version}", version)


def _get_install_base_dir() -> str:
    return os.path.join(os.path.expanduser("~"), ".envtools", "installed")


def _get_cache_dir() -> str:
    return os.path.join(os.path.expanduser("~"), ".envtools", "cache")


def install_package(package_name: str, version: str, use_mirror: bool, install_dir: str | None = None) -> dict:
    manifests = load_manifests()
    manifest = next((m for m in manifests if m["package"]["name"] == package_name), None)
    if not manifest:
        return {"success": False, "message": f"Package '{package_name}' not found", "install_path": None}

    url = _get_download_url(manifest, version, use_mirror)
    if not url:
        return {"success": False, "message": "No download URL for this platform", "install_path": None}

    cache_dir = _get_cache_dir()
    base_dir = install_dir or _get_install_base_dir()
    dest_dir = os.path.join(base_dir, package_name, version)

    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(dest_dir, exist_ok=True)

    filename = url.split("/")[-1]
    cache_path = os.path.join(cache_dir, filename)

    try:
        resp = requests.get(url, stream=True, timeout=300)
        resp.raise_for_status()
        with open(cache_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
    except Exception as e:
        return {"success": False, "message": f"Download failed: {e}", "install_path": None}

    try:
        if filename.endswith(".zip"):
            with zipfile.ZipFile(cache_path, "r") as zf:
                zf.extractall(dest_dir)
        elif filename.endswith(".tar.gz") or filename.endswith(".tgz"):
            with tarfile.open(cache_path, "r:gz") as tf:
                tf.extractall(dest_dir)
        elif filename.endswith(".msi"):
            if IS_WINDOWS:
                subprocess.run(["msiexec", "/i", cache_path, "/passive", "/norestart"], check=True)
        elif filename.endswith(".exe"):
            if IS_WINDOWS:
                subprocess.run([cache_path, "/S"], check=True)
        else:
            return {"success": False, "message": f"Unsupported format: {filename}", "install_path": None}
    except Exception as e:
        return {"success": False, "message": f"Extraction failed: {e}", "install_path": None}

    bin_path = _find_bin_dir(dest_dir)
    if bin_path:
        from . import env_vars
        try:
            env_vars.add_to_path(bin_path)
        except Exception:
            pass

    display_name = manifest["package"]["display_name"]
    return {
        "success": True,
        "message": f"{display_name} {version} installed successfully",
        "install_path": dest_dir,
    }


def uninstall_package(install_path: str):
    if os.path.exists(install_path):
        shutil.rmtree(install_path)
    from . import env_vars
    try:
        env_vars.remove_from_path(install_path)
    except Exception:
        pass


def _find_bin_dir(install_dir: str) -> str | None:
    bin_dir = os.path.join(install_dir, "bin")
    if os.path.isdir(bin_dir):
        return bin_dir
    try:
        for entry in os.listdir(install_dir):
            sub = os.path.join(install_dir, entry)
            if os.path.isdir(sub):
                sub_bin = os.path.join(sub, "bin")
                if os.path.isdir(sub_bin):
                    return sub_bin
                if os.path.exists(os.path.join(sub, "node.exe")) or os.path.exists(os.path.join(sub, "node")):
                    return sub
    except Exception:
        pass
    return install_dir
