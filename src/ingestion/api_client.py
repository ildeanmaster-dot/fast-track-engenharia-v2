"""Cliente HTTP para a API da Camara.

Usa tenacity para retry exponencial em 429 e 5xx, e itera sobre paginas
seguindo o header Link rel="next".
"""
from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.utils.config_loader import APIConfig, EndpointConfig

log = logging.getLogger(__name__)


class CamaraAPIError(Exception):
    pass


class TransientError(CamaraAPIError):
    """Erros que merecem retry."""


@dataclass
class Page:
    records: list[dict]
    page_number: int
    source_url: str


_LINK_NEXT = re.compile(r'<([^>]+)>;\s*rel="next"')


def _parse_next(link_header: str | None) -> str | None:
    if not link_header:
        return None
    m = _LINK_NEXT.search(link_header)
    return m.group(1) if m else None


def _next_page_num(next_url: str, current: int) -> int:
    qs = parse_qs(urlparse(next_url).query)
    return int(qs.get("pagina", [str(current + 1)])[0])


class CamaraAPIClient:
    """Cliente para a API da Camara com retry e paginacao."""

    def __init__(self, config: APIConfig) -> None:
        self.cfg = config
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": config.user_agent,
        })

    @retry(
        retry=retry_if_exception_type(TransientError),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=20),
        reraise=True,
    )
    def _get(self, url: str, params: dict | None = None) -> requests.Response:
        try:
            r = self.session.get(url, params=params, timeout=self.cfg.timeout)
        except requests.RequestException as e:
            raise TransientError(str(e)) from e

        if r.status_code in (429, 500, 502, 503, 504):
            raise TransientError(f"HTTP {r.status_code} em {r.url}")
        if r.status_code >= 400:
            raise CamaraAPIError(f"HTTP {r.status_code} em {r.url}: {r.text[:200]}")
        return r

    def iter_pages(
        self,
        endpoint: EndpointConfig,
        path_params: dict | None = None,
        extra_params: dict | None = None,
        max_pages: int | None = None,
    ) -> Iterator[Page]:
        path = endpoint.path.format(**(path_params or {}))
        url = f"{self.cfg.base_url}{path}"
        params: dict[str, Any] = {**endpoint.params, **(extra_params or {})}

        page_num = 1
        while True:
            if max_pages and page_num > max_pages:
                break

            params["pagina"] = page_num
            r = self._get(url, params=params)
            body = r.json()
            records = body.get("dados", []) if isinstance(body, dict) else body
            if isinstance(records, dict):
                records = [records]

            yield Page(
                records=records or [],
                page_number=page_num,
                source_url=r.url,
            )

            if not endpoint.paginated:
                break

            next_url = _parse_next(r.headers.get("Link"))
            if not next_url:
                break

            new_page = _next_page_num(next_url, page_num)
            if new_page <= page_num:
                break
            page_num = new_page
