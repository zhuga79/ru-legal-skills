"""Регрессия: socks:// в *_PROXY не должен ронять создание httpx-клиента."""
from __future__ import annotations

import httpx

from ru_legal_skills_mcp.router.llm import RouterLLMClient, _drop_unsupported_proxies


def test_drop_unsupported_proxy_env(monkeypatch):
    monkeypatch.setenv("ALL_PROXY", "socks://127.0.0.1:2080/")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:8080/")

    _drop_unsupported_proxies()

    import os

    assert "ALL_PROXY" not in os.environ
    assert os.environ["HTTPS_PROXY"] == "http://127.0.0.1:8080/"


def test_client_builds_with_socks_proxy(monkeypatch):
    monkeypatch.setenv("ALL_PROXY", "socks://127.0.0.1:2080/")

    client = RouterLLMClient()
    http = client._get_http()

    assert isinstance(http, httpx.AsyncClient)
