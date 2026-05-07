"""Tests do silver."""
import json

import pytest

from src.transforms import silver as silver_mod


@pytest.fixture
def fake_samples(tmp_path, monkeypatch):
    monkeypatch.setattr(silver_mod, "SAMPLES_DIR", tmp_path)
    return tmp_path


def _w(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def test_silver_deputados_rename(fake_samples):
    _w(fake_samples / "deputados.jsonl", [
        {"id": 1, "nome": "X", "siglaPartido": "PT", "siglaUf": "SP", "idLegislatura": 57},
    ])
    df = silver_mod.to_silver("deputados")
    assert "id_deputado" in df.columns
    assert "sigla_partido" in df.columns
    assert df.iloc[0]["id_deputado"] == 1


def test_silver_dedup_remove_duplicatas(fake_samples):
    _w(fake_samples / "deputados.jsonl", [
        {"id": 1, "nome": "X", "siglaPartido": "PT", "siglaUf": "SP", "idLegislatura": 57},
        {"id": 1, "nome": "X", "siglaPartido": "PT", "siglaUf": "SP", "idLegislatura": 57},
        {"id": 2, "nome": "Y", "siglaPartido": "PL", "siglaUf": "RJ", "idLegislatura": 57},
    ])
    df = silver_mod.to_silver("deputados")
    assert len(df) == 2


def test_silver_eventos_parse_timestamp_utc(fake_samples):
    _w(fake_samples / "eventos.jsonl", [
        {"id": 1, "dataHoraInicio": "2025-03-15T10:00",
         "dataHoraFim": "2025-03-15T12:00", "descricaoTipo": "Sessao", "situacao": "ok"},
    ])
    df = silver_mod.to_silver("eventos")
    ts_dtype = df["data_hora_inicio"].dtype
    assert "datetime" in ts_dtype.name


def test_silver_voto_aplaina_deputado_aninhado(fake_samples):
    _w(fake_samples / "votacao_votos.jsonl", [
        {"_parent_id": 100,
         "deputado_": {"id": 1, "nome": "X", "siglaPartido": "PT", "siglaUf": "SP"},
         "tipoVoto": "Sim", "dataRegistroVoto": "2025-01-01T10:00"},
    ])
    df = silver_mod.to_silver("votacao_votos")
    assert "id_deputado" in df.columns
    assert df.iloc[0]["id_deputado"] == 1
    assert df.iloc[0]["sigla_partido"] == "PT"
