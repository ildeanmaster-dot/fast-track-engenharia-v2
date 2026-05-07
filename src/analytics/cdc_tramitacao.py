"""Opcional — CDC de tramitacao com SCD2.

Cada mudanca de status de uma proposicao gera nova linha com
valid_from/valid_to/is_current. Permite reconstruir o estado de qualquer
PL em qualquer data.
"""
from __future__ import annotations

import pandas as pd


def build_scd2(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Constroi SCD2 ordenando tramitacoes por data."""
    if "proposicao_tramitacoes" not in silver or silver["proposicao_tramitacoes"].empty:
        return pd.DataFrame()

    df = silver["proposicao_tramitacoes"].copy()
    if "data_hora" not in df.columns:
        return pd.DataFrame()

    df["data_hora"] = pd.to_datetime(df["data_hora"], errors="coerce", utc=True)
    df = df.dropna(subset=["data_hora"])
    df = df.sort_values(["id_proposicao", "data_hora"]).reset_index(drop=True)

    # valid_from = data_hora; valid_to = proxima data_hora (-1s) ou NaT
    df["valid_from"] = df["data_hora"]
    df["valid_to"] = df.groupby("id_proposicao")["data_hora"].shift(-1)
    df["is_current"] = df["valid_to"].isna()

    return df


def estado_atual_proposicoes(scd2: pd.DataFrame) -> pd.DataFrame:
    """Vista com somente o estado atual de cada PL."""
    if scd2.empty:
        return pd.DataFrame()
    return scd2[scd2["is_current"]].copy().reset_index(drop=True)


def alertas_transicao(scd2: pd.DataFrame) -> pd.DataFrame:
    """Detecta transicoes relevantes (avanco para plenario, arquivamento)."""
    if scd2.empty or "descricao_situacao" not in scd2.columns:
        return pd.DataFrame()

    palavras_alerta = {
        "avanco_plenario": r"plen[aá]rio|pronta para pauta",
        "arquivamento": r"arquiv|encerr",
        "votacao": r"vota[çc][aã]o",
    }

    df = scd2.copy()
    df["tipo_alerta"] = pd.NA
    for tipo, regex in palavras_alerta.items():
        mask = df["descricao_situacao"].fillna("").str.contains(regex, case=False, regex=True)
        df.loc[mask & df["tipo_alerta"].isna(), "tipo_alerta"] = tipo

    return df[df["tipo_alerta"].notna()].copy().reset_index(drop=True)


def build(silver: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    scd2 = build_scd2(silver)
    return {
        "gold_pl_tramitacao_scd2": scd2,
        "gold_pl_estado_atual": estado_atual_proposicoes(scd2),
        "gold_pl_alertas_transicao": alertas_transicao(scd2),
    }
