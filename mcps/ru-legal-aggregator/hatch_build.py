"""Hatch build hook: упаковать packs/ внутрь wheel.

Без этого `pip install ru-legal-skills-mcp` даёт wheel без skills и сервер падает на
старте: find_packs_root() не находит packs/.

Работает в двух режимах:
- сборка из репозитория: packs/ лежит на два уровня выше пакета;
- сборка wheel из sdist: packs уже внутри архива (`ru_legal_skills_mcp/packs`).
"""
from __future__ import annotations

from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class PacksBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict) -> None:
        root = Path(self.root).resolve()
        candidates = [
            root / "packs",                      # пакет в корне репозитория
            root.parent.parent / "packs",        # mcps/<pkg> -> repo/packs
            root / "src" / "ru_legal_skills_mcp" / "packs",  # уже собранный sdist
            root / "ru_legal_skills_mcp" / "packs",     # layout sdist hatchling
        ]
        source = next((p for p in candidates if p.is_dir()), None)
        if source is None:
            raise RuntimeError(f"packs/ not found (искали: {', '.join(map(str, candidates))})")
        build_data.setdefault("force_include", {})[str(source)] = "ru_legal_skills_mcp/packs"
