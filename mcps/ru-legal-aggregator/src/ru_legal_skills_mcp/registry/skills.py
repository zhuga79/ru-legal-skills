"""Skill registry — loads + indexes all 186 skills from packs/.

Provides:
- list_skills() — все skills с метаданными
- get_skill(skill_id) — full SKILL.md
- search_skills(query) — keyword search по id/name/description/телу skill
  (префиксная нормализация русских словоформ, IDF, покрытие запроса)
- get_skill_index() — компактный index (для LLM router)

Loaded once at startup, cached in memory.
"""
from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Лёгкая нормализация русских словоформ для keyword-поиска.
#
# Полноценный стеммер (Snowball/pymorphy) тянет зависимость ради одной функции,
# поэтому используем префиксный ключ: у русских словоформ основа обычно
# совпадает в первых 6 символах («сокращение/сокращении», «договор/договора»).
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-zа-я0-9]+")
_STEM_PREFIX_LEN = 6

# Веса полей при скоринге (подобраны на наборе реальных запросов юристов).
# Тело весит меньше: в нём много «воды», но именно в workflow живут ключевые
# слова, которых нет в коротком description («сокращение», «прогул»).
_W_NAME = 2.0
_W_DESC = 1.5
_W_BODY = 0.75
# IDF выше этого порога — токен редкий по корпусу; совпадение только в теле
# тогда почти так же весомо, как в description (см. _RARE_IDF в keyword_search).
_RARE_IDF = 3.0

# Служебные слова: не несут смысла в юридическом запросе
_STOPWORDS = frozenset(
    {
        "и", "или", "в", "во", "на", "по", "с", "со", "к", "ко", "о", "об",
        "для", "при", "из", "от", "до", "за", "не", "что", "как", "это",
        "нужно", "надо", "хочу", "хотим", "можно", "ли", "же", "бы",
        "перед", "через", "после", "между", "если", "чтобы", "когда",
        "его", "ее", "их", "мы", "вы", "он", "она", "они", "мне", "нам",
        "все", "весь", "этот", "эта", "эти", "свой", "свои",
    }
)


def _stem_key(word: str) -> str:
    """Префиксный ключ словоформы: lower, ё→е, первые N символов."""
    normalized = word.lower().replace("ё", "е")
    if len(normalized) <= _STEM_PREFIX_LEN:
        return normalized
    return normalized[:_STEM_PREFIX_LEN]


def _query_keys(text: str) -> list[str]:
    """Уникальные смысловые ключи запроса (без стоп-слов, с нормализацией)."""
    keys: list[str] = []
    for raw in _TOKEN_RE.findall(text.lower()):
        if raw in _STOPWORDS or len(raw) < 3:
            continue
        key = _stem_key(raw)
        if key not in keys:
            keys.append(key)
    return keys


def find_packs_root() -> Path:
    """Найти каталог packs/.

    Порядок: packs, упакованные в пакет (wheel), затем RU_LEGAL_SKILLS_PACKS_ROOT,
    затем поиск вверх по дереву каталогов (репозиторий/editable install).
    """
    import os

    bundled = Path(__file__).resolve().parents[1] / "packs"
    if bundled.is_dir() and any(bundled.glob("*/skills/*/SKILL.md")):
        return bundled

    for var in ("RU_LEGAL_SKILLS_PACKS_ROOT", "RU_LEGAL_PACKS_ROOT"):
        if env := os.getenv(var):
            path = Path(env).resolve()
            if path.exists():
                return path

    for parent in Path(__file__).resolve().parents[:8]:
        candidate = parent / "packs"
        if candidate.is_dir() and any(candidate.glob("*/skills/*/SKILL.md")):
            return candidate

    raise FileNotFoundError(
        "Cannot find packs/ directory. Set RU_LEGAL_SKILLS_PACKS_ROOT environment variable."
    )


