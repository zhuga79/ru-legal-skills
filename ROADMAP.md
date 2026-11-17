# ROADMAP

> Live-документ. Обновляется по факту прогресса + community feedback.
> Последнее обновление: 2026-11-17 (актуализация после переноса methodology/risk-assessment)

## Vision

**ru-legal — open-source инфраструктура для работы юриста с AI в РФ.**

Цель: покрыть **85% популярных юр.вопросов** через комбинацию skills (методология) и MCP (доступ к госреестрам). Apache 2.0, self-hosted, works с любым MCP-клиентом.

**Что мы делаем хорошо** (отличие от закрытых решений):
- 🔓 Open-source — fork, modify, audit
- 🧩 MCP-стандарт — works с Claude Code / Cursor / Continue / LangGraph
- 🇷🇺 Multi-LLM — YandexGPT / GigaChat / Anthropic / OpenAI / DeepSeek / vLLM
- 🏛 Direct access к госреестрам (8 MCPs) — без посредников

---

## Текущее состояние (2026-11-17)

✅ **206 skills** в 21 pack:
- methodology (12), risk-assessment (4) — НОВОЕ 2026-11-17 (перенос из AutoClaw legal skills с переписыванием под РФ)
- contract-law (13, + contract-desensitize), litigation (28, + case-brief, evidence-evaluation)
- labor-law (20), corporate-law (20)
- ip-law (17), tax-law (9), public-procurement (9), compliance-aml (9)
- real-estate (9), data-protection (8), administrative-law (8)
- ai-governance (10), regulatory-monitor (7), nonprofit-law (6)
- consumer-product (5), education-law (3), enforcement-law (3)
- matter-management (3), process-documents (2), personal-bankruptcy (1)

✅ **Переработаны старые порты (волна мая 2026):** contract-review (generic-режим, ст. 333/431.2/432),
claim-chart (составы неустойки/МВ/труда/налогов), amendment-history (ГК 450.1/452),
matter-briefing, chronology, review, escalation-flagger, stakeholder-summary, tabular-review.

✅ **Инфраструктура качества:** `scripts/validate_skills.py` (frontmatter, дубликаты, registry),
`audit_staleness.py` на py3.10+, CI-шаг validate.

✅ **8 MCP-серверов** к госреестрам:
- pravo-mcp, egrul-mcp, kad-mcp, efrsb-mcp
- rospatent-mcp, zakupki-mcp, rosreestr-mcp
- ru-legal-skills-mcp (агрегатор)

✅ Совместимость: Claude Code, Cursor, Continue, LangGraph

✅ **Единый корень дел:** `~/.ru-legal/matters/` для всех паков (`litigation`, `matter-management`)

✅ **ru-legal-aggregator 0.2.0:** skills входят в wheel, `ru-legal` CLI (`list-packs`,
`list-skills`, `show-skill`), `RU_LEGAL_SKILLS_PACKS_ROOT` опционален

✅ **Дубли заменены** версиями из `claude-for-legal-ru`: `svoboda-ispolzovaniya` (FTO),
`pretenziya-o-narushenii`, `isk-sostavlenie` (АПК/ГПК)

**Что отсутствует** (явные дыры):
- Суды общей юрисдикции (СОЮ) — ~90% юр.практики (трудовые, семейные, наследственные споры)
- Семейное / наследственное / жилищное право
- Банкротство физлиц — частично закрыто (1 skill bankrotstvo-fizlica вместо 8–10 из Phase 1)
- Compliance suite (санкции, лицензии, реестр МСП) — частично: compliance-aml есть, sanctions MCP ⚫

> Методологический каркас (норма/факты/состав/заключение/риски) закрыт pack-ами
> `methodology` и `risk-assessment` (2026-11-17). Не путать с отраслевыми дырами выше.

---

## Phase 1 — закрыть основные дыры (ПЕРЕЗАПУСК: декабрь 2026 — февраль 2027)

> Оригинальные дедлайны Phase 1 (июнь-июль) и Phase 2 (август-сентябрь) просрочены.
> Phase 3 (октябрь-ноябрь 2026) формально «наступила» без выполнения Phase 1–2.
> Ниже — актуализированный план от 2026-11-17. Старый текст Phase 1–3 сохранён
> ниже как архив, чтобы не потерять наработки по составу skills.

**Приоритеты пересмотрены.** Методология закрыта. Главное узкое место — **MCP-здоровье**
и **СОЮ**, а не новые pack-и поверх шаткого data-слоя.

