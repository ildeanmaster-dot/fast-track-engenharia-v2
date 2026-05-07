"""Entregavel 5 — Auditoria de CPIs."""
from __future__ import annotations

import pandas as pd

# heuristica de identificacao
_CPI_REGEX = r"CPI|CPMI|Inqu[eé]rito"


def identificar_cpis(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    df = silver["orgaos"].copy()
    mask = df["nome_orgao"].fillna("").str.contains(
        _CPI_REGEX, case=False, regex=True, na=False
    )
    cpis = df[mask].copy()

    for c in ("data_inicio", "data_fim"):
        if c not in cpis.columns:
            cpis[c] = pd.NaT

    if cpis.empty:
        return pd.DataFrame(columns=[
            "id_orgao", "sigla_orgao", "nome_orgao", "tipo_orgao",
            "data_inicio", "data_fim", "duracao_dias", "excedeu_prazo",
        ])

    cpis["data_inicio"] = pd.to_datetime(cpis["data_inicio"], errors="coerce")
    cpis["data_fim"] = pd.to_datetime(cpis["data_fim"], errors="coerce")
    cpis["duracao_dias"] = (cpis["data_fim"] - cpis["data_inicio"]).dt.days
    cpis["excedeu_prazo"] = cpis["duracao_dias"].fillna(0) > 180  # 180 = prazo regimental

    cols = ["id_orgao", "sigla_orgao", "nome_orgao", "tipo_orgao",
            "data_inicio", "data_fim", "duracao_dias", "excedeu_prazo"]
    return cpis[[c for c in cols if c in cpis.columns]].reset_index(drop=True)


def cpi_legislacao(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Tenta cruzar CPIs com proposicoes — bem limitado pela API publica."""
    cpis = identificar_cpis(silver)
    if cpis.empty or "proposicoes" not in silver:
        return pd.DataFrame()

    # cruzamento por substring no nome — heuristica
    rows: list[dict] = []
    for _, row in cpis.iterrows():
        sigla = row.get("sigla_orgao") or ""
        nome = row.get("nome_orgao") or ""
        if not sigla and not nome:
            continue
        ementa = silver["proposicoes"].get("ementa")
        if ementa is None or ementa.empty:
            continue
        match = silver["proposicoes"][
            ementa.str.contains(sigla, case=False, na=False) if sigla else
            ementa.str.contains(nome, case=False, na=False)
        ]
        for _, prop in match.iterrows():
            rows.append({
                "id_cpi": row["id_orgao"],
                "sigla_cpi": sigla,
                "id_proposicao": prop["id_proposicao"],
                "sigla_tipo": prop.get("sigla_tipo"),
                "ementa": prop.get("ementa", "")[:200],
            })
    return pd.DataFrame(rows)


def build(silver: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    cpis = identificar_cpis(silver)
    return {
        "gold_cpi_catalogo": cpis,
        "gold_cpi_legislacao": cpi_legislacao(silver),
    }
