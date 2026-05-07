"""Entregavel 4 — Raio-X CEAP com z-score por categoria."""
from __future__ import annotations

import pandas as pd


def _z_score(df: pd.DataFrame, value_col: str, group_cols: list[str]) -> pd.DataFrame:
    """Calcula z-score do valor dentro de cada grupo."""
    grupo = df.groupby(group_cols)[value_col]
    media = grupo.transform("mean")
    desvio = grupo.transform("std").replace(0, pd.NA)
    df = df.copy()
    df["media_grupo"] = media
    df["std_grupo"] = desvio
    df["z_score"] = (df[value_col] - media) / desvio
    df["outlier"] = df["z_score"].abs() > 3
    return df


def ceap_anomalias(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Z-score por (tipo_despesa, sigla_uf). Outlier quando |z| > 3."""
    df = silver["deputado_despesas"].copy()
    if df.empty:
        return pd.DataFrame()

    dep = silver["deputados"][["id_deputado", "sigla_partido", "sigla_uf", "nome"]]
    df = df.merge(dep, on="id_deputado", how="left")
    df = _z_score(df, "valor_liquido", ["tipo_despesa", "sigla_uf"])

    cols = [
        "id_deputado", "nome", "sigla_partido", "sigla_uf",
        "ano", "mes", "tipo_despesa", "valor_liquido",
        "nome_fornecedor", "cnpj_fornecedor",
        "media_grupo", "std_grupo", "z_score", "outlier",
    ]
    return df[[c for c in cols if c in df.columns]].copy()


def ceap_ranking_fornecedor(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    df = silver["deputado_despesas"]
    if df.empty:
        return pd.DataFrame()
    out = (df.groupby(["cnpj_fornecedor", "nome_fornecedor"], dropna=False)
             .agg(valor_total=("valor_liquido", "sum"),
                  qtd_documentos=("cod_documento", "count"),
                  qtd_deputados=("id_deputado", "nunique"))
             .reset_index()
             .sort_values("valor_total", ascending=False))
    # flag heuristica: fornecedor servindo deputados de muitas UFs
    dep_uf = silver["deputados"][["id_deputado", "sigla_uf"]]
    j = df[["cnpj_fornecedor", "id_deputado"]].merge(dep_uf, on="id_deputado", how="left")
    n_ufs = j.groupby("cnpj_fornecedor")["sigla_uf"].nunique().reset_index(name="ufs_atendidas")
    out = out.merge(n_ufs, on="cnpj_fornecedor", how="left")
    out["flag_multi_uf"] = out["ufs_atendidas"].fillna(0) >= 5
    return out.head(200).reset_index(drop=True)


def ceap_mensal_partido(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    df = silver["deputado_despesas"].copy()
    if df.empty:
        return pd.DataFrame()
    dep = silver["deputados"][["id_deputado", "sigla_partido"]]
    df = df.merge(dep, on="id_deputado", how="left")
    return (df.groupby(["ano", "mes", "sigla_partido"])
              .agg(total=("valor_liquido", "sum"),
                   qtd=("cod_documento", "count"))
              .reset_index()
              .sort_values(["ano", "mes", "total"], ascending=[True, True, False]))


def ceap_top_por_partido(silver: dict[str, pd.DataFrame], top_n: int = 10) -> pd.DataFrame:
    """Top N gastos por partido por mes (relatorio mensal)."""
    df = silver["deputado_despesas"].copy()
    if df.empty:
        return pd.DataFrame()
    dep = silver["deputados"][["id_deputado", "sigla_partido", "nome"]]
    df = df.merge(dep, on="id_deputado", how="left")
    df["rank"] = (df.groupby(["ano", "mes", "sigla_partido"])["valor_liquido"]
                    .rank(method="first", ascending=False))
    return (df[df["rank"] <= top_n]
              .sort_values(["ano", "mes", "sigla_partido", "rank"])
              .reset_index(drop=True))


def build(silver: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {
        "gold_ceap_anomalias": ceap_anomalias(silver),
        "gold_ceap_ranking_fornecedor": ceap_ranking_fornecedor(silver),
        "gold_ceap_mensal_partido": ceap_mensal_partido(silver),
        "gold_ceap_top_por_partido": ceap_top_por_partido(silver),
    }
