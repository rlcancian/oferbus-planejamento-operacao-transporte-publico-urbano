from __future__ import annotations

import argparse
import html
import json
import re
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._ignored_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._ignored_depth > 0:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_depth == 0:
            self.parts.append(data)


def visible_text(document: str) -> str:
    parser = _VisibleTextParser()
    parser.feed(document)
    parser.close()
    text = html.unescape(" ".join(parser.parts))
    return re.sub(r"\s+", " ", text).strip()


def fetch_html(url: str, timeout: float) -> str:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            request = urllib.request.Request(url, headers={"Accept": "text/html"})
            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status != 200:
                    raise RuntimeError(f"unexpected HTTP status {response.status}")
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset)
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            time.sleep(0.5)
    raise RuntimeError(f"web workspace did not become available at {url}: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the rendered OferBus planning workspace")
    parser.add_argument("--web-url", default="http://127.0.0.1:3010")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()
    url = args.web_url.rstrip("/") + "/"
    document = fetch_html(url, args.timeout)
    text = visible_text(document)

    expected = [
        "Phase B Core Planning Fixture",
        "DEV-001 · Linha de Desenvolvimento OferBus",
        "Plano computado",
        "Normalizado",
        "Gráfico de Marcha",
        "seleção sincronizada · C.6",
        "Terminal Origem",
        "Terminal Destino",
        "Horários planejados",
        "Blocos de veículo",
        "fingerprint verificado",
    ]
    forbidden = [
        "O resultado ainda não pode ser carregado.",
        "Ainda não há um plano calculado.",
        "Gráfico de Marcha indisponível",
        "somente leitura · C.1",
    ]
    missing = [item for item in expected if item not in text]
    present_forbidden = [item for item in forbidden if item in text]
    if missing or present_forbidden:
        raise AssertionError({"missing": missing, "unexpected_empty_or_error_states": present_forbidden, "document_excerpt": text[:2200]})
    print(json.dumps({"status": "pass", "web_url": url, "assertions": expected}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