### Волна A — здоровье данных (декабрь 2026) — P0

Без этого новые skills будут цитировать непроверенные нормы.

| Задача | Что | Критерий готовности |
|---|---|---|
| `pravo-mcp` | TLS до сих пор сломан (с 2026-05-21), Basic auth в коде. Env-override, pinger TLS, переход на HTTPS когда оживёт | smoke test зелёный 2 недели подряд |
| `kad-mcp` / `efrsb-mcp` | Browser UA добавлен 2026-05-26, ре-тест так и не описан как пройденный | live-тест + запись в MCP-STATUS |
| `egrul-mcp` | Free tier 800 запросов **суммарно** — для прода непригоден. dadata fallback (P3 из статуса) | ключ + fallback в README |
| `zakupki-mcp` | Endpoint подозрителен. Либо доказать, либо пометить ⚫ | вердикт в MCP-STATUS |
| `rosreestr-mcp` | `get_encumbrances` вводит в заблуждение (всегда платная EGRN) | honest description или удалить tool |
| MCP-аудит | «Next audit: 2026-11-02» просрочен. Сделать понедельничный CI реальностью, а не обещанием | свежий audit + cron |
| constants | `references/constants/2026.yaml` есть — **проверить, что skills реально ссылаются**, а не хардкодят 18 млн | grep-аудит хардкодов |

### Волна B — СОЮ и process-documents (январь 2027) — P0

СОЮ — ~90% практики, без него семейное/наследственное/жилищное не работает.

1. **`gas-pravosudie-mcp`** — sudrf/vsrf. Нет публичного API: честно оценить
   scraping vs paid feed vs «ручной поиск юристом» (как rospatent URL-builder).
   Не обещать работающий поиск, если его нет.
2. **`process-documents` добить** — сейчас 2 skills (`isk-sostavlenie`,
   `motion-evidence-collection`). Из архива Phase 1 взять: appeal-draft,
   cassation-draft, response-draft, procedural-deadlines-calc, settlement-agreement.
   Парность: `isk-sostavlenie` ↔ `isk-proverka` уже есть в litigation.
3. **Gold dataset** — хотя бы 10 кейсов на methodology + litigation
   (см. Quality Infrastructure ниже). Без этого «206 skills» не проверяемы.

### Волна C — отраслевые pack-и (февраль–апрель 2027) — P1

Порядок — по массовости практики, не по «красивости»:

1. **`family-law`** (10–12) — состав из архива Phase 1 остаётся валидным.
2. **`inheritance-law`** (8–10) — там же.
3. **`personal-bankruptcy` расширить** — 1 killer-skill есть, добавить:
   внесудебное через МФЦ (чек-лист), кредитор-триаж, оспаривание сделок (213.32).
4. **`housing-law`** — после СОЮ MCP, иначе без картотеки СОЮ навыки «слепые».

### Волна D — compliance и ниша (май–июнь 2027) — P2

- sanctions: оставить ⚫ до появления machine-readable источника; в skills
  `compliance-aml/sanctions-screening` — ручной процесс, не фейковый MCP.
- `financial-disputes`, `social-benefits` — по запросу community (vote issues).
- `documents-mcp` — генератор шаблонов: вероятно, лучше python-docx в skills
  (как `sanitize_docx.py`), чем отдельный MCP.

### Quality Infrastructure (не откладывать в Phase 3)

- `scripts/validate_skills.py` — есть. Расширить: проверка `references` НПА,
  запрещённых англицизмов в описаниях новых skills, наличие «Что НЕ делает».
- Gold dataset: `tests/gold/<pack>/<skill>/case-*.yaml` — старт с methodology
  (12 skills × 2 кейса) и litigation (case-brief, evidence-evaluation, claim-chart).
- Legal Review Pipeline: искать 3–5 юристов-партнёров (family, inheritance,
  bankruptcy, СОЮ) — см. конец файла.
- THIRD_PARTY_NOTICES.md: в портах упоминается, файла в корне нет — создать
  или убрать ссылки.

### Чего НЕ делать в 2027 H1

- Phase 4 `ru-buh` — отложить до traction (звёзды/пилюли), не по календарю.
- Новые pack-и «на вырост» (medical, customs, agro) — только по issues.
- Писать skills, зависящие от несуществующих MCP (sanctions, СОЮ поиск).

---

## Архив оригинального плана (не актуализирован, состав skills полезен)

## Phase 1 — закрыть основные дыры (июнь-июль 2026)

