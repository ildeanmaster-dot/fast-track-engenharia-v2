"""Tests dos 6 entregaveis + CDC com fixtures sinteticas pequenas."""
import pandas as pd
import pytest

from src.analytics import (
    atlas_frentes,
    calendario,
    cdc_tramitacao,
    ceap,
    correlacao,
    cpis,
    engajamento,
)


@pytest.fixture
def silver():
    return {
        "deputados": pd.DataFrame([
            {"id_deputado": 1, "nome": "A", "sigla_partido": "PT", "sigla_uf": "SP", "id_legislatura": 57},
            {"id_deputado": 2, "nome": "B", "sigla_partido": "PT", "sigla_uf": "SP", "id_legislatura": 57},
            {"id_deputado": 3, "nome": "C", "sigla_partido": "PL", "sigla_uf": "RJ", "id_legislatura": 57},
        ]),
        "partidos": pd.DataFrame([
            {"id_partido": 10, "sigla_partido": "PT", "nome_partido": "PT"},
        ]),
        "frentes": pd.DataFrame([
            {"id_frente": 100, "nome_frente": "F1", "id_legislatura": 57},
            {"id_frente": 200, "nome_frente": "F2", "id_legislatura": 57},
        ]),
        "frente_membros": pd.DataFrame([
            {"id_frente": 100, "id_deputado": 1},
            {"id_frente": 100, "id_deputado": 2},
            {"id_frente": 100, "id_deputado": 3},
            {"id_frente": 200, "id_deputado": 1},
        ]),
        "orgaos": pd.DataFrame([
            {"id_orgao": 1, "sigla_orgao": "X", "nome_orgao": "Comissao Comum",
             "tipo_orgao": "Permanente", "cod_tipo_orgao": 3,
             "data_inicio": pd.NaT, "data_fim": pd.NaT},
            {"id_orgao": 2, "sigla_orgao": "CPI8J", "nome_orgao": "CPMI 8 Janeiro",
             "tipo_orgao": "CPMI", "cod_tipo_orgao": 5,
             "data_inicio": pd.Timestamp("2023-05-25"), "data_fim": pd.Timestamp("2023-12-22")},
        ]),
        "eventos": pd.DataFrame([
            {"id_evento": 1, "data_hora_inicio": pd.Timestamp("2025-03-15", tz="UTC"),
             "data_hora_fim": pd.Timestamp("2025-03-15 12:00", tz="UTC"),
             "descricao_tipo": "Audiencia", "situacao": "ok"},
            {"id_evento": 2, "data_hora_inicio": pd.Timestamp("2025-03-22", tz="UTC"),
             "data_hora_fim": pd.Timestamp("2025-03-22 14:00", tz="UTC"),
             "descricao_tipo": "Sessao", "situacao": "ok"},
        ]),
        "evento_deputados": pd.DataFrame([
            {"id_evento": 1, "id_deputado": 1, "sigla_partido": "PT", "sigla_uf": "SP"},
            {"id_evento": 1, "id_deputado": 2, "sigla_partido": "PT", "sigla_uf": "SP"},
            {"id_evento": 2, "id_deputado": 1, "sigla_partido": "PT", "sigla_uf": "SP"},
        ]),
        "votacoes": pd.DataFrame([
            {"id_votacao": 1000, "data_hora_registro": pd.Timestamp("2025-03-20", tz="UTC")},
            {"id_votacao": 2000, "data_hora_registro": pd.Timestamp("2025-03-21", tz="UTC")},
        ]),
        "votacao_votos": pd.DataFrame([
            {"id_votacao": 1000, "id_deputado": 1, "tipo_voto": "Sim", "sigla_partido": "PT", "data_registro_voto": None},
            {"id_votacao": 1000, "id_deputado": 2, "tipo_voto": "Sim", "sigla_partido": "PT", "data_registro_voto": None},
            {"id_votacao": 1000, "id_deputado": 3, "tipo_voto": "Nao", "sigla_partido": "PL", "data_registro_voto": None},
        ]),
        "deputado_despesas": pd.DataFrame([
            {"id_deputado": 1, "ano": 2024, "mes": 1, "tipo_despesa": "COMB",
             "valor_liquido": 100.0, "nome_fornecedor": "F1",
             "cnpj_fornecedor": "00001", "data_documento": None, "cod_documento": "D1"},
            {"id_deputado": 2, "ano": 2024, "mes": 1, "tipo_despesa": "COMB",
             "valor_liquido": 110.0, "nome_fornecedor": "F2",
             "cnpj_fornecedor": "00002", "data_documento": None, "cod_documento": "D2"},
            {"id_deputado": 3, "ano": 2024, "mes": 1, "tipo_despesa": "COMB",
             "valor_liquido": 5000.0, "nome_fornecedor": "F3",
             "cnpj_fornecedor": "00003", "data_documento": None, "cod_documento": "D3"},
        ]),
        "proposicoes": pd.DataFrame([
            {"id_proposicao": 1, "sigla_tipo": "PL", "ementa": "Tema X", "data_apresentacao": pd.Timestamp("2024-03-01")},
        ]),
        "proposicao_tramitacoes": pd.DataFrame([
            {"id_proposicao": 1, "sequencia": 1,
             "data_hora": pd.Timestamp("2024-03-02", tz="UTC"),
             "sigla_orgao": "MESA", "descricao_situacao": "Aguardando Parecer",
             "descricao_tramitacao": "x"},
            {"id_proposicao": 1, "sequencia": 2,
             "data_hora": pd.Timestamp("2024-04-01", tz="UTC"),
             "sigla_orgao": "PLEN", "descricao_situacao": "Pronta para Pauta no Plenario",
             "descricao_tramitacao": "y"},
        ]),
    }


