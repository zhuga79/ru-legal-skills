# Передача репозитория на аккаунт zhuga79

Чек-лист. Выполнять по порядку; шаги 1–3 — до передачи, 4–8 — сразу после.

> **Статус 2026-10-20:** передача завершена. Репозиторий — `zhuga79/ru-legal-skills`.
> Локальный remote `fork` переключён, ссылки и clone-инструкции обновлены, CI зелёный.
> Осталось только п. 6 (PyPI): передать maintainer-права на пакет `ru-legal-mcp`.

## 1. Предполётная проверка

```bash
git status                      # рабочее дерево чистое
git log --oneline -5            # ожидаемые коммиты
git push fork master            # форк синхронизирован
gh auth status                  # токен с правами admin на репозиторий
```

- CI `.github/workflows/validate.yml` зелёный на `master`.
- `python3 scripts/audit_staleness.py` → 0 stale / 0 missing.
- `PYTHONPATH=mcps/ru-legal-aggregator/src python3 -m pytest mcps/ru-legal-aggregator/tests -q` → зелёный.

## 2. Согласовать с получателем

- Получатель `zhuga79` подтвердил передачу (нужен его ответ в issue/чате).
- Договориться о судьбе: issues, PR, wiki, GitHub Actions minutes, Packages.
- Зафиксировать, что `NOTICE` и лицензия Apache-2.0 не меняются.

## 3. Передача

```bash
gh api -X POST repos/Blqd/ru-legal-skills/transfer -f new_owner=zhuga79
```

- GitHub пришлёт приглашение: `zhuga79` должен принять его в течение 1 дня.
- Старый URL `Blqd/ru-legal-skills` начнёт редиректить на новый (редирект живёт, пока имя не займут).

## 4. После передачи: локальные remote

```bash
git remote set-url fork https://github.com/zhuga79/ru-legal-skills.git
git remote -v
```

`origin` (upstream `AlsKozlov/ru-legal`) не трогать — история происхождения сохраняется.

## 5. После передачи: настройки репозитория

- Actions: включены, workflow permissions = read-only по умолчанию.
- Branch protection на `master`: required check `validate` (jobs: registry, skills), запрет force-push.
- Secrets не переносятся автоматически — перевыпустить, если использовались.
- Описание/топики/сайт: поправить ссылки на `zhuga79/ru-legal-skills`.
- Releases и теги переносятся вместе с репозиторием — проверить `gh release list`.

## 6. PyPI

Пакет `ru-legal-mcp` **ещё не опубликован** (404 на pypi.org), поэтому «передачи прав»
не требуется — нужна первая публикация.

Публикация настроена через trusted publishing (OIDC, без токенов):
`.github/workflows/publish.yml` собирает wheel + sdist, проверяет, что `packs/` внутри,
и публикует по GitHub Release (или вручную через `workflow_dispatch`).

Что сделать вручную (нужен аккаунт PyPI `zhuga79`):

1. pypi.org → Account settings → Publishing → **Add a pending publisher**
   - PyPI Project Name: `ru-legal-mcp`
   - Owner: `zhuga79`
   - Repository name: `ru-legal-skills`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`
2. Создать GitHub Release `v0.2.0` — workflow опубликует пакет.
3. Проверить: `pip index versions ru-legal-mcp` и `uvx ru-legal-mcp`.

Пока пакет не опубликован, установка — из исходников:
`pip install -e mcps/ru-legal-aggregator`.

## 7. Коммуникация

- В старом репозитории — issue/README-заметка о новом адресе.
- В `README.md` проверить бейджи и ссылки (уже указывают на `zhuga79/ru-legal-skills`).
- Предупредить пользователей: старые URL работают через редирект, но `git remote` лучше обновить.

## 8. Пост-проверка

```bash
gh repo view zhuga79/ru-legal-skills
gh run list --repo zhuga79/ru-legal-skills --limit 3
git ls-remote fork master
```

CI должен запуститься на новом месте без правок workflow.
