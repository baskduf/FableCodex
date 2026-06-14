#!/usr/bin/env python3
"""Install FableCodex through the Codex personal plugin marketplace."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

PLUGIN_NAME = "codex-fable5"
MARKETPLACE_NAME = "personal"
CATEGORY = "Productivity"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "name": MARKETPLACE_NAME,
            "interface": {"displayName": "Personal"},
            "plugins": [],
        }
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise SystemExit(f"{path} must contain a JSON object.")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def marketplace_entry() -> dict[str, Any]:
    return {
        "name": PLUGIN_NAME,
        "source": {
            "source": "local",
            "path": f"./plugins/{PLUGIN_NAME}",
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": CATEGORY,
    }


def update_marketplace(path: Path) -> str:
    payload = load_json(path)
    name = payload.get("name")
    if not isinstance(name, str) or not name.strip():
        payload["name"] = MARKETPLACE_NAME
        name = MARKETPLACE_NAME
    payload.setdefault("interface", {"displayName": name.capitalize()})
    plugins = payload.setdefault("plugins", [])
    if not isinstance(plugins, list):
        raise SystemExit(f"{path} field 'plugins' must be an array.")

    entry = marketplace_entry()
    for index, item in enumerate(plugins):
        if isinstance(item, dict) and item.get("name") == PLUGIN_NAME:
            plugins[index] = entry
            break
    else:
        plugins.append(entry)

    write_json(path, payload)
    return name


def find_codex() -> str | None:
    candidates = [
        shutil.which("codex"),
        "/Applications/Codex.app/Contents/Resources/codex",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    plugin_src = repo_root / "plugins" / PLUGIN_NAME
    if not (plugin_src / ".codex-plugin" / "plugin.json").exists():
        raise SystemExit(f"Cannot find plugin manifest under {plugin_src}")

    home = Path.home()
    plugin_dst = home / "plugins" / PLUGIN_NAME
    marketplace_path = home / ".agents" / "plugins" / "marketplace.json"

    if plugin_dst.exists():
        shutil.rmtree(plugin_dst)
    plugin_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(plugin_src, plugin_dst)
    print(f"Copied plugin to {plugin_dst}", flush=True)

    marketplace_name = update_marketplace(marketplace_path)
    print(f"Updated marketplace: {marketplace_path}", flush=True)
    print(f"Marketplace name: {marketplace_name}", flush=True)

    codex = find_codex()
    if codex is None:
        print("Codex CLI not found. Install manually after restarting Codex:")
        print(f"  codex plugin add {PLUGIN_NAME}@{marketplace_name}")
        return 0

    cmd = [codex, "plugin", "add", f"{PLUGIN_NAME}@{marketplace_name}"]
    print("Installing plugin through Codex CLI:", flush=True)
    print("  " + " ".join(cmd), flush=True)
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        print("Codex CLI install did not complete. You can retry manually:")
        print(f"  codex plugin add {PLUGIN_NAME}@{marketplace_name}")
        return result.returncode

    print("Installed plugin through Codex marketplace.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
