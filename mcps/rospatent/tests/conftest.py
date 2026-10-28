"""Тесты не должны зависеть от прокси-настроек окружения.

httpx читает *_PROXY при создании клиента и падает на неподдерживаемой схеме
(например ALL_PROXY=socks://...), даже если весь HTTP замокан через respx.
Поэтому чистим прокси-переменные до импорта тестовых модулей.
"""

import os

for _var in (
    "ALL_PROXY", "all_proxy",
    "HTTP_PROXY", "http_proxy",
    "HTTPS_PROXY", "https_proxy",
    "NO_PROXY", "no_proxy",
):
    os.environ.pop(_var, None)