**Цель:** покрытие популярных юр.вопросов 40% → 70%.

### MCPs (3 новых сервера)

#### 🔴 `gas-pravosudie-mcp` — суды общей юрисдикции
- `sudrf.ru` — federal портал СОЮ
- `vsrf.ru` — Верховный Суд РФ (определения, обзоры)
- `mos-gorsud.ru` — Мосгорсуд (отдельная картотека)

**Без этого MCP не покрываем больше половины юр.практики.** Top priority.

#### 🟡 `compliance-mcp` — объединённый сервер
- `check_sanctions_lists()` — Росфинмониторинг + ОФАК + ЕС
- `check_msp_status()` — Реестр МСП ФНС
- `check_blocked_accounts()` — счета юрлица в ФНС
- `check_disqualified_persons()` — реестр дисквалифицированных
- `check_license(ogrn)` — лицензии регулирующих органов

#### 🟢 `documents-mcp` — генератор шаблонов
- `draft_claim_template(case_type, jurisdiction)`
- `draft_appeal_template(case_type)`
- `format_motion(motion_type)`

### Skills (4 новых пака, ~40 skills)

#### `family-law` (10-12 skills)
- divorce-petition-prep, alimony-calculation, alimony-recovery
- property-division, child-custody, prenuptial-agreement-draft
- paternity-determination, adoption-petition
- parental-rights-deprivation, post-marital-disputes

#### `inheritance-law` (8-10 skills)
- estate-opening, acceptance-rejection
- mandatory-share-calc, will-validity-challenge
- heirs-dispute, estate-administrator-appointment
- intestate-succession, foreign-elements-inheritance

#### `process-documents` (12-15 skills) — cross-cutting
- isk-sostavlenie (АПК/ГПК), claim-draft-arbitration
- response-draft, appeal-draft, cassation-draft
- supervisory-complaint
- motion-judge-recusal, motion-evidence-collection, motion-expertise
- settlement-agreement, statement-of-claim-amendment
- procedural-deadlines-calc

#### `personal-bankruptcy` (8-10 skills)
- bankruptcy-filing-prep, creditor-protection
- extrajudicial-bankruptcy (через МФЦ)
- restructuring-plan, debt-discharge
- bankruptcy-eligibility, asset-protection

**Метрика Phase 1:** ~25 new MCP tools + 40 new skills.

---

## Phase 2 — Business & Financial domains (август-сентябрь 2026)

**Цель:** покрытие 70% → 85%.

### MCPs (3 новых сервера)

#### `banking-finance-mcp`
- ЦБ РФ API (справочник банков, отозванные лицензии)
- АСВ (страхование вкладов, банкротство банков)
- Реестр платежных систем ЦБ
- Реестр МФО

#### `real-estate-extended-mcp`
- Лесной реестр (земли лесфонда)
- Реестр объектов культурного наследия
- Публичная кадастровая карта
- Реестр СРО строителей/проектировщиков

#### `public-disclosure-mcp`
- `e-disclosure.ru` — раскрытие публичных АО
- Реестр аффилированных лиц ЦБ
- Раскрытие банков-эмитентов

### Skills (3 новых пака, ~30 skills)

#### `housing-law` (10 skills)
- communal-services-disputes, management-company-claims
- neighbor-disputes, redevelopment-permits
- equity-construction-protection, privatization-disputes
- eviction-defense, housing-conditions-claims

#### `financial-disputes` (8-10 skills)
- osago-insurance-disputes, kasco-disputes
- bank-account-blocking-appeal, microloan-disputes
- failed-bank-deposit-recovery
- credit-card-disputes, failed-payment-recovery

#### `social-benefits` (10 skills)
- pension-assignment, pension-recalculation
- maternity-capital-disputes, disability-status-appeal
- social-benefit-denial-appeal, benefit-priority-categories

---

## Phase 3 — Specialized + Community (октябрь-ноябрь 2026)

**Цель:** добить niche домены + переход на community-driven contributions.

### MCPs (2-3 niche)
- `sanctions-international-mcp` — OFAC + EU + UK lists
- `pravo-ru-news-mcp` — daily обзор изменений законодательства
- `b2b-center-mcp` — коммерческие тендеры

### Skills (2-3 новых пака, ~20 skills)
- `administrative-extended` (10) — ГИБДД, миграция, КоАП
- `medical-disputes` (5-7) — мед.споры, ОМС, пациентские права
- niche packs по запросам community