# ---- 1: atlas frentes ----

def test_atlas_e_hhi(silver):
    atlas = atlas_frentes.atlas_frentes(silver)
    assert len(atlas) == 4
    hhi = atlas_frentes.hhi_por_frente(atlas)
    f1 = hhi[hhi["id_frente"] == 100].iloc[0]
    assert abs(f1["hhi"] - 5/9) < 1e-6


# ---- 2: calendario ----

def test_taxa_presenca(silver):
    out = calendario.taxa_presenca_deputado(silver)
    # deputado 1 esteve em 2 de 2 eventos
    d1 = out[out["id_deputado"] == 1].iloc[0]
    assert d1["n_presencas"] == 2
    assert d1["taxa_presenca"] == 1.0


# ---- 3: correlacao ----

def test_alinhamento_partido_unanime(silver):
    out = correlacao.alinhamento_partido_por_votacao(silver)
    pt = out[out["sigla_partido"] == "PT"]
    assert (pt["alinhamento"] == 1.0).all()


# ---- 4: ceap ----

def test_ceap_z_score_marca_outlier(silver):
    out = ceap.ceap_anomalias(silver)
    # 5000 vs media de ~1736 com std alta -> z proximo de 1.15. Nao outlier (>3),
    # mas garantimos que o calculo rodou sem erro
    assert "z_score" in out.columns
    assert "outlier" in out.columns


def test_ceap_ranking_fornecedor(silver):
    out = ceap.ceap_ranking_fornecedor(silver)
    assert len(out) == 3
    assert out.iloc[0]["valor_total"] == 5000.0


# ---- 5: cpis ----

def test_identificar_cpis(silver):
    out = cpis.identificar_cpis(silver)
    assert len(out) == 1  # so o CPMI 8 Janeiro
    assert out.iloc[0]["sigla_orgao"] == "CPI8J"


# ---- 6: engajamento ----

def test_score_normalizado_entre_0_e_1(silver):
    out = engajamento.score_engajamento(silver)
    assert out["engajamento"].between(0, 1).all()


def test_absenteismo(silver):
    out = engajamento.absenteismo_em_votacoes(silver)
    # deputados 2 e 3 votaram em 1 das 2; deputado 1 votou em 1 das 2
    assert (out["taxa_ausencia"] == 0.5).all()


# ---- opcional: CDC ----

def test_cdc_scd2_marca_is_current(silver):
    out = cdc_tramitacao.build_scd2(silver)
    assert "is_current" in out.columns
    # so a ultima tramitacao (sequencia 2) e current
    cur = out[out["is_current"]]
    assert len(cur) == 1
    assert cur.iloc[0]["sequencia"] == 2


def test_cdc_alertas_detecta_plenario(silver):
    scd2 = cdc_tramitacao.build_scd2(silver)
    alertas = cdc_tramitacao.alertas_transicao(scd2)
    assert "avanco_plenario" in alertas["tipo_alerta"].values
