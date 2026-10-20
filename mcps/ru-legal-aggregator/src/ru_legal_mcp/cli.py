"""CLI для ru-legal-mcp.

По умолчанию запускает MCP-сервер (stdio). Дополнительные команды — для
инспекции реестра skills без запуска MCP-клиента (fastmcp не требуется).
"""
from __future__ import annotations

import argparse
import sys

from .registry.skills import SkillRegistry, find_packs_root

__version__ = "0.2.0"


def _load_registry() -> SkillRegistry:
    registry = SkillRegistry()
    registry.load_from_packs(find_packs_root())
    return registry


def _cmd_list_skills(args: argparse.Namespace) -> int:
    skills = _load_registry().list_all(pack=args.pack or None, only_user_invocable=False)
    for s in skills:
        print(f"{s.pack}/{s.name}")
    print(f"\nвсего: {len(skills)}", file=sys.stderr)
    return 0


def _cmd_show_skill(args: argparse.Namespace) -> int:
    skill = _load_registry().get(args.skill_id)
    if skill is None:
        print(f"skill не найден: {args.skill_id}", file=sys.stderr)
        return 1
    print(skill.body)
    return 0


def _cmd_list_packs(_: argparse.Namespace) -> int:
    packs: dict[str, int] = {}
    for s in _load_registry().list_all(only_user_invocable=False):
        packs[s.pack] = packs.get(s.pack, 0) + 1
    for pack, n in sorted(packs.items()):
        print(f"{pack}\t{n}")
    print(f"\nпаков: {len(packs)}, skills: {sum(packs.values())}", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ru-legal",
        description="ru-legal-mcp: MCP-сервер + инспекция реестра skills.",
    )
    parser.add_argument("--version", action="version", version=f"ru-legal-mcp {__version__}")
    sub = parser.add_subparsers(dest="command")
    p_list = sub.add_parser("list-skills", help="список skills (опционально по паку)")
    p_list.add_argument("--pack", default="")
    p_list.set_defaults(func=_cmd_list_skills)
    p_show = sub.add_parser("show-skill", help="вывести SKILL.md по id pack/skill")
    p_show.add_argument("skill_id")
    p_show.set_defaults(func=_cmd_show_skill)
    p_packs = sub.add_parser("list-packs", help="список паков и число skills")
    p_packs.set_defaults(func=_cmd_list_packs)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if not getattr(args, "command", None):
        # Без подкоманды — обычный запуск MCP-сервера (stdio).
        from . import server

        server.main()
        return
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
