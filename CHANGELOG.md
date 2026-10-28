# Changelog

Все значимые изменения в `ru-legal` документируются здесь.

Формат основан на [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
проект следует [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added (2026-10-29)
- `packs/personal-bankruptcy/` — новый pack «Личное банкротство граждан (гл. X ФЗ-127)»
  (P1 из roadmap_packs): killer-skill `bankrotstvo-fizlica` (триаж внесудебное МФЦ vs
  судебное по гл. X ФЗ-127, перспектива должника), PROFILE.md, references/currency-watch.md
- `packs/registry.json` — pack `personal-bankruptcy` убран из roadmap в рабочий реестр
- Сверка норм 2026-10-29: ст. 223.2-223.7 (окно МФЦ 25 т.р.–1 млн, бесплатно, 6 мес),
  ст. 333.37 НК (госпошлина должника 0 ₽ с 09.09.2024), ст. 213.30 ФЗ-127
  (ред. 04.08.2026), КС 15-П от 26.04.2021, Обзор ВС РФ от 18.06.2025 пп. 17/18/30/34

### Fixed (2026-10-20) — 0.3.1
- Агрегатор падал на старте, если в окружении `ALL_PROXY=socks://...`: fastmcp
  проверял новую версию на PyPI через httpx, и `httpx.AsyncClient` бросал
  `ValueError: Unknown scheme for proxy URL`. Проверка версии отключена
  (`FASTMCP_CHECK_FOR_UPDATES=off` до импорта fastmcp), неподдерживаемые
  proxy-схемы вычищаются перед созданием клиента в router.

### Added (2026-10-20)
- Перенесены из `claude-for-legal-ru` (Apache-2.0) 4 пака: `nonprofit-law` (6), `education-law` (3), `enforcement-law` (3), `matter-management` (3)
- 24 skill добавлены в существующие паки: `ip-law` +4, `corporate-law` +7, `litigation` +9, `labor-law` +3, `regulatory-monitor` +1
- `NOTICE` — атрибуция Anthropic и `claude-for-legal-ru`
- Адаптированы пути профилей (`~/.ru-legal/profiles/<pack>/PROFILE.md`), имена паков и frontmatter (`user_invocable`)
- `packs/registry.json` — single source of truth для всех packs и MCP
- `packs/*/pack.yaml` — portable runtime-agnostic manifests для каждого pack
- `packs/process-documents/pack.yaml` — манифест пака (ранее отсутствовал при наличии записи в реестре)
- `.github/workflows/validate.yml` — CI: реестр, `pack.yaml` ↔ каталоги skills, frontmatter
- `tools/pre-commit` + `tools/install-hooks.sh` — хук валидации перед коммитом

### Changed (2026-10-20)
- Заменены дубли улучшенными версиями из `claude-for-legal-ru`:
  `ip-law/fto-triage` → `ip-law/svoboda-ispolzovaniya`,
  `ip-law/cease-desist` → `ip-law/pretenziya-o-narushenii`,
  `process-documents/claim-draft-civil` → `process-documents/isk-sostavlenie`
- Единый корень дел для всех паков: `~/.ru-legal/matters/` (ранее `litigation` использовал
  `~/.ru-legal/profiles/litigation/matters/`)
- `ru-legal-aggregator` 0.2.0: пакеты skills попадают в wheel, `ru-legal` CLI (`list-packs`,
  `list-skills`, `show-skill`), `RU_LEGAL_SKILLS_PACKS_ROOT` теперь опционален

### Renamed (2026-10-20)
- PyPI-пакет `ru-legal-mcp` → `ru-legal-skills-mcp`, модуль `ru_legal_mcp` → `ru_legal_skills_mcp`,
  CLI `ru-legal` → `ru-legal-skills`, MCP server name `ru-legal` → `ru-legal-skills`,
  env var `RU_LEGAL_PACKS_ROOT` → `RU_LEGAL_SKILLS_PACKS_ROOT` (старое имя работает как alias)
- версия агрегатора 0.3.0

### Fixed (2026-10-20)
- `references/constants/2026.yaml`: МРОТ-2026 = 27 093 ₽ (было 19 242 ₽ — значение 2024 года),
  предельная база взносов 2 979 000 ₽, госпошлины АПК/ГПК по ред. ФЗ-259/2024, шкала НДФЛ,
  пособие по безработице; `next_review` продлён
- `ru-legal-aggregator`: wheel без `packs/` (падение на старте после `pip install`), битый
  entrypoint `ru_legal_skills_mcp.cli:main`, неверный `REPO_ROOT` в тестах реестра

---

## [0.1.0] - planned (first public release)

Первый публичный релиз. Repository содержит две части: skills (Markdown content) и MCP servers (Python packages).

### Skills (`packs/`) — 186 skills в 19 packs

- **contract-law** (12 skills) — NDA / vendor agreement / SaaS MSA review, договоры услуг / поставки / аренды
- **data-protection** (8) — DSAR response, 152-ФЗ compliance
- **litigation** (26) — matter intake, brief drafting
- **labor-law** (20) — termination review, ЛНПА drafting
- **corporate-law** (20) — share-deal review, DD
- **tax-law** (9) — tax-audit response (ВНП)
- **public-procurement** (9) — tender documentation review (44-ФЗ / 223-ФЗ)
- **compliance-aml** (9) — sanctions screening, 115-ФЗ
- **ip-law** (17) — clearance, FTO, претензия, infringement triage, takedown (ФЗ-149)
- **ai-governance** (10) — use-case triage, vendor AI review
- **administrative-law** (8) — КоАП violation response
- **real-estate** (9) — ДДУ review (214-ФЗ), cadastre check
- **regulatory-monitor** (7) — reg-feed watcher
- **nonprofit-law** (6), **education-law** (3), **enforcement-law** (3), **matter-management** (3),
  **process-documents** (2) — перенесены из `claude-for-legal-ru`
- **consumer-product** (5) — launch review (ЗЗПП + 152-ФЗ + 38-ФЗ)

### MCP servers (`mcps/`) — 8 пакетов

| MCP | Источник | Что даёт |
|-----|----------|----------|
| `pravo-mcp` | pravo.gov.ru | Тексты ФЗ / Указов / Постановлений |
| `egrul-mcp` | api-fns.ru | ЕГРЮЛ (требует API key) |
| `kad-mcp` | kad.arbitr.ru | Арбитражные дела |
| `efrsb-mcp` | bankrot.fedresurs.ru | Реестр банкротств |
| `rospatent-mcp` | fips.ru | ТЗ / патенты / ПО |
| `zakupki-mcp` | zakupki.gov.ru | Гос.закупки + РНП |
| `rosreestr-mcp` | pkk.rosreestr.ru | Кадастр недвижимости |
| `ru-legal-skills-mcp` (aggregator) | — | Unified entry-point: skills как MCP prompts + Strategy C router |

### Aggregator features
- 186 skills auto-зарегистрированы как MCP prompts (slash-commands)
- Tools: `list_skills`, `find_skill`, `get_skill`, `get_skill_index`
- Strategy C router — keyword shortlist + optional LLM picker (OpenAI / YandexGPT / GigaChat / DeepSeek auto-detected из env)

### Vendored content
- `vendor/claude-for-legal/` — git submodule с upstream Anthropic claude-for-legal (Apache 2.0). Используется как reference для adapted ports — см. attribution в frontmatter каждого ported skill.