### Quality Infrastructure (критично!)

- **Legal Review Pipeline** — каждый skill review'ится практикующим юристом до merge
- **Gold Dataset** — 30-50 размеченных кейсов per pack, regression tests
- **Audit & Disclaimer** infrastructure — verified/unverified маркеры в каждом output

---

## Phase 4 — Sister project: ru-buh (декабрь 2026 - февраль 2027)

> Когда ru-legal достиг traction (500+ ⭐, активный community, 3-5 paid pilots) — стартуем отдельный проект для **бухгалтеров**.

**Логика:** аудитория бухгалтеров в РФ ~500k (vs 150k юристов). Workflow-heavy, MCP-friendly, нет open-source альтернатив.

**Архитектура:**
- Отдельный repo `ru-buh` (skills + MCPs для бухгалтерии)
- **Shared infrastructure** с ru-legal (тот же ru-legal-agent harness)
- Shared MCPs где есть overlap (ФНС, ЕГРЮЛ)
- Cross-promotion между проектами

См. [ru-buh repo](https://github.com/AlsKozlov/ru-buh) — sister-проект upstream (AlsKozlov), не переносится в zhuga79/ru-legal-skills без отдельного решения.

---

## Долгосрочное (2027+)

### Возможные направления:
- **ru-legal-agent v1.0** — production-grade harness (LangGraph + checkpointing + HITL)
- **Telegram бот для SMB-юристов** — easy entry для тех кто не использует Claude Code
- **Web UI** — для юр.фирм с teams
- **Custom enterprise mirrors** — self-hosted database с госреестрами для compliance-heavy клиентов
- **Mobile companion** — quick checks от телефона
- **API for legaltech vendors** — embed ru-legal в их продукты

### Возможные новые домены:
- `ru-fintech` — банкинг, инвестиции, регулирование
- `ru-medical` — мед.право детально (помимо medical-disputes)
- `ru-customs` — таможенное право
- `ru-agro` — аграрное право

---

## Как контрибьютить

### Низкий порог входа

1. **Issue с предложением skill** — описываете workflow, мы обсуждаем
2. **PR с новым skill** — используйте `packs/_template/SKILL.md`
3. **PR с новым MCP** — используйте `mcps/_template/`
4. **Review существующих skills** (если вы юрист) — комментируйте в issues

### Recognition

- Имя в `CONTRIBUTORS.md`
- Mention в GitHub Releases
- (когда будет коммерческий tier) — first paid clients = опытные contributors

### Партнёры-юристы (мы ищем 3-5 человек)

Если вы практикующий юрист в области из roadmap (family, inheritance, housing, bankruptcy, financial disputes) — нужны:
- Review новых skills вашего домена (1-2 часа в неделю)
- Тестирование на реальных кейсах (анонимизированных)

В обмен:
- Recognition как domain owner в README
- Early access к ru-legal-agent (когда выйдет)
- Соавторство в публикациях / case studies
- (опционально) первые paid лицензии когда монетизируем

Связь: @alskozlov (Telegram) или Issues с тегом `domain-owner-application`.

---

## Метрики прогресса (будем обновлять)

| Метрика | Факт (2026-11-17) | Волна A–B (Q1’27) | Волна C (Q2’27) | Волна D (H1’27) |
|---|---|---|---|---|
| Packs | 22 | 22–23 (process-documents добить) | 25–26 (family, inheritance, housing) | 27+ по запросу |
| Skills | 206 | 215–225 | 245–260 | 270+ |
| MCPs рабочих | 8 (2 зелёных) | 8–9 (pravo/kad/efrsb стабилизированы) | 9–10 (СОЮ если решим) | по запросу |
| Gold-кейсы | 0 | 30+ (methodology + litigation) | 60+ | 100+ |
| Domain owners | 0 | 2 | 4 | 6 |
| GitHub ⭐ | см. repo | — | — | ru-buh только при traction |

---

## Подписка на updates

- [⭐ Star repo](https://github.com/zhuga79/ru-legal-skills)
- [Watch releases](https://github.com/zhuga79/ru-legal-skills/releases) — только когда новый release
- [Telegram канал](https://t.me/alskozlov) — upstream-канал (не наш); для этого форка — Issues/Discussions
- [Discussions](https://github.com/zhuga79/ru-legal-skills/discussions) — Q&A, feature requests

---

Roadmap корректируется на основе community feedback. Голосуйте через 👍 на issues с тегом `roadmap-vote`.
