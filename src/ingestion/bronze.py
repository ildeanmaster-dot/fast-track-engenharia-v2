"""Camada Bronze: persiste payloads da API em JSONL local.

A versao Spark/Delta dessa camada vive em notebooks/01_bronze.py e re-lê
esses JSONL produzidos aqui para gravar Delta no Volume UC.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ingestion.api_client import CamaraAPIClient
from src.utils.config_loader import APIConfig, EndpointConfig

log = logging.getLogger(__name__)
SAMPLES_DIR = Path("data/samples")


def _audit(endpoint_name: str, source_url: str) -> dict[str, Any]:
    return {
        "ingest_ts": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint_name,
        "source_url": source_url,
    }


def _write_jsonl(records: list[dict], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return len(records)


def collect_simple(
    client: CamaraAPIClient,
    endpoint: EndpointConfig,
    max_pages: int | None = None,
) -> int:
    """Coleta endpoint paginado simples e grava JSONL em SAMPLES_DIR."""
    out_path = SAMPLES_DIR / f"{endpoint.name}.jsonl"
    rows: list[dict] = []
    for page in client.iter_pages(endpoint, max_pages=max_pages):
        audit = _audit(endpoint.name, page.source_url)
        for rec in page.records:
            rec["_audit"] = audit
            rows.append(rec)
    n = _write_jsonl(rows, out_path)
    log.info("bronze %s: %d registros -> %s", endpoint.name, n, out_path)
    return n


def _load_parent_ids(parent_name: str) -> list[Any]:
    path = SAMPLES_DIR / f"{parent_name}.jsonl"
    if not path.exists():
        raise RuntimeError(
            f"pai '{parent_name}' nao foi coletado ainda — "
            f"colete antes do fanout"
        )
    ids: list[Any] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            if "id" in obj:
                ids.append(obj["id"])
    return ids


def collect_fanout(
    client: CamaraAPIClient,
    endpoint: EndpointConfig,
    max_parents: int = 15,
) -> int:
    """Coleta endpoint que depende de id do pai (1:N)."""
    if not endpoint.fanout_from:
        raise ValueError(f"{endpoint.name} nao tem fanout_from")

    parent_ids = _load_parent_ids(endpoint.fanout_from)[:max_parents]

    out_path = SAMPLES_DIR / f"{endpoint.name}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    with out_path.open("w", encoding="utf-8") as f:
        for pid in parent_ids:
            try:
                for page in client.iter_pages(endpoint, path_params={"id": pid}):
                    audit = _audit(endpoint.name, page.source_url)
                    for rec in page.records:
                        rec["_parent_id"] = pid
                        rec["_audit"] = audit
                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        total += 1
            except Exception as e:
                # registra mas nao falha a coleta inteira
                log.warning("fanout %s pid=%s falhou: %s", endpoint.name, pid, e)

    log.info("bronze %s (fanout): %d registros", endpoint.name, total)
    return total


def collect_all(config: APIConfig, max_pages_simple: int = 2) -> dict[str, int]:
    """Pipeline de coleta completo, em ordem de dependencia."""
    client = CamaraAPIClient(config)
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, int] = {}

    # primeiro os simples (fontes para fanout)
    simples = [n for n, ep in config.endpoints.items() if ep.fanout_from is None]
    for name in simples:
        ep = config.endpoints[name]
        try:
            n = collect_simple(client, ep, max_pages=max_pages_simple)
            results[name] = n
        except Exception as e:
            log.error("falha em %s: %s", name, e)
            results[name] = 0

    # depois os fanouts
    fanouts = [n for n, ep in config.endpoints.items() if ep.fanout_from]
    for name in fanouts:
        ep = config.endpoints[name]
        max_parents = config.fanout_limits.get(name, 15)
        try:
            n = collect_fanout(client, ep, max_parents=max_parents)
            results[name] = n
        except Exception as e:
            log.error("falha em %s: %s", name, e)
            results[name] = 0

    return results
