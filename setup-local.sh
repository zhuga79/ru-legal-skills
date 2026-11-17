#!/usr/bin/env bash
# Локальная установка ru-legal для Claude Code.
# Повторно запускать после обновления зависимостей: патч certifi слетает.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

[ -d .venv ] || uv venv --python 3.12 .venv
VIRTUAL_ENV=.venv uv pip install -e mcps/ru-legal-aggregator -e mcps/cbr -e mcps/pravo \
  -e mcps/egrul -e mcps/kad -e mcps/efrsb -e mcps/zakupki -e mcps/rosreestr -e mcps/rospatent

# Корневые сертификаты Минцифры: без них zakupki.gov.ru и часть госресурсов
# падают с CERTIFICATE_VERIFY_FAILED. httpx игнорирует SSL_CERT_FILE и берёт
# бандл certifi, поэтому дописываем прямо в него.
mkdir -p certs
[ -s certs/russiantrustedca.pem ] || \
  env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u all_proxy \
  curl -sS -m 30 -o certs/russiantrustedca.pem https://gu-st.ru/content/Other/doc/russiantrustedca.pem

CACERT="$(.venv/bin/python -c 'import certifi;print(certifi.where())')"
if ! grep -q "Russian Trusted" <(openssl crl2pkcs7 -nocrl -certfile "$CACERT" | openssl pkcs7 -print_certs -noout); then
  cp "$CACERT" "$CACERT.orig"
  cat certs/russiantrustedca.pem >> "$CACERT"
  echo "certifi пропатчен: $CACERT"
fi

echo "Готово. MCP-серверы: .venv/bin/{ru-legal,cbr,pravo,egrul,kad,efrsb,zakupki,rosreestr,rospatent}-mcp"
