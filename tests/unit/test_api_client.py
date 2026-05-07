"""Tests do cliente HTTP."""
import pytest
import responses

from src.ingestion.api_client import (
    CamaraAPIClient,
    CamaraAPIError,
    _next_page_num,
    _parse_next,
)
from src.utils.config_loader import APIConfig, EndpointConfig


@pytest.fixture
def cfg():
    eps = {
        "test": EndpointConfig(name="test", path="/test", params={"itens": 10},
                               paginated=True, pk=["id"], incremental="snapshot"),
    }
    return APIConfig(
        base_url="https://api.exemplo.com",
        user_agent="ut/0.1", timeout=10, max_retries=3,
        endpoints=eps, fanout_limits={},
    )


def test_parse_next_link_header():
    h = '<https://api/?pagina=1>; rel="self", <https://api/?pagina=2>; rel="next"'
    assert _parse_next(h) == "https://api/?pagina=2"
    assert _parse_next(None) is None
    assert _parse_next('<https://api/>; rel="last"') is None


def test_next_page_num_extracao():
    assert _next_page_num("https://api/?pagina=5", current=4) == 5


@responses.activate
def test_iter_pages_pagina_unica(cfg):
    responses.add(
        responses.GET,
        "https://api.exemplo.com/test",
        json={"dados": [{"id": 1}, {"id": 2}]},
        status=200,
    )
    client = CamaraAPIClient(cfg)
    pages = list(client.iter_pages(cfg.endpoints["test"]))
    assert len(pages) == 1
    assert len(pages[0].records) == 2


@responses.activate
def test_iter_pages_segue_link_next(cfg):
    responses.add(
        responses.GET,
        "https://api.exemplo.com/test",
        json={"dados": [{"id": 1}]},
        status=200,
        headers={"Link": '<https://api.exemplo.com/test?pagina=2>; rel="next"'},
        match_querystring=False,
    )
    responses.add(
        responses.GET,
        "https://api.exemplo.com/test",
        json={"dados": [{"id": 2}]},
        status=200,
        match_querystring=False,
    )
    client = CamaraAPIClient(cfg)
    pages = list(client.iter_pages(cfg.endpoints["test"], max_pages=3))
    assert len(pages) == 2


@responses.activate
def test_erro_cliente_4xx_levanta(cfg):
    responses.add(
        responses.GET,
        "https://api.exemplo.com/test",
        json={"erro": "x"},
        status=400,
    )
    client = CamaraAPIClient(cfg)
    with pytest.raises(CamaraAPIError):
        list(client.iter_pages(cfg.endpoints["test"]))
