"""Gold: dimensoes + fatos do star schema."""
from __future__ import annotations

import pandas as pd


def dim_deputado(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return silver["deputados"][[
        "id_deputado", "nome", "sigla_partido", "sigla_uf", "id_legislatura"
    ]].copy()


def dim_partido(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return silver["partidos"][["id_partido", "sigla_partido", "nome_partido"]].copy()


def dim_frente(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return silver["frentes"][["id_frente", "nome_frente", "id_legislatura"]].copy()


def dim_orgao(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    df = silver["orgaos"]
    cols = ["id_orgao", "sigla_orgao", "nome_orgao", "tipo_orgao", "cod_tipo_orgao"]
    return df[[c for c in cols if c in df.columns]].copy()


def dim_evento(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    df = silver["eventos"]
    cols = ["id_evento", "data_hora_inicio", "data_hora_fim", "descricao_tipo", "situacao"]
    return df[[c for c in cols if c in df.columns]].copy()


def dim_data(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Dimensao calendario derivada das datas dos eventos e votacoes."""
    timestamps: list[pd.Series] = []
    if "eventos" in silver and "data_hora_inicio" in silver["eventos"].columns:
        timestamps.append(silver["eventos"]["data_hora_inicio"])
    if "votacoes" in silver and "data_hora_registro" in silver["votacoes"].columns:
        timestamps.append(silver["votacoes"]["data_hora_registro"])

    if not timestamps:
        return pd.DataFrame(columns=["data", "ano", "mes", "dia", "semana", "dia_semana"])

    all_ts = pd.concat(timestamps).dropna()
    if all_ts.empty:
        return pd.DataFrame(columns=["data", "ano", "mes", "dia", "semana", "dia_semana"])

    dias = pd.to_datetime(all_ts, utc=True).dt.normalize().drop_duplicates().sort_values()
    dim = pd.DataFrame({"data": dias.dt.date})
    dim["ano"] = dias.dt.year.values
    dim["mes"] = dias.dt.month.values
    dim["dia"] = dias.dt.day.values
    dim["semana"] = dias.dt.isocalendar().week.values
    dim["dia_semana"] = dias.dt.day_name().values
    return dim.reset_index(drop=True)


# ---------- Fatos ----------

def fato_voto(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    df = silver["votacao_votos"]
    cols = ["id_votacao", "id_deputado", "tipo_voto", "data_registro_voto"]
    return df[[c for c in cols if c in df.columns]].copy()


def fato_presenca(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    df = silver["evento_deputados"]
    cols = ["id_evento", "id_deputado", "sigla_partido", "sigla_uf"]
    return df[[c for c in cols if c in df.columns]].copy()


def fato_despesa(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    df = silver["deputado_despesas"]
    cols = [
        "id_deputado", "ano", "mes", "tipo_despesa", "valor_liquido",
        "nome_fornecedor", "cnpj_fornecedor", "data_documento", "cod_documento",
    ]
    return df[[c for c in cols if c in df.columns]].copy()
