"""Entregavel 3 — Correlacao frente x votacao.

Compara o alinhamento medio dentro de frentes vs dentro de partidos.
"""
from __future__ import annotations

import pandas as pd


def _alinhamento(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Pra cada votacao+grupo, % do voto majoritario."""
    df = df[df["tipo_voto"].isin(["Sim", "Nao"])].copy()
    if df.empty:
        return pd.DataFrame()

    g = (df.groupby(["id_votacao", group_col, "tipo_voto"])
           .size()
           .reset_index(name="n"))
    pivot = g.pivot_table(
        index=["id_votacao", group_col],
        columns="tipo_voto", values="n", fill_value=0,
    ).reset_index()

    for c in ("Sim", "Nao"):
        if c not in pivot.columns:
            pivot[c] = 0

    pivot["total"] = pivot["Sim"] + pivot["Nao"]
    pivot = pivot[pivot["total"] >= 2].copy()
    pivot["alinhamento"] = pivot[["Sim", "Nao"]].max(axis=1) / pivot["total"]
    return pivot


def alinhamento_frente_por_votacao(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    fm = silver["frente_membros"][["id_frente", "id_deputado"]]
    votos = silver["votacao_votos"].merge(fm, on="id_deputado")
    out = _alinhamento(votos, "id_frente")
    nomes = silver["frentes"][["id_frente", "nome_frente"]]
    return out.merge(nomes, on="id_frente", how="left")


def alinhamento_partido_por_votacao(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return _alinhamento(silver["votacao_votos"], "sigla_partido")


def resumo_alinhamento(detalhe: pd.DataFrame, group_col: str) -> pd.DataFrame:
    if detalhe.empty:
        return pd.DataFrame()
    return (detalhe.groupby(group_col)
                   .agg(alinhamento_medio=("alinhamento", "mean"),
                        qtd_votacoes=("id_votacao", "nunique"))
                   .reset_index()
                   .sort_values("alinhamento_medio", ascending=False))


def build(silver: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    detalhe_f = alinhamento_frente_por_votacao(silver)
    detalhe_p = alinhamento_partido_por_votacao(silver)
    resumo_f = resumo_alinhamento(detalhe_f, "id_frente")
    resumo_p = resumo_alinhamento(detalhe_p, "sigla_partido")

    # adiciona nome da frente no resumo
    if not resumo_f.empty:
        nomes = silver["frentes"][["id_frente", "nome_frente"]]
        resumo_f = resumo_f.merge(nomes, on="id_frente", how="left")

    return {
        "gold_alinhamento_frente_por_votacao": detalhe_f,
        "gold_alinhamento_partido_por_votacao": detalhe_p,
        "gold_resumo_alinhamento_frente": resumo_f,
        "gold_resumo_alinhamento_partido": resumo_p,
    }
