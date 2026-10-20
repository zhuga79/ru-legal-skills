"""Hatch build hook: упаковать packs/ внутрь wheel.

Без этого `pip install ru-legal-mcp` даёт wheel без skills и сервер падает на
старте: _find_packs_root() не находит packs/.
"""
from __future__ import annotations

from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class PacksBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict) -> None:
        repo_packs = Path(self.root).resolve().parent.parent / "packs"
        if not repo_packs.is_dir():
            raise RuntimeError(f"packs/ not found at {repo_packs}")
        build_data.setdefault("force_include", {})[str(repo_packs)] = "ru_legal_mcp/packs"
