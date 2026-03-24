import subprocess
import platform

IS_WINDOWS = platform.system() == "Windows"


def _run_cmd(cmd: str, args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            [cmd] + args, capture_output=True, text=True, timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        out = result.stdout.strip()
        return out if out and result.returncode == 0 else None
    except Exception:
        return None


def _get_npm_registry() -> str | None:
    return _run_cmd("npm", ["config", "get", "registry"])


def _get_pip_source() -> str | None:
    return _run_cmd("pip", ["config", "get", "global.index-url"])


def get_mirror_configs() -> list[dict]:
    import os
    return [
        {
            "name": "npm",
            "display_name": "npm Registry",
            "current_source": _get_npm_registry(),
            "official_source": "https://registry.npmjs.org/",
            "mirror_source": "https://registry.npmmirror.com/",
            "config_command": "npm config set registry",
        },
        {
            "name": "pip",
            "display_name": "pip Index",
            "current_source": _get_pip_source(),
            "official_source": "https://pypi.org/simple/",
            "mirror_source": "https://pypi.tuna.tsinghua.edu.cn/simple/",
            "config_command": "pip config set global.index-url",
        },
        {
            "name": "cargo",
            "display_name": "Cargo Registry",
            "current_source": None,
            "official_source": "https://crates.io",
            "mirror_source": "https://rsproxy.cn/crates.io-index",
            "config_command": "",
        },
        {
            "name": "go",
            "display_name": "Go Proxy",
            "current_source": os.environ.get("GOPROXY"),
            "official_source": "https://proxy.golang.org,direct",
            "mirror_source": "https://goproxy.cn,direct",
            "config_command": "go env -w GOPROXY",
        },
    ]


def set_mirror_source(name: str, url: str) -> str:
    if name == "npm":
        return _run_cmd("npm", ["config", "set", "registry", url]) or "ok"
    elif name == "pip":
        return _run_cmd("pip", ["config", "set", "global.index-url", url]) or "ok"
    elif name == "go":
        return _run_cmd("go", ["env", "-w", f"GOPROXY={url}"]) or "ok"
    else:
        raise ValueError(f"Unknown mirror config: {name}")
