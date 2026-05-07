"""Carrega o catalogo YAML em estruturas Python tipadas."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class EndpointConfig:
    name: str
    path: str
    params: dict[str, Any] = field(default_factory=dict)
    paginated: bool = True
    pk: list[str] = field(default_factory=list)
    incremental: str = "snapshot"
    fanout_from: str | None = None


@dataclass
class APIConfig:
    base_url: str
    user_agent: str
    timeout: int
    max_retries: int
    endpoints: dict[str, EndpointConfig]
    fanout_limits: dict[str, int]


def load(path: str | Path = "conf/endpoints.yaml") -> APIConfig:
    """Le YAML e devolve APIConfig."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    eps = {
        name: EndpointConfig(name=name, **cfg)
        for name, cfg in raw.get("endpoints", {}).items()
    }
    return APIConfig(
        base_url=raw["base_url"].rstrip("/"),
        user_agent=raw.get("user_agent", "camara-pipeline/0.1"),
        timeout=int(raw.get("timeout", 30)),
        max_retries=int(raw.get("max_retries", 4)),
        endpoints=eps,
        fanout_limits=raw.get("fanout_limits", {}),
    )
