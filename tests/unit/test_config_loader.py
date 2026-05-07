"""Tests do loader de configuracao YAML."""
from src.utils.config_loader import load


def test_load_basico():
    cfg = load("conf/endpoints.yaml")
    assert cfg.base_url.startswith("https://dadosabertos.camara.leg.br")
    assert "deputados" in cfg.endpoints
    assert "frente_membros" in cfg.endpoints


def test_endpoints_basicos_tem_pk():
    cfg = load("conf/endpoints.yaml")
    for name in ["deputados", "partidos", "frentes", "orgaos", "votacoes"]:
        ep = cfg.endpoints[name]
        assert ep.pk, f"endpoint {name} sem PK"


def test_fanouts_apontam_para_pais_validos():
    cfg = load("conf/endpoints.yaml")
    for name, ep in cfg.endpoints.items():
        if ep.fanout_from:
            assert ep.fanout_from in cfg.endpoints, \
                f"fanout {name} aponta pra {ep.fanout_from} que nao existe"


def test_estrategias_incrementais_validas():
    cfg = load("conf/endpoints.yaml")
    valid = {"snapshot", "append", "watermark", "scd2"}
    for name, ep in cfg.endpoints.items():
        assert ep.incremental in valid, \
            f"{name} tem incremental invalida: {ep.incremental}"
