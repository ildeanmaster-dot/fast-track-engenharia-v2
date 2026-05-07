"""Entregavel 2 — Calendario analitico de eventos."""
from __future__ import annotations

import pandas as pd


def taxa_presenca_deputado(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    eventos = silver["eventos"]["id_evento"]
    total = eventos.nunique()
    if total == 0:
        return pd.DataFrame()

    presencas = (silver["evento_deputados"]
                 .groupby("id_deputado")
                 .size()
                 .reset_index(name="n_presencas"))
    presencas["total_eventos"] = total
    presencas["taxa_presenca"] = presencas["n_presencas"] / total

    dep = silver["deputados"][["id_deputado", "nome", "sigla_partido", "sigla_uf"]]
    return (presencas.merge(dep, on="id_deputado", how="left")
                     .sort_values("taxa_presenca", ascending=False)
                     .reset_index(drop=True))


def taxa_presenca_por_tipo(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Quantos deputados marcaram presenca em cada tipo de evento."""
    ev = silver["eventos"][["id_evento", "descricao_tipo"]]
    ed = silver["evento_deputados"][["id_evento", "id_deputado"]]
    j = ed.merge(ev, on="id_evento", how="left")
    return (j.groupby("descricao_tipo")
             .agg(n_eventos=("id_evento", "nunique"),
                  total_presencas=("id_deputado", "count"),
                  deputados_distintos=("id_deputado", "nunique"))
             .reset_index()
             .sort_values("total_presencas", ascending=False))


def densidade_semanal(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    df = silver["eventos"].copy()
    df["data_hora_inicio"] = pd.to_datetime(df["data_hora_inicio"], errors="coerce", utc=True)
    df = df.dropna(subset=["data_hora_inicio"])
    df["ano"] = df["data_hora_inicio"].dt.isocalendar().year
    df["semana"] = df["data_hora_inicio"].dt.isocalendar().week
    return (df.groupby(["ano", "semana"])
              .size()
              .reset_index(name="qtd_eventos")
              .sort_values(["ano", "semana"])
              .reset_index(drop=True))


def semanas_sem_atividade(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Lista semanas no range coberto pelos dados em que nao houve evento."""
    densidade = densidade_semanal(silver)
    if densidade.empty:
        return pd.DataFrame(columns=["ano", "semana"])

    # gera range completo
    pares = set(zip(densidade["ano"], densidade["semana"]))
    ano_min = int(densidade["ano"].min())
    ano_max = int(densidade["ano"].max())
    sem_atividade = []
    for ano in range(ano_min, ano_max + 1):
        for sem in range(1, 54):
            if (ano, sem) not in pares:
                sem_atividade.append({"ano": ano, "semana": sem})
    return pd.DataFrame(sem_atividade)


def eventos_futuros(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    df = silver["eventos"].copy()
    df["data_hora_inicio"] = pd.to_datetime(df["data_hora_inicio"], errors="coerce", utc=True)
    futuros = df[df["data_hora_inicio"] > pd.Timestamp.utcnow()].copy()
    return futuros.sort_values("data_hora_inicio").reset_index(drop=True)


def build(silver: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {
        "gold_taxa_presenca_deputado": taxa_presenca_deputado(silver),
        "gold_taxa_presenca_por_tipo": taxa_presenca_por_tipo(silver),
        "gold_densidade_semanal": densidade_semanal(silver),
        "gold_semanas_sem_atividade": semanas_sem_atividade(silver),
        "gold_eventos_futuros": eventos_futuros(silver),
    }
