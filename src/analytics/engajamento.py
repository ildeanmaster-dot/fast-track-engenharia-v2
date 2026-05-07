"""Entregavel 6 — Score de engajamento parlamentar."""
from __future__ import annotations

import pandas as pd


def _norm_min_max(s: pd.Series) -> pd.Series:
    rng = s.max() - s.min()
    if rng == 0 or pd.isna(rng):
        return s * 0.0
    return (s - s.min()) / rng


def score_engajamento(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Score composto: presencas + votos. Cada componente normalizado min-max."""
    dep = silver["deputados"][["id_deputado", "nome", "sigla_partido", "sigla_uf"]]

    n_pres = (silver["evento_deputados"]
              .groupby("id_deputado").size().reset_index(name="n_presencas"))
    n_vot = (silver["votacao_votos"]
             .groupby("id_deputado").size().reset_index(name="n_votos"))

    df = (dep.merge(n_pres, on="id_deputado", how="left")
              .merge(n_vot, on="id_deputado", how="left"))
    df[["n_presencas", "n_votos"]] = df[["n_presencas", "n_votos"]].fillna(0)

    df["presencas_norm"] = _norm_min_max(df["n_presencas"])
    df["votos_norm"] = _norm_min_max(df["n_votos"])
    df["engajamento"] = (df["presencas_norm"] + df["votos_norm"]) / 2
    df["percentil"] = df["engajamento"].rank(pct=True)

    return df.sort_values("engajamento", ascending=False).reset_index(drop=True)


def absenteismo_em_votacoes(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Para cada deputado, % de votacoes que ele nao participou."""
    dep = silver["deputados"][["id_deputado", "nome", "sigla_partido", "sigla_uf"]]
    total_v = silver["votacoes"]["id_votacao"].nunique()
    if total_v == 0:
        return pd.DataFrame()

    votou = (silver["votacao_votos"]
             .groupby("id_deputado")["id_votacao"].nunique()
             .reset_index(name="n_votou"))

    df = dep.merge(votou, on="id_deputado", how="left")
    df["n_votou"] = df["n_votou"].fillna(0).astype(int)
    df["n_ausencias"] = total_v - df["n_votou"]
    df["taxa_ausencia"] = df["n_ausencias"] / total_v
    return df.sort_values("taxa_ausencia", ascending=False).reset_index(drop=True)


def absenteismo_temporal(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Taxa de presenca por mes — mostra padroes temporais."""
    ed = silver["evento_deputados"][["id_evento", "id_deputado"]]
    ev = silver["eventos"][["id_evento", "data_hora_inicio"]].copy()
    ev["data_hora_inicio"] = pd.to_datetime(ev["data_hora_inicio"], errors="coerce", utc=True)
    ev["ano"] = ev["data_hora_inicio"].dt.year
    ev["mes"] = ev["data_hora_inicio"].dt.month

    j = ed.merge(ev, on="id_evento", how="left")
    return (j.groupby(["ano", "mes"])
             .agg(presencas=("id_deputado", "count"),
                  deputados_distintos=("id_deputado", "nunique"),
                  eventos=("id_evento", "nunique"))
             .reset_index()
             .sort_values(["ano", "mes"]))


def build(silver: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {
        "gold_engajamento_deputado": score_engajamento(silver),
        "gold_absenteismo_votacao": absenteismo_em_votacoes(silver),
        "gold_absenteismo_temporal": absenteismo_temporal(silver),
    }