@dataclass
class SkillMetadata:
    """Compact metadata из skill frontmatter."""

    skill_id: str  # "pack-name/skill-name"
    pack: str
    name: str
    description: str
    argument_hint: str | None = None
    user_invocable: bool = True
    ported_from: str | None = None
    adaptation_category: str | None = None
    path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "pack": self.pack,
            "name": self.name,
            "description": self.description.strip(),
            "argument_hint": self.argument_hint,
            "user_invocable": self.user_invocable,
        }


@dataclass
class Skill(SkillMetadata):
    """Full skill — metadata + body."""

    body: str = ""

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["body"] = self.body
        return base


class SkillRegistry:
    """In-memory registry всех skills.

    Loaded once at startup via load_from_packs(). Thread-safe для read.
    """

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}
        self._loaded = False
        self._search_index: dict[str, tuple[set[str], set[str], set[str]]] | None = None
        self._idf: dict[str, float] | None = None

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def __len__(self) -> int:
        return len(self._skills)

    def load_from_packs(self, packs_root: Path | str) -> int:
        """Load all SKILL.md files under packs_root.

        Returns:
            Number of skills loaded.
        """
        packs_path = Path(packs_root).resolve()
        if not packs_path.exists():
            raise FileNotFoundError(f"Packs directory not found: {packs_path}")

        self._search_index = None  # пересоберётся при следующем поиске
        self._idf = None

        count = 0
        for skill_md in packs_path.glob("*/skills/*/SKILL.md"):
            try:
                skill = self._parse_skill_file(skill_md, packs_path)
                if skill is not None:
                    self._skills[skill.skill_id] = skill
                    count += 1
            except Exception as e:
                logger.warning("Failed to load %s: %s", skill_md, e)

        self._loaded = True
        logger.info("Loaded %d skills from %s", count, packs_path)
        return count

    def _parse_skill_file(self, path: Path, packs_root: Path) -> Skill | None:
        """Parse SKILL.md — extract frontmatter + body."""
        content = path.read_text(encoding="utf-8")
        if not content.startswith("---"):
            logger.warning("No frontmatter in %s, skipping", path)
            return None

        # Split frontmatter / body
        m = re.match(r"^---\s*\n(.+?)\n---\s*\n(.*)$", content, re.DOTALL)
        if not m:
            logger.warning("Invalid frontmatter in %s", path)
            return None

        try:
            fm = yaml.safe_load(m.group(1))
        except yaml.YAMLError as e:
            logger.warning("YAML parse error in %s: %s", path, e)
            return None

        if not isinstance(fm, dict):
            return None

        body = m.group(2).strip()

        # Derive skill_id from path: packs/<pack>/skills/<skill_name>/SKILL.md
        rel = path.relative_to(packs_root)
        parts = rel.parts
        if len(parts) < 4 or parts[1] != "skills":
            return None
        pack_name = parts[0]
        skill_name = parts[2]
        skill_id = f"{pack_name}/{skill_name}"

        return Skill(
            skill_id=skill_id,
            pack=pack_name,
            name=fm.get("name", skill_name),
            description=str(fm.get("description", "")),
            argument_hint=fm.get("argument-hint") or fm.get("argument_hint"),
            user_invocable=bool(fm.get("user_invocable", True)),
            ported_from=fm.get("ported_from"),
            adaptation_category=fm.get("adaptation_category"),
            path=path,
            body=body,
        )

    def list_all(
        self,
        pack: str | None = None,
        only_user_invocable: bool = True,
    ) -> list[SkillMetadata]:
        """Return all skills (optionally filtered)."""
        result = []
        for skill in self._skills.values():
            if only_user_invocable and not skill.user_invocable:
                continue
            if pack is not None and skill.pack != pack:
                continue
            result.append(skill)
        return sorted(result, key=lambda s: s.skill_id)

    def get(self, skill_id: str) -> Skill | None:
        """Get full skill by ID."""
        return self._skills.get(skill_id)

    def _ensure_search_index(self) -> None:
        """Построить поисковый индекс (лениво, один раз на процесс).

        Индексируются три поля с разным весом: id+name, description и тело.
        Тело важно: ключевые слова часто есть только в workflow
        («сокращение», «прогул»), а не в коротком description.
        """
        if self._search_index is not None:
            return

        index: dict[str, tuple[set[str], set[str], set[str]]] = {}
        df: dict[str, int] = {}

        for skill_id, skill in self._skills.items():
            if not skill.user_invocable:
                continue
            name_keys = {
                _stem_key(tok)
                for tok in _TOKEN_RE.findall(f"{skill.skill_id} {skill.name}".lower())
            }
            desc_keys = {_stem_key(tok) for tok in _TOKEN_RE.findall(skill.description.lower())}
            body_keys = {_stem_key(tok) for tok in _TOKEN_RE.findall(skill.body.lower())}
            index[skill_id] = (name_keys, desc_keys, body_keys)
            for key in name_keys | desc_keys | body_keys:
                df[key] = df.get(key, 0) + 1

        total = max(len(index), 1)
        self._idf = {key: math.log((total + 1) / (cnt + 1)) + 1.0 for key, cnt in df.items()}
        self._search_index = index

    def keyword_search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[tuple[SkillMetadata, float]]:
        """Keyword search с учётом русской морфологии и IDF.

        Скоринг: совпадение в id/name весит 2.0, в description — 1.5,
        в теле skill — 0.75; вес токена — его IDF (частые слова вроде
        «проверка» вносят меньший вклад, чем редкие). Итог умножается на
        покрытие запроса: skill, где нашлись все слова запроса, важнее
        skill'а с одним частым совпадением («разработка» в названии).

        Это tier-1 shortlist для LLM-роутера — важнее recall@limit, чем
        точное top-1 (тонкий выбор делает LLM-tier или юрист).

        Returns:
            List of (skill, score) sorted by score descending.
        """
        keys = _query_keys(query)
        if not keys:
            return []

        self._ensure_search_index()
        assert self._search_index is not None
        assert self._idf is not None

        scored: list[tuple[SkillMetadata, float]] = []
        for skill_id, (name_keys, desc_keys, body_keys) in self._search_index.items():
            score = 0.0
            matched = 0
            for key in keys:
                weight = self._idf.get(key, 1.0)
                if key in name_keys:
                    score += _W_NAME * weight
                elif key in desc_keys:
                    score += _W_DESC * weight
                elif key in body_keys:
                    # Совпадение только в теле слабо против desc-match по тому
                    # же запросу («сокращение» в теле termination-review против
                    # «разработка» в desc ip-паков). Если токен редкий (высокий
                    # IDF), совпадение в теле — сильный сигнал, а не шум: поднимаем
                    # вес до уровня description.
                    body_w = _W_BODY if weight < _RARE_IDF else _W_DESC
                    score += body_w * weight
                else:
                    continue
                matched += 1
            if score > 0:
                coverage = matched / len(keys)
                scored.append((self._skills[skill_id], score * (0.5 + coverage)))

        scored.sort(key=lambda item: (-item[1], item[0].skill_id))
        return scored[:limit]

    def get_index_for_router(self) -> str:
        """Compact index of all skills для LLM router.

        Format:
            <skill_id> | <description (first 120 chars)>

        ~186 skills × ~150 chars = ~22KB — fits comfortably в context.
        """
        lines = ["Available skills (skill_id | description):"]
        for skill in sorted(self._skills.values(), key=lambda s: s.skill_id):
            if not skill.user_invocable:
                continue
            desc = re.sub(r"\s+", " ", skill.description).strip()
            if len(desc) > 150:
                desc = desc[:147] + "..."
            lines.append(f"  {skill.skill_id} | {desc}")
        return "\n".join(lines)
