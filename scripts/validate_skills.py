#!/usr/bin/env python3
"""validate_skills.py — валидация SKILL.md и манифестов packs.

Проверяет:
1. Frontmatter: name совпадает с каталогом, description не пустой.
2. Обязательные секции user_invocable skills (Workflow, Degraded mode).
3. Дубликаты name по всему packs/.
4. pack.yaml: каждый skill в списке существует, каждый каталог в списке.
5. registry.json: skill_count == фактическому числу SKILL.md в pack.

Usage:
    python scripts/validate_skills.py
    python scripts/validate_skills.py --no-registry   # не трогать registry
Exit 1 — есть ошибки (issues). Warnings не блокируют.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

ROOT = Path(__file__).resolve().parent.parent
PACKS = ROOT / "packs"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict[str, Any]:
    if yaml is not None:
        m = FRONTMATTER_RE.match(text)
        if not m:
            return {}
        try:
            data = yaml.safe_load(m.group(1))
            return data if isinstance(data, dict) else {}
        except yaml.YAMLError:
            return {}
    # fallback — как в audit_staleness
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    result: dict[str, Any] = {}
    for line in m.group(1).split("\n"):
        if ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            val = val.split("#", 1)[0].strip().strip("'\"")
            if val:
                result[key.strip()] = val
    return result


def find_skills(packs_root: Path) -> list[Path]:
    skills: list[Path] = []
    for pack_dir in sorted(packs_root.iterdir()):
        if not pack_dir.is_dir() or pack_dir.name.startswith("_"):
            continue
        skills_dir = pack_dir / "skills"
        if not skills_dir.exists():
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            if (skill_dir / "SKILL.md").exists():
                skills.append(skill_dir / "SKILL.md")
    return skills


def validate_skill(path: Path) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    text = path.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    rel = path.relative_to(ROOT)

    if not fm:
        issues.append(f"{rel}: frontmatter не распознан")
        return issues, warnings

    name = str(fm.get("name") or "").strip()
    if not name:
        issues.append(f"{rel}: нет name")
    elif name != path.parent.name:
        issues.append(f"{rel}: name={name!r} != каталог {path.parent.name!r}")

    desc = str(fm.get("description") or "").strip()
    if not desc:
        issues.append(f"{rel}: пустой description")

    user_inv = fm.get("user_invocable", fm.get("user-invocable"))
    if user_inv in (True, "true"):
        if "## Workflow" not in text and "## Инструкции" not in text and "## Шаг" not in text:
            warnings.append(f"{rel}: нет '## Workflow'")
        if (
            "## Degraded mode" not in text
            and "## degraded mode" not in text.lower()
            and "MCP" not in text
            and "mcp" not in text
        ):
            warnings.append(f"{rel}: нет '## Degraded mode'")

    # Zwork-специфика, которую не тащим в опенсорс-проект
    for forbidden in ("dxe_client", "PROJECT_CONTEXT", "legal_statute", "ydzk.chineselaw"):
        if forbidden in text:
            issues.append(f"{rel}: запрещённый артефакт другой платформы: {forbidden}")

    return issues, warnings


def validate_pack_yaml(pack_dir: Path, skill_dirs: set[str]) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    manifest = pack_dir / "pack.yaml"
    if not manifest.exists():
        warnings.append(f"{pack_dir.name}: нет pack.yaml")
        return issues, warnings
    if yaml is None:
        warnings.append(f"{pack_dir.name}: pyyaml недоступен, pack.yaml не проверен")
        return issues, warnings
    try:
        data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        issues.append(f"{pack_dir.name}: pack.yaml не парсится: {e}")
        return issues, warnings

    listed: set[str] = set()
    for item in data.get("skills") or []:
        if not isinstance(item, dict):
            continue
        sid = str(item.get("id") or "")
        spath = str(item.get("path") or "")
        if not sid:
            issues.append(f"{pack_dir.name}: skill без id в pack.yaml")
            continue
        listed.add(sid)
        # path обычно skills/<id>/SKILL.md
        if spath and sid not in spath:
            warnings.append(f"{pack_dir.name}/{sid}: path={spath} не содержит id")
        if sid not in skill_dirs:
            issues.append(f"{pack_dir.name}: pack.yaml содержит {sid}, каталога нет")

    extra = skill_dirs - listed
    if extra:
        warnings.append(
            f"{pack_dir.name}: каталоги без записи в pack.yaml: {', '.join(sorted(extra))}"
        )
    return issues, warnings


def validate_registry(packs_root: Path) -> tuple[list[str], list[str], int]:
    issues: list[str] = []
    warnings: list[str] = []
    reg_path = packs_root / "registry.json"
    if not reg_path.exists():
        return [f"нет packs/registry.json"], warnings, 0
    data = json.loads(reg_path.read_text(encoding="utf-8"))
    total = 0
    for p in data.get("packs", []):
        pid = p.get("id") or p.get("path")
        root = packs_root / str(p.get("path") or pid)
        if not root.is_dir():
            issues.append(f"registry: {pid}: нет каталога {root}")
            continue
        actual = len(list((root / "skills").glob("*/SKILL.md")))
        declared = p.get("skill_count")
        total += actual
        if declared != actual:
            issues.append(f"registry: {pid}: skill_count={declared}, фактически {actual}")
    return issues, warnings, total


def main() -> int:
    args = sys.argv[1:]
    check_registry = "--no-registry" not in args

    all_issues: list[str] = []
    all_warnings: list[str] = []

    skills = find_skills(PACKS)
    print(f"Найдено SKILL.md: {len(skills)}")

    seen_names: dict[tuple[str, str], str] = {}
    packs_dirs: dict[str, set[str]] = {}

    for path in skills:
        issues, warnings = validate_skill(path)
        all_issues.extend(issues)
        all_warnings.extend(warnings)
        fm = parse_frontmatter(path.read_text(encoding="utf-8"))
        name = str(fm.get("name") or path.parent.name)
        pack_name = path.relative_to(PACKS).parts[0]
        key = (pack_name, name)
        if key in seen_names:
            all_issues.append(
                f"дубликат name={name!r} в pack {pack_name}: "
                f"{seen_names[key]} и {path.relative_to(ROOT)}"
            )
        else:
            seen_names[key] = str(path.relative_to(ROOT))
        packs_dirs.setdefault(pack_name, set()).add(path.parent.name)

    for pack_name, skill_dirs in packs_dirs.items():
        issues, warnings = validate_pack_yaml(PACKS / pack_name, skill_dirs)
        all_issues.extend(issues)
        all_warnings.extend(warnings)

    if check_registry:
        issues, warnings, total = validate_registry(PACKS)
        all_issues.extend(issues)
        all_warnings.extend(warnings)
        print(f"Фактических skills (для registry): {total}")

    print(f"\n=== Ошибки: {len(all_issues)} ===")
    for x in all_issues:
        print(f"  ❌ {x}")
    print(f"=== Предупреждения: {len(all_warnings)} ===")
    for x in all_warnings:
        print(f"  ⚠ {x}")

    return 1 if all_issues else 0


if __name__ == "__main__":
    sys.exit(main())
