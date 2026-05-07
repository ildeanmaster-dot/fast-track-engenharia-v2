"""Silver: leitura de bronze JSONL + rename + tipagem + dedup."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

SAMPLES_DIR = Path("data/samples")


# campo bronze -> snake_case silver, por entidade
_RENAMES: dict[str, dict[str, str]] = {
    "deputados": {
        "id": "id_deputado",
        "siglaPartido": "sigla_partido",
        "siglaUf": "sigla_uf",
        "idLegislatura": "id_legislatura",
        "urlFoto": "url_foto",
    },
    "partidos": {
        "id": "id_partido",
        "sigla": "sigla_partido",
        "nome": "nome_partido",
    },
    "legislaturas": {
        "id": "id_legislatura",
        "dataInicio": "data_inicio",
        "dataFim": "data_fim",
    },
    "frentes": {
        "id": "id_frente",
        "titulo": "nome_frente",
        "idLegislatura": "id_legislatura",
    },
    "frente_membros": {
        "id": "id_deputado",
        "_parent_id": "id_frente",
        "nome": "nome_deputado",
        "siglaPartido": "sigla_partido",
        "siglaUf": "sigla_uf",
    },
    "orgaos": {
        "id": "id_orgao",
        "sigla": "sigla_orgao",
        "nome": "nome_orgao",
        "codTipoOrgao": "cod_tipo_orgao",
        "tipoOrgao": "tipo_orgao",
        "dataInicio": "data_inicio",
        "dataFim": "data_fim",
    },
    "eventos": {
        "id": "id_evento",
        "dataHoraInicio": "data_hora_inicio",
        "dataHoraFim": "data_hora_fim",
        "descricaoTipo": "descricao_tipo",
    },
    "evento_deputados": {
        "id": "id_deputado",
        "_parent_id": "id_evento",
        "siglaPartido": "sigla_partido",
        "siglaUf": "sigla_uf",
    },
    "votacoes": {
        "id": "id_votacao",
        "dataHoraRegistro": "data_hora_registro",
    },
    "votacao_votos": {
        "_parent_id": "id_votacao",
        "tipoVoto": "tipo_voto",
        "dataRegistroVoto": "data_registro_voto",
    },
    "deputado_despesas": {
        "_parent_id": "id_deputado",
        "tipoDespesa": "tipo_despesa",
        "codDocumento": "cod_documento",
        "valorDocumento": "valor_documento",
        "valorLiquido": "valor_liquido",
        "valorGlosa": "valor_glosa",
        "dataDocumento": "data_documento",
        "nomeFornecedor": "nome_fornecedor",
        "cnpjCpfFornecedor": "cnpj_fornecedor",
    },
    "proposicoes": {
        "id": "id_proposicao",
        "siglaTipo": "sigla_tipo",
        "ementa": "ementa",
        "dataApresentacao": "data_apresentacao",
    },
    "proposicao_tramitacoes": {
        "_parent_id": "id_proposicao",
        "dataHora": "data_hora",
        "siglaOrgao": "sigla_orgao",
        "descricaoSituacao": "descricao_situacao",
        "descricaoTramitacao": "descricao_tramitacao",
    },
}

_PKS: dict[str, list[str]] = {
    "deputados": ["id_deputado"],
    "partidos": ["id_partido"],
    "legislaturas": ["id_legislatura"],
    "frentes": ["id_frente"],
    "frente_membros": ["id_frente", "id_deputado"],
    "orgaos": ["id_orgao"],
    "eventos": ["id_evento"],
    "evento_deputados": ["id_evento", "id_deputado"],
    "votacoes": ["id_votacao"],
    "votacao_votos": ["id_votacao", "id_deputado"],
    "deputado_despesas": ["id_deputado", "cod_documento"],
    "proposicoes": ["id_proposicao"],
    "proposicao_tramitacoes": ["id_proposicao", "sequencia"],
}

# coluna -> tipo (date | ts) para parse temporal
_DATE_COLS: dict[str, list[tuple[str, str]]] = {
    "legislaturas": [("data_inicio", "date"), ("data_fim", "date")],
    "orgaos": [("data_inicio", "date"), ("data_fim", "date")],
    "eventos": [("data_hora_inicio", "ts"), ("data_hora_fim", "ts")],
    "votacoes": [("data_hora_registro", "ts")],
    "votacao_votos": [("data_registro_voto", "ts")],
    "deputado_despesas": [("data_documento", "ts")],
    "proposicoes": [("data_apresentacao", "date")],
    "proposicao_tramitacoes": [("data_hora", "ts")],
}


def _read_jsonl(name: str) -> list[dict]:
    path = SAMPLES_DIR / f"{name}.jsonl"
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _flatten_voto_deputado(rec: dict) -> dict:
    """Em /votacoes/{id}/votos, o registro tem deputado_ aninhado."""
    if "deputado_" in rec and isinstance(rec["deputado_"], dict):
        d = rec.pop("deputado_")
        rec["id_deputado"] = d.get("id")
        rec["nome_deputado"] = d.get("nome")
        rec["sigla_partido"] = d.get("siglaPartido")
        rec["sigla_uf"] = d.get("siglaUf")
    return rec


def to_silver(name: str) -> pd.DataFrame:
    """Bronze -> silver para uma entidade."""
    raw = _read_jsonl(name)
    if not raw:
        return pd.DataFrame()

    if name == "votacao_votos":
        raw = [_flatten_voto_deputado(r) for r in raw]

    df = pd.json_normalize(raw, sep="_")

    # tira metadados de auditoria expandidos
    df = df.drop(columns=[c for c in df.columns if c.startswith("_audit")], errors="ignore")

    # rename
    df = df.rename(columns=_RENAMES.get(name, {}))

    # parse datas
    for col, kind in _DATE_COLS.get(name, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=(kind == "ts"))

    # dedup pela PK
    pk = _PKS.get(name)
    if pk and all(c in df.columns for c in pk):
        df = df.drop_duplicates(subset=pk, keep="last").reset_index(drop=True)

    return df


def to_silver_all() -> dict[str, pd.DataFrame]:
    """Roda silver pra todas as entidades cujo bronze existe."""
    out: dict[str, pd.DataFrame] = {}
    for name in _RENAMES.keys():
        try:
            out[name] = to_silver(name)
        except FileNotFoundError:
            pass
    return out
